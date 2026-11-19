import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pymupdf
from data_downloader.downloader import candidates, run
from data_downloader.sources import Source

class FakeClient:
    def __init__(self, pages):
        self.pages = pages
    def get(self, url):
        return self.pages[url]

class DownloaderTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dest = self.root / 'data'
        self.index = self.dest / 'manifest.json'
        self.page = 'https://example.com/reports'
        self.pdf_url = 'https://example.com/2024_BCTC.pdf/view'
        self.source = Source('ELC', 'technology', self.page, ('example.com',))
        doc = pymupdf.open()
        doc.new_page()
        self.pdf = doc.tobytes()
        doc.close()
        self.client = FakeClient({self.page: f'<a href="{self.pdf_url}">BCTC</a>'.encode(), self.pdf_url: self.pdf})

    def call(self, **kwargs):
        with patch('data_downloader.downloader.time.sleep'):
            return run([self.source], client=self.client, root=self.root, dest=self.dest, index=self.index, **kwargs)

    def test_download_resume_and_preserve_metadata(self):
        self.assertEqual(self.call(target=1), (1, []))
        data = json.loads(self.index.read_text(encoding='utf8'))
        data['historical_metadata'] = {'keep': True}
        self.index.write_text(json.dumps(data), encoding='utf8')
        self.assertEqual(self.call(target=1), (0, []))
        after = json.loads(self.index.read_text(encoding='utf8'))
        self.assertEqual(after['historical_metadata'], {'keep': True})
        self.assertEqual(len(after['reports']), 1)
        self.assertTrue((self.root / after['reports'][0]['pdf']).is_file())

    def test_augmentation_preserves_baseline_target_and_metadata(self):
        self.call(target=1)
        doc = pymupdf.open()
        doc.new_page().insert_text((20, 20), 'second report')
        second = doc.tobytes()
        doc.close()
        extra = Source('CMG', 'technology', 'https://example.com/extra.pdf', ('example.com',), 'pdf', self.page)
        with patch('data_downloader.downloader.time.sleep'):
            result = run([extra], augment=True, client=FakeClient({extra.url: second}),
                         root=self.root, dest=self.dest, index=self.index)
        self.assertEqual(result, (1, []))
        manifest = json.loads(self.index.read_text(encoding='utf8'))
        self.assertEqual(manifest['target'], 1)
        self.assertEqual(manifest['count'], 2)
        self.assertEqual(manifest['reports'][1]['collection'], 'vnr500_2026_top10_private_information')

    def test_modified_pdf_does_not_change_manifest(self):
        self.call(target=1)
        before = self.index.read_bytes()
        row = json.loads(before)['reports'][0]
        (self.root / row['pdf']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'modified PDF'):
            self.call(target=2)
        self.assertEqual(self.index.read_bytes(), before)

    def test_filter_annual_and_keep_underscore_bctc(self):
        html = '<a href="/abc_BCTC_2024.pdf/view">BCTC</a><a href="/bao_cao_thuong_nien_BCTC.pdf">BCTC</a><a href="https://other.com/BCTC.pdf">BCTC</a>'
        links = list(candidates(self.source, FakeClient({self.page: html.encode()})))
        self.assertEqual(len(links), 1)
        self.assertIn('abc_BCTC_2024', links[0][0])

if __name__ == '__main__':
    unittest.main()
