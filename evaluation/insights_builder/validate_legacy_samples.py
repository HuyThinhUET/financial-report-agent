"""Check PDF identity, saved evidence and numeric strings for generated drafts."""
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import pymupdf

BASE = Path(__file__).resolve().parents[2] / 'data' / 'data_evaluate'


def evaluate(directory):
    errors, warnings = [], []
    config = json.loads((directory/'run_config.json').read_text(encoding='utf-8'))
    pdf = Path(config['source_pdf'])
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if config['sha256'] != digest:
        errors.append('PDF SHA-256 differs from run_config')
    doc = pymupdf.open(pdf)
    data = json.loads((directory/'insights.json').read_text(encoding='utf-8'))
    raw = data.get('insights')
    if not isinstance(raw, list):
        raise ValueError('insights must be an array')
    seen, checked = set(), 0
    for ix, item in enumerate(raw):
        iid = str(item.get('id', ix))
        if iid in seen:
            errors.append(f'{iid}: duplicated id')
        seen.add(iid)
        evidence = item.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            errors.append(f'{iid}: no evidence')
            continue
        quotes = []
        for e in evidence:
            page, quote = e.get('pdf_page'), e.get('quote')
            if not isinstance(page, int) or not 1 <= page <= len(doc) or not isinstance(quote, str) or not quote.strip():
                errors.append(f'{iid}: invalid page/quote')
                continue
            if quote not in doc[page-1].get_text():
                errors.append(f'{iid}: quote does not match page {page}')
            checked += 1
            quotes.append(quote)
        if item.get('review_status') != 'draft':
            warnings.append(f'{iid}: review status not draft')
        supported = ' '.join(quotes)
        # PDF tables may use either commas or periods as thousands separators.
        supported_numbers = {re.sub(r'[.,\s]', '', n) for n in
                             re.findall(r'(?<!\d)\d{1,3}(?:[.,][ \t]*\d{3})+(?!\d)', supported)}
        for number in re.findall(r'(?<!\d)\d{1,3}(?:\.\d{3})+(?!\d)', item.get('insight', '')):
            if number.replace('.', '') not in supported_numbers:
                warnings.append(f'{iid}: {number} not found in evidence with a recognized thousands separator')
    calc = json.loads((directory/'calculations.json').read_text(encoding='utf-8'))
    calcs = calc if isinstance(calc, list) else calc.get('calculations')
    if not isinstance(calcs, list):
        errors.append('calculations must contain an array')
        calcs = []
    for ix, calculation in enumerate(calcs):
        cid = str(calculation.get('id', ix))
        evidence = list(calculation.get('evidence', []))
        inputs = calculation.get('input_values', [])
        if isinstance(inputs, list):
            for value in inputs:
                if isinstance(value, dict):
                    evidence.extend(value.get('evidence', []))
        if not evidence:
            warnings.append(f'{cid}: calculation has no directly checkable evidence')
        for e in evidence:
            page, quote = e.get('pdf_page'), e.get('quote')
            if not isinstance(page, int) or not 1 <= page <= len(doc) or not isinstance(quote, str) or not quote.strip():
                errors.append(f'{cid}: invalid calculation evidence')
            elif quote not in doc[page - 1].get_text():
                errors.append(f'{cid}: calculation quote does not match page {page}')
        # Verify the arithmetic only for recognizable two-input formulas.
        if isinstance(inputs, list) and len(inputs) == 2:
            try:
                a, b = [Decimal(str(value['value'])) for value in inputs]
                actual = Decimal(str(calculation['result']))
                formula = str(calculation.get('formula', '')).lower().replace(' ', '')
                if not b or '/' not in formula:
                    raise ValueError('unsupported formula')
                expected = a / b
                if '-1' in formula:
                    expected -= 1
                if '100' in formula:
                    expected *= 100
                if abs(expected - actual) > Decimal('0.011'):
                    warnings.append(f'{cid}: arithmetic differs from inferred two-input formula')
            except (KeyError, InvalidOperation, ValueError, TypeError):
                warnings.append(f'{cid}: arithmetic not automatically checked')
    result = {'status': 'failed' if errors else 'passed_with_warnings' if warnings else 'passed',
              'insights_count': len(raw), 'evidence_count': checked, 'calculations_count': len(calcs),
              'errors': errors, 'warnings': warnings,
              'limits': ['Kiểm tra chuỗi và hash; chỉ thử tính lại công thức hai đầu vào nhận diện được, không xác nhận ngữ nghĩa hay bố cục bảng.',
                         'Tất cả kết quả cần đối chiếu PDF và con người kiểm duyệt.']}
    (directory/'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(directory.name, result['status'], len(raw), len(calcs), 'errors', len(errors), 'warnings', len(warnings))


if __name__ == '__main__':
    for directory in sorted(BASE.iterdir()):
        if directory.is_dir() and (directory/'run_config.json').exists():
            if not (directory/'insights.json').exists() or not (directory/'calculations.json').exists():
                print(directory.name, 'incomplete')
                continue
            try:
                evaluate(directory)
            except (ValueError, KeyError, OSError) as exc:
                print(directory.name, 'validation error:', exc)
