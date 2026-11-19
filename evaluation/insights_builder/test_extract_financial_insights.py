import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
try:
    from . import extract_financial_insights as app
except ImportError:
    import extract_financial_insights as app


class ExtractionTests(unittest.TestCase):
    def test_detects_mangled_vietnamese(self):
        self.assertTrue(app.damaged_text({'text': 'T?ng C?ng ty C? ph?n Khoan v? D?ch v? Khoan D?u kh?'}))
        self.assertFalse(app.damaged_text({'text': 'Tổng Công ty Cổ phần Khoan và Dịch vụ Khoan Dầu khí?'}))

    def test_period_inference_excludes_publication_date_and_ambiguous_year(self):
        pdf = app.ROOT / 'data/hop_nhat_quy/a.pdf'
        self.assertEqual(app.infer({'source_label': '20260730 - BCTC Quy 2 nam 2026.pdf', 'company': 'AAA'}, pdf)['quarter'], 2)
        self.assertIsNone(app.infer({'source_label': '20260730 - BCTC Quy 2.pdf'}, pdf))
        self.assertIsNone(app.infer({'source_label': 'BCTC Quy III NDTC 2025-2026.pdf'}, pdf))

    def test_max_sample_counts_unprocessed_reports(self):
        rows = [{'pdf': str(i), 'company': f'C{i}', 'year': 2025, 'quarter': None} for i in range(4)]
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output/'001_C0_2025').mkdir()
            with patch.object(app, 'OUTPUT', output), patch.object(app, 'discover', return_value=rows), patch.object(app.shutil, 'which', return_value='codex'), patch.object(app, 'run', return_value='completed') as run, patch.object(app.sys, 'argv', ['script', '--max_sample', '2']):
                self.assertEqual(app.main(), 0)
                self.assertEqual([call.args[0]['company'] for call in run.call_args_list], ['C1', 'C2'])

    def test_run_is_ephemeral_and_preserves_empty_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root/'data'
            pdf = data/'x'/'hop_nhat_quy'/'A.pdf'
            pdf.parent.mkdir(parents=True)
            pdf.write_bytes(b'pdf')
            out = root/'evaluation'/'data_evaluate'
            row = {'pdf': str(pdf), 'company': 'A', 'year': 2025, 'quarter': 2}
            def fake(cmd, **kwargs):
                self.assertIn('--ephemeral', cmd)
                path = next(out.glob('001_A_2025_2'))
                (path/'insights.json').write_text('{"insights": []}', encoding='utf-8')
                kwargs['stdout'].write('{"type":"thread.started","thread_id":"new"}\n')
                return type('Proc', (), {'returncode': 0})()
            with patch.object(app, 'ROOT', root), patch.object(app, 'DATA', data), patch.object(app, 'OUTPUT', out), patch.object(app.subprocess, 'run', side_effect=fake):
                self.assertEqual(app.run(row, 'codex', None), 'failed')
                self.assertEqual(json.loads((out/'001_A_2025_2'/'metrics.json').read_text(encoding='utf-8'))['thread_id'], 'new')
                self.assertEqual(app.run(row, 'codex', None), 'skipped')


if __name__ == '__main__':
    unittest.main()
