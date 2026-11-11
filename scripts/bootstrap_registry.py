#!/usr/bin/env python3
"""Bootstrap unverified sources from official exchange company catalogs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from exchange_adapters import EXCHANGES, ExchangeCompany, fetch_catalog


def normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def parse_exchanges(value: str) -> list[str]:
    names = [item.strip().upper() for item in value.split(",") if item.strip()]
    invalid = sorted(set(names) - set(EXCHANGES))
    if invalid:
        raise argparse.ArgumentTypeError(f"unsupported exchange: {', '.join(invalid)}")
    return names


def to_source(company: ExchangeCompany) -> dict[str, object]:
    adapter = EXCHANGES[company.exchange]
    return {
        "company_code": company.code, "company_name": company.name,
        "exchange": company.exchange, "industry": company.industry,
        "verified": False, "aliases": [company.code],
        "exchange_disclosure_url": adapter.disclosure_url(company.code),
        "allowed_domains": list(adapter.allowed_domains),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--industry", required=True, help="Industry as published by an exchange")
    parser.add_argument("--limit", type=int, default=10, help="Maximum companies to add (default: 10)")
    parser.add_argument("--exchanges", type=parse_exchanges, default=list(EXCHANGES), help="Comma-separated HOSE,HNX,UPCOM")
    parser.add_argument("--registry", type=Path, default=Path("config/report_sources.json"))
    parser.add_argument("--catalog-url", action="append", default=[], metavar="EXCHANGE=URL", help="Override an official catalog endpoint")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without writing")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")

    overrides: dict[str, str] = {}
    for item in args.catalog_url:
        exchange, separator, url = item.partition("=")
        if not separator or exchange.upper() not in EXCHANGES or not url.startswith(("https://", "http://")):
            parser.error("--catalog-url must be EXCHANGE=https://...")
        overrides[exchange.upper()] = url
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    registered = {str(source.get("company_code", "")).upper() for source in registry.get("sources", [])}
    candidates: list[ExchangeCompany] = []
    for exchange in args.exchanges:
        candidates.extend(fetch_catalog(EXCHANGES[exchange], overrides.get(exchange)))
    candidates = [source for source in candidates if normalize(source.industry) == normalize(args.industry) and source.code not in registered]
    candidates = sorted(candidates, key=lambda source: (source.exchange, source.code))[: args.limit]
    if args.dry_run:
        print(json.dumps({"sources": [to_source(source) for source in candidates]}, ensure_ascii=False, indent=2))
        return 0
    registry.setdefault("sources", []).extend(to_source(source) for source in candidates)
    args.registry.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Added {len(candidates)} unverified {args.industry} sources to {args.registry}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"bootstrap failed: {error}", file=sys.stderr)
        raise SystemExit(2) from error
