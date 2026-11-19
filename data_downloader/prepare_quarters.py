import json,concurrent.futures,re
from pathlib import Path
from bs4 import BeautifulSoup
from data_downloader.downloader import HttpClient,fold
p=Path('data/data_raw/5-linh-vuc/danh_sach_nguon.json');old=json.loads(p.read_text(encoding='utf8'));seen={x['source_url'] for x in old if x.get('source_url')};jobs=[]
for x in old:
 t=x['company']; k=(x['sector'],t)
 if k not in jobs and t!='VTP':jobs.append(k)
def find(pair):
 sector,ticker=pair;page=f'https://stock.hoana.vn/bao-cao-tai-chinh/{ticker}';found=[]
 try:
  html=HttpClient().get(page);soup=BeautifulSoup(html,'html.parser')
  for tr in soup.select('tbody tr'):
   tds=tr.find_all('td')
   if len(tds)<3:continue
   period=tds[0].get_text(' ',strip=True);f=fold(period)
   if not re.match(r'quy\s+[1-4]\s*/\s*20\d{2}',f):continue
   for a in tds[2].find_all('a',href=True):
    url=a['href']; label=fold(a.get_text(' ',strip=True))
    if 'hop nhat' not in label or not url.startswith('https://') or not url.lower().split('?')[0].endswith('.pdf') or url in seen:continue
    found.append({'sector':sector,'company':ticker,'discovery_page':page,'source_url':url,'period':period,'selection':'quarterly_candidate','error':'','download_status':'chua_tai'});break
   if len(found)>=2:break
 except Exception as e:return pair,[],str(e)
 return pair,found,''
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool: results=list(pool.map(find,jobs))
new=[v for _,ls,_ in results for v in ls]; old.extend(new);p.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
summary={'attempted_companies':len(jobs),'sources':len(new),'companies_with_source':len({x['company'] for x in new}),'missing_companies':[c for (_,c),ls,err in results if not ls],'errors':[{ 'company':c,'error':err} for (_,c),ls,err in results if err]}
Path('data/data_raw/5-linh-vuc/bo_sung_quy_nguon.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(summary,ensure_ascii=False))
