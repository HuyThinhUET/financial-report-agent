import argparse, datetime, json, os, subprocess, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = Path(__file__).with_name('schema.json')

def run(source, model):
    data = json.loads(source.read_text(encoding='utf-8-sig'))
    insights = data['insights']
    items = [{'id': x['id'], 'text': x['text']} for x in insights]
    if len({x['id'] for x in items}) != len(items):
        raise ValueError('Duplicate insight IDs')
    out = source.parent / 'questions.json'
    temp = source.parent / 'questions.generated.tmp'
    metrics_path = source.parent / 'questions_metrics.json'
    prompt = ('Với từng insight dưới đây, tạo đúng một câu hỏi tiếng Việt ngắn gọn kiểu từ khóa, tự nhiên như nhà đầu tư hỏi, để câu trả lời có thể bao gồm insight đó. Không tiết lộ kết luận hoặc số liệu của insight trong câu hỏi, không yêu cầu chỉ dẫn hay phương pháp phân tích. Giữ ID chính xác. Trả JSON theo schema. Bối cảnh báo cáo: ' + json.dumps(data.get('document', {}), ensure_ascii=False) + '\nInsights: ' + json.dumps(items, ensure_ascii=False))
    cmd = ['codex', 'exec', '--ephemeral', '--json', '--skip-git-repo-check', '--sandbox', 'read-only', '--color', 'never', '-m', model, '-c', 'model_reasoning_effort="medium"', '--output-schema', str(SCHEMA), '-o', str(temp), '-']
    start = time.monotonic()
    metrics = {'model': model, 'reasoning_effort': 'medium', 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'token_usage': None}
    try:
        proc = subprocess.run(cmd, input=prompt, text=True, encoding='utf-8', errors='replace', capture_output=True, cwd=ROOT)
        metrics['exit_code'] = proc.returncode
        for line in proc.stdout.splitlines():
            try: event = json.loads(line)
            except ValueError: continue
            if event.get('type') == 'turn.completed': metrics['token_usage'] = event.get('usage')
            if event.get('type') == 'thread.started': metrics['thread_id'] = event.get('thread_id')
        if proc.returncode: raise RuntimeError(proc.stderr[-4000:] or proc.stdout[-4000:])
        result = json.loads(temp.read_text(encoding='utf-8'))['questions']
        mapping = {x['id']: x['question'] for x in result}
        if len(mapping) != len(result) or set(mapping) != {x['id'] for x in items} or any(not isinstance(q, str) or not q.strip() for q in mapping.values()): raise ValueError('Invalid question coverage')
        out.write_text(json.dumps({'document': data.get('document'), 'questions': [{'insight_id': x['id'], 'insight': x['text'], 'question': mapping[x['id']]} for x in items]}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        metrics['status'] = 'completed'
    except Exception as e:
        metrics.update(status='failed', error=str(e))
    finally:
        temp.unlink(missing_ok=True)
        metrics['elapsed_seconds'] = round(time.monotonic()-start, 2)
        metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(source.parent.name, metrics['status'], metrics.get('error', '')[:200], flush=True)
    return metrics['status'] == 'completed'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('paths', nargs='+', type=Path, help='Dataset directories or insights.json files')
    p.add_argument('--model', default='gpt-6-luna')
    p.add_argument('--workers', type=int, default=1, help='Number of datasets to process concurrently')
    a = p.parse_args()
    sources = sorted({f for path in a.paths for f in ([path] if path.is_file() else path.rglob('insights.json'))})
    if not sources: p.error('No insights.json found')
    if a.workers < 1: p.error('--workers must be positive')
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        results = list(pool.map(lambda x: run(x, a.model), sources))
    raise SystemExit(0 if all(results) else 1)

if __name__ == '__main__': main()
