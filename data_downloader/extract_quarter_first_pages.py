import json,pymupdf
from pathlib import Path
root=Path('data/data_raw/5-linh-vuc');folder=root/'trang-dau';rows=json.loads((root/'manifest.json').read_text(encoding='utf8'))['reports'];n=0
for r in rows:
 p=Path(r['pdf']); png=folder/(p.stem+'.png'); txt=folder/(p.stem+'.txt')
 if png.exists() and txt.exists():continue
 with pymupdf.open(p) as d:
  d[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),colorspace=pymupdf.csGRAY).save(png);txt.write_text(d[0].get_text(),encoding='utf8');n+=1
print('Pages created',n)
