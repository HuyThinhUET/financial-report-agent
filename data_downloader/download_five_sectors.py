import json
from pathlib import Path
from urllib.parse import urlsplit
from data_downloader.sources import Source
from data_downloader.downloader import run, ROOT
base=ROOT/'data/data_raw/5-linh-vuc'; entries=json.loads((base/'danh_sach_nguon.json').read_text(encoding='utf8'))
sources=[Source(x['company'],x['sector'],x['source_url'],(urlsplit(x['source_url']).hostname,),'pdf',x['discovery_page']) for x in entries if x['source_url']]
added, failures=run(sources,root=ROOT,dest=base,index=base/'manifest.json')
print(f'Da tai {added}; loi {len(failures)}')
