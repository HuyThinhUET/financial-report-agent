"""Thu thập PDF BCTC, giữ manifest tương thích với pipeline insight."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
from urllib.error import HTTPError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

import pymupdf
from .sources import BASELINE, VNR500, Source

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'data/data_raw/tech-manufacturing-statements'
INDEX = DEST / 'manifest.json'
USER_AGENT = 'Mozilla/5.0 (compatible; financial-report-agent-research/1.0)'
MAX_BYTES = 80 * 1024 * 1024

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.parts = []

    def handle_data(self, value):
        if self.href:
            self.parts.append(value)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href:
            self.links.append((self.href, ' '.join(self.parts)))
            self.href = None

class HttpClient:
    def __init__(self):
        self.robots = {}

    def allowed(self, url):
        parts = urlsplit(url)
        base = f'{parts.scheme}://{parts.netloc}'
        if base not in self.robots:
            robot = RobotFileParser()
            try:
                with urlopen(Request(base + '/robots.txt', headers={'User-Agent': USER_AGENT}), timeout=20) as response:
                    robot.parse(response.read().decode('utf8', errors='replace').splitlines())
                self.robots[base] = robot
            except HTTPError as exc:
                if 400 <= exc.code < 500 and exc.code != 429:
                    robot.parse([])
                    self.robots[base] = robot
                else:
                    self.robots[base] = None
            except OSError:
                self.robots[base] = None
        robot = self.robots[base]
        return robot is not None and robot.can_fetch(USER_AGENT, url)

    def get(self, url):
        if not self.allowed(url):
            raise ValueError('robots.txt unavailable or disallows URL')
        with urlopen(Request(url, headers={'User-Agent': USER_AGENT}), timeout=45) as response:
            content = response.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ValueError('Response exceeds 80 MiB')
        return content

def fold(value):
    value = unicodedata.normalize('NFD', unquote(value).casefold().replace('đ', 'd'))
    return ''.join(char for char in value if unicodedata.category(char) != 'Mn')

def candidates(source, client):
    if source.kind == 'pdf':
        yield source.url, Path(urlsplit(source.url).path).name
        return
    parser = Links()
    parser.feed(client.get(source.url).decode('utf8', errors='replace'))
    for href, label in parser.links:
        url = urljoin(source.url, href)
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.hostname not in source.hosts:
            continue
        if source.kind == 'fpt':
            if href.startswith('/api/media/') and 'bctc' in href.casefold() and parts.path.casefold().endswith('.pdf'):
                yield url, label or Path(parts.path).name
            continue
        path = parts.path[:-5] if parts.path.lower().endswith('.pdf/view') else parts.path
        text = fold(path.rsplit('/', 1)[-1] + ' ' + label)
        if ('.pdf' in parts.path.casefold()
            and re.search(r'(?<![a-z0-9])bctc(?![a-z0-9])|bao[ _-]+cao[ _-]+tai[ _-]+chinh|financial[ _-]+statements', text)
            and not re.search(r'thuong[ _-]+nien|annual[ _-]+report|to[ _-]+trinh|ban[ _-]+kiem[ _-]+soat', text)):
            yield url, label.strip()

def write_manifest(path, data):
    temp = path.with_suffix('.json.part')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    temp.replace(path)

def run(sources, *, target=None, augment=False, client=None, root=ROOT, dest=DEST, index=INDEX):
    """Tải hoặc tiếp tục; trả về (số thêm, danh sách lỗi)."""
    client = client or HttpClient()
    dest.mkdir(parents=True, exist_ok=True)
    data = json.loads(index.read_text(encoding='utf8')) if index.exists() else {'reports': []}
    rows = data['reports']
    hashes = set()
    urls = set()
    # Không âm thầm xóa record hay thay file khi corpus đã có lỗi.
    for row in rows:
        path = root / row['pdf']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError(f"Missing or modified PDF: {row['pdf']}; manifest unchanged")
        hashes.add(row['sha256'])
        urls.add(row['source_url'])
    failures, added = [], 0
    for source in sources:
        if target is not None and len(rows) >= target:
            break
        try:
            for url, label in candidates(source, client):
                if target is not None and len(rows) >= target:
                    break
                if url in urls:
                    continue
                urls.add(url)
                try:
                    time.sleep(1)
                    content = client.get(url)
                    if b'%PDF-' not in content[:1024]:
                        raise ValueError('Not a PDF')
                    digest = hashlib.sha256(content).hexdigest()
                    if digest in hashes:
                        continue
                    with pymupdf.open(stream=content, filetype='pdf') as doc:
                        if doc.needs_pass or not len(doc):
                            raise ValueError('Encrypted or empty PDF')
                        page_count = len(doc)
                    filename = f'{source.company}_{digest[:16]}.pdf'
                    path = dest / filename
                    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                        raise ValueError(f'File collision: {filename}')
                    if not path.exists():
                        temporary = path.with_suffix('.pdf.part')
                        temporary.write_bytes(content)
                        temporary.replace(path)
                    row = {'id': f'{source.company}_{digest[:16]}', 'company': source.company,
                           'sector': source.sector, 'pdf': path.relative_to(root).as_posix(),
                           'source_url': url, 'discovery_page': source.discovery_page or source.url,
                           'source_label': label, 'sha256': digest, 'page_count': page_count,
                           'classification': 'candidate_financial_statement', 'review_status': 'unreviewed'}
                    if augment:
                        row['collection'] = 'vnr500_2026_top10_private_information'
                    rows.append(row)
                    hashes.add(digest)
                    added += 1
                    data['count'] = len(rows)
                    if target is not None:
                        data['target'] = target
                        data['shortfall'] = max(0, target - len(rows))
                    write_manifest(index, data)
                    print(f'Added {filename} ({len(rows)} total)', flush=True)
                except (OSError, ValueError, pymupdf.FileDataError) as exc:
                    failures.append({'source_url': url, 'error': str(exc)})
                    print(f'Failed {url}: {exc}', flush=True)
        except (OSError, ValueError) as exc:
            failures.append({'source_url': source.url, 'error': str(exc)})
            print(f'Failed {source.url}: {exc}', flush=True)
    data['count'] = len(rows)
    if target is not None:
        data['target'] = target
        data['shortfall'] = max(0, target - len(rows))
    data['augmentation_failures' if augment else 'failures'] = failures
    write_manifest(index, data)
    return added, failures

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf8', errors='replace')
    parser = argparse.ArgumentParser(description='Tải PDF báo cáo tài chính công khai')
    parser.add_argument('--target', type=int, default=100, help='Số PDF mục tiêu ở chế độ mặc định')
    parser.add_argument('--augment', action='store_true', help='Bổ sung PDF FPT/CMC vào manifest')
    parser.add_argument('--consolidated', action='store_true', help='Tải danh sách BCTC hợp nhất đã chọn, tối đa 10 đường dẫn mỗi doanh nghiệp')
    args = parser.parse_args()
    if args.target < 1:
        parser.error('--target must be positive')
    if args.augment and args.consolidated:
        parser.error('--augment and --consolidated cannot be combined')
    if args.augment and not INDEX.exists():
        parser.error('Chạy chế độ mặc định trước để tạo manifest')
    try:
        if args.consolidated:
            entries = json.loads((ROOT / 'data_downloader/consolidated_sources.json').read_text(encoding='utf8'))
            counts = {}
            sources = []
            for item in entries:
                company = item['company']
                counts[company] = counts.get(company, 0) + 1
                if counts[company] > 10:
                    raise ValueError(f'More than 10 sources for {company}')
                url = item['url']
                host = urlsplit(url).hostname
                if urlsplit(url).scheme != 'https' or not host:
                    raise ValueError(f'Invalid source URL: {url}')
                sources.append(Source(company, 'technology', url, (host,), 'pdf', item['discovery_page']))
        else:
            sources = VNR500 if args.augment else BASELINE
        added, failures = run(sources, target=None if (args.augment or args.consolidated) else args.target, augment=args.augment)
        data = json.loads(INDEX.read_text(encoding='utf8'))
        print(f"Added {added}; total {data['count']}; failures {len(failures)}; manifest {INDEX}")
        return int(bool(failures) if (args.augment or args.consolidated) else data['count'] < args.target)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(1, f'Download failed: {exc}\n')
