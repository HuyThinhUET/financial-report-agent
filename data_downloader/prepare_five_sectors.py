import json, concurrent.futures, re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from data_downloader.downloader import HttpClient, fold
sectors={
 'dau_khi_khoang_san':['PLX','OIL','BSR','GAS','PVD','PVS','PVC','PVB','PVO','TDN'],
 'dien':['POW','PGV','NT2','PPC','QTP','HND','VSH','BTP','GEG','TMP'],
 'thuc_pham_do_uong':['VNM','MSN','MCH','SAB','QNS','KDC','VHC','MPC','HAG','DBC'],
 'thep_vat_lieu':['HPG','HSG','NKG','TVN','POM','SMC','VGS','TLH','DTL','VCA'],
 'van_tai_logistics':['HVN','VJC','ACV','VTP','GMD','SCS','HAH','VOS','PHP','VSC']}
root=Path('data/data_raw/5-linh-vuc'); root.mkdir(parents=True,exist_ok=True)
def get(pair):
 sector,ticker=pair; page=f'https://stock.hoana.vn/bao-cao-tai-chinh/{ticker}'; out={'sector':sector,'company':ticker,'discovery_page':page,'source_url':'','period':'','selection':'candidate','error':''}
 try:
  soup=BeautifulSoup(HttpClient().get(page),'html.parser'); candidates=[]
  for tr in soup.select('tbody tr'):
   cells=tr.find_all('td');
   if len(cells)<3: continue
   period=cells[0].get_text(' ',strip=True); f=fold(period)
   if 'ban nien' in f or not re.search(r'\b(nam|quy)\b',f):continue
   for a in cells[2].find_all('a',href=True):
    if 'hop nhat' not in fold(a.get_text(' ',strip=True)):continue
    u=a['href']; host=urlparse(u).hostname or ''
    if not u.startswith('https://') or not (u.lower().split('?')[0].endswith('.pdf')):continue
    score=(0 if 'nam 2025' in f else 1 if 'nam ' in f else 2)
    candidates.append((score,u,period));break
  if candidates:
   _,out['source_url'],out['period']=min(candidates,key=lambda x:x[0])
  else:out['error']='Khong tim thay PDF hop nhat nam/quy co nhan tai trang nguon'
 except Exception as e:out['error']=str(e)
 return out
jobs=[(s,t) for s,ts in sectors.items() for t in ts]
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool: data=list(pool.map(get,jobs))
(root/'danh_sach_nguon.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for s in sectors:
 a=[x for x in data if x['sector']==s]; print(s,'sources',sum(bool(x['source_url']) for x in a),'missing',','.join(x['company'] for x in a if not x['source_url']))
