import csv,json,re,hashlib,unicodedata
from pathlib import Path
root=Path('data/data_raw/5-linh-vuc');manifest=root/'manifest.json';m=json.loads(manifest.read_text(encoding='utf8'))
entries=json.loads((root/'danh_sach_nguon.json').read_text(encoding='utf8'));byurl={x['source_url']:x for x in entries if x['source_url']}; sampled={'PLX_5570d8cdb64de8f7','POW_64563ebb8ab5b365','VNM_ee996ffcb87f0699','HPG_f38c5f75becf7d3f','VTP_cf43d73ecb17bff0','QNS_562c814c82c1d029'}
quarter_samples={'PLX_925339daf7038fe2','POW_4e888f2979eda1f5','VNM_fd144a9acb3bacbc','HPG_2ad37ccd3812a3bc','VTP_d61dbe66f8c76f38'}
sampled.update(quarter_samples)
def fold(s):return ''.join(c for c in unicodedata.normalize('NFD',s.lower().replace('đ','d')) if unicodedata.category(c)!='Mn')
rows=[]; moved=[]
for x in m['reports']:
 src=Path(x['pdf']); ocr=(root/'trang-dau'/f"{src.stem}.ocr.txt").read_text(encoding='utf8'); native=(root/'trang-dau'/f'{src.stem}.txt').read_text(encoding='utf8'); s=fold(ocr+' '+native)
 cons=bool(re.search(r'\b(?:hop|hvp|hgp|hep|hcyp|hqp|h[oea]p)\s+nhat\b|consolidated\s+financial',s)); separate=bool(re.search(r'\brieng\b|separate\s+financial',s))
 cat='can_kiem_tra';reason='OCR trang đầu không xác định chắc phạm vi hoặc kỳ; cần kiểm tra.'
 if x['id']=='VTP_cf43d73ecb17bff0': cat='sai_doanh_nghiep';reason='Kiểm tra mẫu: trang đầu ghi Công ty CP Thuốc sát trùng Việt Nam, không phải Viettel Post.'
 elif cons and not separate:
  if re.search(r'\bqu[y?!]*\s*(?:[1-4]|i{1,3}|iv)\b|quarter\s*[1-4]|\bq[1-4]\b',s):cat='hop_nhat_quy';reason='OCR trang đầu nhận diện hợp nhất và nhãn quý; có thể gồm số liệu lũy kế.'
  elif re.search(r'ban nien|giua nien|six.month|6 thang|sau thang',s):cat='ky_khac_can_kiem_tra';reason='Trang đầu có dấu hiệu bán niên; không coi là báo cáo quý.'
  elif re.search(r'\b(?:cho nam|nam tai chinh|financial year|for the year|nam 20\d{2}|nam ket thuc)\b',s):cat='hop_nhat_nam';reason='OCR trang đầu nhận diện hợp nhất và năm; chưa kiểm chứng nội dung.'
 if x['id'] in {'PLX_5570d8cdb64de8f7','POW_64563ebb8ab5b365','VNM_ee996ffcb87f0699','HPG_f38c5f75becf7d3f'}:cat='hop_nhat_nam';reason='Mẫu kiểm tra trực quan: trang đầu ghi hợp nhất năm 2025.'
 if x['id']=='QNS_562c814c82c1d029':cat='hop_nhat_nam';reason='Kiểm tra trang đầu qua nguồn QNS: BCTC hợp nhất năm 2025.'
 if x['id'] in quarter_samples:cat='hop_nhat_quy';reason='Kiểm tra trực quan trang đầu: BCTC hợp nhất quý; có thể kèm số liệu lũy kế.'
 if byurl[x['source_url']].get('selection','').startswith('quarterly_candidate') and cat=='hop_nhat_nam':
  cat='can_kiem_tra';reason='Nguồn gắn nhãn báo cáo quý nhưng OCR trang đầu chưa xác định được quý.'
 dst=root/x['sector']/cat/src.name
 if not src.exists() or (dst.exists() and src!=dst):raise ValueError(f'Path conflict: {src} {dst}')
 dst.parent.mkdir(parents=True,exist_ok=True)
 if src!=dst:src.rename(dst);moved.append((src,dst))
 x['pdf']=dst.as_posix();x['first_page_classification']=cat;x['first_page_review']='visual_sample' if x['id'] in sampled else 'ocr_unverified';x['review_status']='misidentified_company' if x['id']=='VTP_cf43d73ecb17bff0' else 'unreviewed'
 meta=byurl[x['source_url']]; meta['download_status']='sai_doanh_nghiep' if x['id']=='VTP_cf43d73ecb17bff0' else 'da_tai';meta['pdf']=x['pdf'];meta['first_page_classification']=cat
 rows.append({'nganh':x['sector'],'ma':x['company'],'phan_loai':cat,'ky_nguon_cong_bo':meta['period'],'pdf':x['pdf'],'anh_trang_dau':f"data/data_raw/5-linh-vuc/trang-dau/{src.stem}.png",'kiem_tra_thu_cong': 'co' if x['id'] in sampled else 'khong','nhan_xet':reason,'source_url':x['source_url'],'trang_nguon':meta['discovery_page']})
for x in entries:
 if not x.get('download_status') or x['download_status']=='chua_tai':
  if not x.get('source_url'):
   x['download_status']='chua_co_nguon'
  else:
   err=next((e['error'] for e in m.get('failures',[])+m.get('quarterly_failures',[]) if e['source_url']==x['source_url']),'')
   x['download_status']='loi_tai' if err else 'bo_qua_co_the_trung'
   x['error']=err
manifest.with_suffix('.json.part').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8');manifest.with_suffix('.json.part').replace(manifest)
(root/'danh_sach_nguon.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with (root/'phan_loai.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
from collections import Counter
print('Phan loai:',dict(Counter(x['phan_loai'] for x in rows)))
print('Linh vuc:',dict(Counter(x['nganh'] for x in rows)))
