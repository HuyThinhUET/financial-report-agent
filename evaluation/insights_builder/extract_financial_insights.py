"""Extract one consolidated statement per isolated Codex session, or process a batch."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'data_raw'
OUTPUT = ROOT / 'data' / 'data_evaluate'
PROMPT = Path(__file__).resolve().parent / 'financial_statement_prompt.txt'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def damaged_text(data):
    """Detect likely replacement characters, without rejecting ordinary questions."""
    if isinstance(data, str):
        return data.count('\ufffd') >= 3 or len(re.findall(r'(?i)[a-z?]\?[a-z?]', data)) >= 5
    if isinstance(data, dict):
        return any(damaged_text(value) for value in data.values())
    if isinstance(data, list):
        return any(damaged_text(value) for value in data)
    return False


def infer(row, pdf):
    """Only accept explicit period labels, never infer a year from a publication date."""
    label = unquote(row.get('source_label', ''))
    label = re.sub(r'^\d{8}\s*[-_ ]+', '', label)
    year = re.findall(r'(?<!\d)(20\d{2})(?!\d)', label)
    if len(set(year)) != 1:
        return None
    quarter = None
    if pdf.parent.name == 'hop_nhat_quy':
        m = re.search(r'(?i)\b(?:quy|quý|q)\s*([1-4]|iii|iv|ii|i)\b', label)
        if not m:
            return None
        quarter = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4}.get(m[1].lower(), int(m[1]) if m[1].isdigit() else None)
    return {'pdf': str(pdf.relative_to(ROOT)), 'company': row.get('company') or pdf.stem.split('_')[0], 'year': int(year[0]), 'quarter': quarter}


def discover():
    rows = []
    for manifest in sorted(DATA.rglob('manifest.json')):
        try:
            data = json.loads(manifest.read_text(encoding='utf-8'))
            for row in data.get('reports', []):
                pdf = (ROOT / row.get('pdf', '')).resolve()
                if pdf.is_file() and pdf.is_relative_to(DATA.resolve()) and pdf.parent.name in ('hop_nhat_nam', 'hop_nhat_quy'):
                    entry = infer(row, pdf)
                    if entry:
                        rows.append(entry)
                    else:
                        print(f'Bỏ qua kỳ chưa rõ: {pdf.relative_to(ROOT)}', file=sys.stderr)
        except (OSError, ValueError, AttributeError) as exc:
            print(f'Không đọc được {manifest}: {exc}', file=sys.stderr)
    unique = {r['pdf']: r for r in rows}
    return [unique[k] for k in sorted(unique)]


def key(row):
    return f"{row['company'].upper()}_{row['year']}" + (f"_{row['quarter']}" if row.get('quarter') else '')


def existing(row):
    return sorted(OUTPUT.glob(f'[0-9][0-9][0-9]_{key(row)}'))


def run(row, codex, model):
    pdf = (ROOT / row['pdf']).resolve()
    if not pdf.is_file() or not pdf.is_relative_to(DATA.resolve()) or pdf.parent.name not in ('hop_nhat_nam', 'hop_nhat_quy'):
        raise ValueError(f'PDF phải nằm trong data/data_raw/.../hop_nhat_nam hoặc hop_nhat_quy: {pdf}')
    if bool(row.get('quarter')) != (pdf.parent.name == 'hop_nhat_quy'):
        raise ValueError('Loại kỳ không khớp thư mục PDF')
    if not re.fullmatch(r'[A-Za-z0-9]+', row['company']) or not 1900 <= row['year'] <= 2100 or row.get('quarter') not in (None, 1, 2, 3, 4):
        raise ValueError('Mã công ty, năm hoặc quý không hợp lệ')
    found = existing(row)
    if found:
        print(f'Bỏ qua: {key(row)} đã có thư mục {found[0].name}; kiểm tra thủ công nếu cần chạy lại.')
        return 'skipped'
    OUTPUT.mkdir(parents=True, exist_ok=True)
    used = [int(m.group(1)) for p in OUTPUT.iterdir() if (m := re.match(r'^(\d{3})_', p.name))]
    number = max(used, default=0) + 1
    if number > 999:
        raise ValueError('Đã hết STT 3 chữ số')
    out = OUTPUT / f'{number:03d}_{key(row)}'
    out.mkdir()
    expected = sha(pdf)
    config = {**row, 'pdf_sha256': expected, 'model': model, 'status': 'draft_not_expert_reviewed'}
    (out / 'run_config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    prompt = PROMPT.read_text(encoding='utf-8') + '\nCấu hình dự kiến (cần đối chiếu trong PDF): ' + json.dumps(config, ensure_ascii=False) + '\nPDF: ' + str(pdf) + '\nOutput: ' + str(out / 'insights.json') + '\n'
    cmd = [codex, 'exec', '--ephemeral', '--json', '--skip-git-repo-check', '--sandbox', 'workspace-write', '--color', 'never']
    if model:
        cmd += ['--model', model]
    cmd += ['-']
    start = time.monotonic()
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    error, usage, thread, rc = None, None, None, None
    try:
        with (out/'events.jsonl').open('w', encoding='utf-8') as events, (out/'stderr.log').open('w', encoding='utf-8') as err:
            proc = subprocess.run(cmd, input=prompt, stdout=events, stderr=err, text=True, encoding='utf-8', cwd=ROOT, env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'})
            rc = proc.returncode
        for line in (out/'events.jsonl').read_text(encoding='utf-8').splitlines():
            try: event = json.loads(line)
            except ValueError: continue
            if event.get('type') == 'thread.started': thread = event.get('thread_id')
            if event.get('type') == 'turn.completed': usage = event.get('usage')
        if rc != 0: raise ValueError(f'codex exit {rc}')
        result = json.loads((out/'insights.json').read_text(encoding='utf-8'))
        if not isinstance(result, dict) or not isinstance(result.get('insights'), list) or not result['insights']:
            raise ValueError('Thiếu danh sách insight hoặc danh sách rỗng; cần kiểm tra thủ công')
        if damaged_text(result): raise ValueError('Phát hiện văn bản có khả năng lỗi mã hóa; kiểm tra insights.json và events.jsonl')
        if sha(pdf) != expected: raise ValueError('PDF đã thay đổi trong khi chạy')
    except (OSError, ValueError) as exc:
        error = str(exc)
    metrics = {'pdf_sha256': expected, 'started_at_utc': started_at, 'elapsed_seconds': round(time.monotonic()-start, 2), 'thread_id': thread, 'token_usage': usage, 'exit_code': rc, 'status': 'failed' if error else 'completed', 'error': error}
    (out/'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"{out.name}: {metrics['status']} {error or ''}", flush=True)
    return metrics['status']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pdf', help='Một PDF trong data/data_raw/.../hop_nhat_nam hoặc hop_nhat_quy')
    p.add_argument('--company', help='Mã công ty cho --pdf')
    p.add_argument('--year', type=int, help='Năm tài chính cho --pdf')
    p.add_argument('--quarter', type=int, choices=range(1, 5), help='Quý tài chính cho --pdf')
    p.add_argument('--manifest', type=Path, help='Danh sách JSON đã chuẩn bị, gồm reports')
    p.add_argument('--max_sample', '--max-sample', '--limit', type=int, help='Số báo cáo chưa có thư mục, mặc định tất cả')
    p.add_argument('--model')
    p.add_argument('--codex', help='Đường dẫn tới codex.exe hoặc codex.cmd nếu không có trên PATH')
    p.add_argument('--list', action='store_true', help='Liệt kê lựa chọn, không gọi Codex')
    a = p.parse_args()
    if a.max_sample is not None and a.max_sample < 1: p.error('--max_sample phải dương')
    if a.pdf and (not a.company or not a.year or a.manifest): p.error('--pdf cần --company, --year và không dùng cùng --manifest')
    if not a.pdf and (a.company or a.year or a.quarter): p.error('--company, --year, --quarter chỉ dùng cùng --pdf')
    try:
        rows = ([{'pdf': a.pdf, 'company': a.company, 'year': a.year, 'quarter': a.quarter}] if a.pdf else json.loads(a.manifest.read_text(encoding='utf-8'))['reports'] if a.manifest else discover())
        if a.list:
            for r in rows:
                print(f"{key(r)} {'[đã có thư mục]' if existing(r) else '[chưa chạy]'} {r['pdf']}")
            return 0
        codex = shutil.which(a.codex or 'codex')
        if not codex: p.error('Không tìm thấy Codex CLI. Cài Codex CLI và thêm vào PATH, hoặc dùng --codex với đường dẫn codex.exe/codex.cmd')
        attempted = failures = 0
        for row in rows:
            if existing(row):
                print(f'Bỏ qua {key(row)}: đã có thư mục')
                continue
            if a.max_sample is not None and attempted >= a.max_sample: break
            attempted += 1
            try:
                if run(row, codex, a.model) == 'failed': failures += 1
            except (OSError, ValueError, KeyError) as exc:
                failures += 1
                print(f'Lỗi {row}: {exc}', file=sys.stderr)
        print(f'Đã thử {attempted} báo cáo, lỗi {failures}.')
        return int(failures > 0)
    except (OSError, ValueError, KeyError) as exc:
        p.error(str(exc))

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main())
