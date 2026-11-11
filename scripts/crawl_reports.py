#!/usr/bin/env python3
"""Discover public financial-report PDFs from approved exchange sources.

Official exchange disclosures are primary. A reviewed company IR page is used
only as a fallback when the exchange result contains no report PDFs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import shutil
import ssl
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


USER_AGENT = "financial-report-agent-research/0.1 (+local academic project)"
REPORT_MARKERS = (
    "bao cao tai chinh",
    "bao cao thuong nien",
    "financial statement",
    "financial report",
    "annual report",
    "bctc",
    "bctn",
)


@dataclass(frozen=True)
class Source:
    company_code: str
    company_name: str
    exchange: str
    exchange_disclosure_url: str | None
    ir_url: str | None
    ir_urls: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    industry: str | None
    aliases: tuple[str, ...]
    verified: bool
    ajax: bool


class LinkParser(HTMLParser):
    """Collect links with surrounding anchor text for report filtering."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = [dict(attrs).get("download") or ""]

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            self.links.append((self._href, " ".join(self._text)))
            self._href = None
            self._text = []


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFD", value.casefold()).replace("đ", "d")
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", value)).strip()


def normalize_selector(value: str) -> str:
    """Match Vietnamese company names whether the query has accents or not."""
    decomposed = unicodedata.normalize("NFD", value)
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return normalize_text(without_accents.replace("đ", "d"))


def canonical_url(url: str) -> str:
    parts = urlparse(url)
    return urlunparse((parts.scheme, parts.netloc, parts.path, "", parts.query, ""))


def path_slug(value: str) -> str:
    value = normalize_selector(value)
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "unknown"


def is_allowed(url: str, domains: tuple[str, ...]) -> bool:
    host = (urlparse(url).hostname or "").casefold()
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def is_report_link(url: str, anchor_text: str) -> bool:
    url_text = normalize_text(url)
    candidate = f"{url_text} {normalize_text(anchor_text)}"
    return ".pdf" in url_text and any(marker in candidate for marker in REPORT_MARKERS)


def infer_report_type(label: str, url: str) -> str:
    candidate = normalize_text(f"{label} {url}")
    if "thuong nien" in candidate or "annual report" in candidate or "bctn" in candidate:
        return "annual_report"
    if "tai chinh" in candidate or "financial statement" in candidate or "bctc" in candidate:
        return "financial_statement"
    return "unclassified"


def request(url: str, timeout: int, method: str = "GET", ajax: bool = False) -> Any:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.1"}
    if ajax:
        headers["X-Requested-With"] = "XMLHttpRequest"
    url = quote(url, safe=":/%?=&+#%")
    return urlopen(Request(url, headers=headers, method=method), timeout=timeout)


def is_certificate_error(error: URLError) -> bool:
    return isinstance(error.reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(error)


def curl_bytes(url: str, timeout: int) -> bytes:
    """Use the OS TLS stack only when Python rejects a certificate."""
    curl = shutil.which("curl") or shutil.which("curl.exe")
    if not curl:
        raise RuntimeError("Python TLS verification failed and curl is unavailable")
    completed = subprocess.run(
        [curl, "--fail", "--location", "--silent", "--show-error", "--max-time", str(timeout), "-A", USER_AGENT, url],
        check=True,
        capture_output=True,
    )
    return completed.stdout


def read_bytes(url: str, timeout: int, ajax: bool = False) -> tuple[bytes, str | None]:
    try:
        with request(url, timeout, ajax=ajax) as response:
            return response.read(), response.headers.get_content_type()
    except URLError as error:
        if not is_certificate_error(error):
            raise
        logging.warning("Python TLS rejected %s; retrying with the OS TLS stack", url)
        return curl_bytes(url, timeout), None


def robots_allowed(url: str, timeout: int, cache: dict[str, RobotFileParser | None]) -> bool:
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    if root not in cache:
        parser = RobotFileParser()
        try:
            robots_bytes, _ = read_bytes(f"{root}/robots.txt", timeout)
            robots_text = robots_bytes.decode("utf-8", errors="replace")
            parser.parse(robots_text.splitlines())
        except (HTTPError, URLError, OSError, RuntimeError, subprocess.CalledProcessError):
            logging.warning("Could not read robots.txt for %s; skipping this source", root)
            cache[root] = None
            return False
        cache[root] = parser
    parser = cache[root]
    return parser is not None and parser.can_fetch(USER_AGENT, url)


def fetch_html(url: str, timeout: int) -> str:
    body, content_type = read_bytes(url, timeout)
    if content_type and content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError(f"Expected HTML but received {content_type}")
    if body.startswith(b"%PDF-"):
        raise ValueError("Expected HTML but received a PDF")
    return body.decode("utf-8", errors="replace")


def json_pdf_links(payload: Any) -> list[tuple[str, str]]:
    """Extract attachment URLs and their titles from an exchange JSON response."""
    found: list[tuple[str, str]] = []
    if isinstance(payload, dict):
        label = str(payload.get("title") or payload.get("name") or payload.get("subject") or "")
        for value in payload.values():
            if isinstance(value, str) and ".pdf" in value.casefold():
                found.append((value, label))
            else:
                found.extend(json_pdf_links(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(json_pdf_links(item))
    return found


def discover_pdfs_at(url: str, domains: tuple[str, ...], timeout: int, delay: float, obey_robots: bool, ajax: bool = False) -> list[tuple[str, str]]:
    robots_cache: dict[str, RobotFileParser | None] = {}
    if obey_robots and not robots_allowed(url, timeout, robots_cache):
        logging.warning("robots.txt disallows source page: %s", url)
        return []

    body, content_type = read_bytes(url, timeout, ajax=ajax)
    raw_links: list[tuple[str, str]]
    if content_type and "json" in content_type:
        raw_links = json_pdf_links(json.loads(body.decode("utf-8-sig")))
    else:
        if body.startswith(b"%PDF-"):
            raise ValueError("Expected a disclosure page but received a PDF")
        parser = LinkParser()
        parser.feed(body.decode("utf-8", errors="replace"))
        raw_links = parser.links
    found: dict[str, str] = {}
    for href, text in raw_links:
        resolved = canonical_url(urljoin(url, href))
        # Some sites expose both a download endpoint and a direct media URL.
        # The direct URL avoids duplicate copies of the same PDF.
        if urlparse(resolved).path.rstrip("/").endswith("/api/download"):
            continue
        if not is_allowed(resolved, domains):
            continue
        if not is_report_link(resolved, text):
            continue
        if obey_robots and not robots_allowed(resolved, timeout, robots_cache):
            logging.info("robots.txt disallows PDF: %s", resolved)
            continue
        found.setdefault(resolved, text.strip())

    time.sleep(delay)
    return sorted(found.items())


def discover_pdfs(source: Source, timeout: int, delay: float, obey_robots: bool) -> list[tuple[str, str, str]]:
    if source.exchange_disclosure_url:
        links = discover_pdfs_at(source.exchange_disclosure_url, source.allowed_domains, timeout, delay, obey_robots)
        if links or not (source.ir_url or source.ir_urls):
            return [(url, label, source.exchange_disclosure_url) for url, label in links]
        logging.info("No exchange PDFs for %s; trying reviewed IR fallback", source.company_code)
    pages = source.ir_urls or ((source.ir_url,) if source.ir_url else ())
    found = []
    for page in pages:
        for url, label in discover_pdfs_at(page, source.allowed_domains, timeout, delay, obey_robots, source.ajax):
            found.append((url, label, page))
    return found


def infer_year(label: str, url: str, discovery_page: str = "") -> int | None:
    # Upload directories often contain the publication year, not the report year.
    match = re.search(r"(?<!\d)(20\d{2})(?!\d)", f"{label} {Path(urlparse(url).path).name} {urlparse(discovery_page).query}")
    return int(match.group(1)) if match else None


def safe_filename(source: Source, year: int | None, url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.casefold() or ".pdf"
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(urlparse(url).path).stem)[:90]
    period = str(year) if year else "unknown_year"
    return f"{source.company_code}_{period}_{token}{suffix}"


def file_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest(), path.stat().st_size


def append_manifest_record(manifest_path: Path, record: dict[str, Any]) -> None:
    with manifest_path.open("a", encoding="utf-8") as manifest:
        manifest.write(json.dumps(record, ensure_ascii=False) + "\n")


def download_pdf(url: str, target: Path, timeout: int, dry_run: bool) -> tuple[str | None, int | None]:
    if dry_run:
        return None, None
    temporary = target.with_suffix(f"{target.suffix}.part")
    digest = hashlib.sha256()
    byte_count = 0
    try:
        with request(url, timeout) as response, temporary.open("wb") as output:
            content_type = response.headers.get_content_type()
            first_chunk = response.read(8192)
            if content_type != "application/pdf" and not first_chunk.startswith(b"%PDF-"):
                raise ValueError(f"URL did not return a PDF (content type: {content_type})")
            output.write(first_chunk)
            digest.update(first_chunk)
            byte_count += len(first_chunk)
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
                byte_count += len(chunk)
        temporary.replace(target)
        return digest.hexdigest(), byte_count
    except URLError as error:
        temporary.unlink(missing_ok=True)
        if not is_certificate_error(error):
            raise
        logging.warning("Python TLS rejected %s; downloading with the OS TLS stack", url)
        curl = shutil.which("curl") or shutil.which("curl.exe")
        if not curl:
            raise RuntimeError("Python TLS verification failed and curl is unavailable") from error
        try:
            subprocess.run(
                [curl, "--fail", "--location", "--silent", "--show-error", "--max-time", str(timeout), "-A", USER_AGENT, "-o", str(temporary), url],
                check=True,
            )
            first_chunk = temporary.read_bytes()[:8192]
            if not first_chunk.startswith(b"%PDF-"):
                raise ValueError("URL did not return a PDF")
            digest = hashlib.sha256(temporary.read_bytes())
            byte_count = temporary.stat().st_size
            temporary.replace(target)
            return digest.hexdigest(), byte_count
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def load_sources(path: Path) -> list[Source]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    sources = raw.get("sources", [])
    if not isinstance(sources, list) or not sources:
        raise ValueError("config must contain a non-empty 'sources' list")

    result: list[Source] = []
    for item in sources:
        required = ("company_code", "company_name", "exchange", "allowed_domains")
        missing = [name for name in required if not item.get(name)]
        if missing:
            raise ValueError(f"source is missing required fields: {', '.join(missing)}")
        if not item.get("exchange_disclosure_url") and not item.get("ir_url") and not item.get("ir_urls"):
            raise ValueError("source requires exchange_disclosure_url or ir_url")
        result.append(
            Source(
                company_code=str(item["company_code"]).upper(),
                company_name=str(item["company_name"]),
                exchange=str(item["exchange"]).upper(),
                exchange_disclosure_url=str(item["exchange_disclosure_url"]) if item.get("exchange_disclosure_url") else None,
                ir_url=str(item["ir_url"]) if item.get("ir_url") else None,
                ir_urls=tuple(str(url) for url in item.get("ir_urls", [])),
                allowed_domains=tuple(str(domain).casefold() for domain in item["allowed_domains"]),
                industry=str(item["industry"]) if item.get("industry") else None,
                aliases=tuple(str(alias) for alias in item.get("aliases", [])),
                verified=bool(item.get("verified", False)),
                ajax=bool(item.get("ajax", False)),
            )
        )
    return result


def select_sources(registry: list[Source], companies: list[str], industries: list[str]) -> list[Source]:
    selected: dict[str, Source] = {}
    for query in companies:
        wanted = normalize_selector(query)
        for source in registry:
            names = (source.company_code, source.company_name, *source.aliases)
            if any(wanted == normalize_selector(name) for name in names):
                selected[source.company_code] = source

    for query in industries:
        wanted = normalize_selector(query)
        for source in registry:
            if source.industry and wanted == normalize_selector(source.industry):
                selected[source.company_code] = source

    if not selected:
        requested = ", ".join([*companies, *industries]) or "(no selector)"
        raise ValueError(f"No registry source matches: {requested}. Run --list-sources to see available choices.")
    return list(selected.values())


def print_sources(sources: list[Source]) -> None:
    print("company_code\tindustry\texchange\tverified\tcompany_name")
    for source in sorted(sources, key=lambda item: item.company_code):
        print(f"{source.company_code}\t{source.industry or '-'}\t{source.exchange}\t{source.verified}\t{source.company_name}")


def run(args: argparse.Namespace) -> int:
    registry = load_sources(args.registry)
    if args.list_sources:
        print_sources(registry)
        return 0
    sources = load_sources(args.config) if args.config else select_sources(registry, args.company, args.industry)
    unverified = [source.company_code for source in sources if not source.verified]
    if unverified:
        raise ValueError(f"Unverified sources cannot be crawled: {', '.join(unverified)}. Set verified to true after manual review.")
    args.output.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()
    seen_urls: set[str] = set()
    records: list[dict[str, Any]] = []

    for source in sources:
        company_dir = args.output / path_slug(source.industry or "unclassified") / path_slug(source.company_code)
        company_dir.mkdir(parents=True, exist_ok=True)
        pdf_dir = company_dir / "pdf"
        if not args.dry_run:
            pdf_dir.mkdir(exist_ok=True)
        manifest_path = company_dir / "manifest.jsonl"
        logging.info("Discovering reports for %s from the approved primary source", source.company_code)
        try:
            links = discover_pdfs(source, args.timeout, args.delay, True)
        except (HTTPError, URLError, OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
            logging.error("Could not discover reports for %s: %s", source.company_code, error)
            continue

        for url, label, discovery_page in links:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            year = infer_year(label, url, discovery_page)
            filename = safe_filename(source, year, url)
            target = pdf_dir / filename
            record: dict[str, Any] = {
                "document_id": hashlib.sha256(url.encode("utf-8")).hexdigest()[:16],
                "company_code": source.company_code,
                "company_name": source.company_name,
                "exchange": source.exchange,
                "report_type": infer_report_type(label, url),
                "fiscal_year": year,
                "source_url": url,
                "discovery_page": discovery_page,
                "link_text": label,
                "downloaded_at": now,
                "file_name": f"pdf/{filename}",
                "sha256": None,
                "bytes": None,
                "status": "discovered",
            }
            try:
                if target.exists() and not args.overwrite:
                    record["status"] = "skipped_existing"
                    record["sha256"], record["bytes"] = file_digest(target)
                else:
                    record["sha256"], record["bytes"] = download_pdf(url, target, args.timeout, args.dry_run)
                    record["status"] = "dry_run" if args.dry_run else "downloaded"
                logging.info("%s: %s", record["status"], url)
            except (HTTPError, URLError, OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
                record["status"] = "failed"
                record["error"] = str(error)
                logging.error("Download failed for %s: %s", url, error)
            records.append(record)
            append_manifest_record(manifest_path, record)
            time.sleep(args.delay)

    logging.info("Wrote %d manifest records", len(records))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--config", type=Path, help="Path to an explicit source JSON configuration")
    source_group.add_argument("--company", action="append", default=[], help="Company code or registered company name; repeatable")
    source_group.add_argument("--industry", action="append", default=[], help="Registered industry name; repeatable")
    parser.add_argument("--registry", type=Path, default=Path("config/report_sources.json"), help="Company/industry source registry")
    parser.add_argument("--list-sources", action="store_true", help="List companies and industries available in the registry")
    parser.add_argument("--output", type=Path, default=Path("data/annual-reports"), help="Output directory")
    parser.add_argument("--delay", type=float, default=1.0, help="Minimum delay between requests in seconds")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Discover links without downloading PDFs")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing PDF files")
    args = parser.parse_args()
    if not args.list_sources and not (args.config or args.company or args.industry):
        parser.error("one of --config, --company, --industry, or --list-sources is required")
    return args


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        raise SystemExit(run(parse_args()))
    except (ValueError, json.JSONDecodeError) as error:
        logging.error("Invalid configuration: %s", error)
        raise SystemExit(2) from error
