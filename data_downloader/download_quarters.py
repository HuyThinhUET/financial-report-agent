import json
from pathlib import Path
from urllib.parse import urlsplit
from data_downloader.sources import Source
from data_downloader.downloader import run,ROOT,write_manifest
p=ROOT/'data/data_raw/5-linh-vuc';idx=p/'manifest.json';entries=json.loads((p/'danh_sach_nguon.json').read_text(encoding='utf8'));m=json.loads(idx.read_text(encoding='utf8'));past=m.get('failures',[])
sources=[Source(x['company'],x['sector'],x['source_url'],(urlsplit(x['source_url']).hostname,),'pdf',x['discovery_page']) for x in entries if x.get('selection')=='quarterly_candidate']
try:
 added,failed=run(sources,root=ROOT,dest=p,index=idx)
finally:
 after=json.loads(idx.read_text(encoding='utf8'));after['quarterly_failures']=after.get('failures',[]);after['failures']=past;write_manifest(idx,after)
print('Added',added,'errors',len(failed))
