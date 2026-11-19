"""Nguồn BCTC công khai đã chọn và thứ tự ưu tiên."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Source:
    company: str
    sector: str
    url: str
    hosts: tuple[str, ...]
    kind: str = 'page'
    discovery_page: str = ''

BASELINE = [Source('HPT', 'technology', 'https://www.hpt.vn/co-dong', ('www.hpt.vn',))]
BASELINE += [Source('ELC', 'technology', f'https://www.elcom.com.vn/co-dong/bao-cao-tai-chinh?page=1&year={year}', ('www.elcom.com.vn', 'elcom.com.vn')) for year in range(2026, 2016, -1)]
BASELINE += [Source('HPG', 'manufacturing', 'https://www.hoaphat.com.vn/quan-he-co-dong/bao-cao-tai-chinh', ('www.hoaphat.com.vn', 'file.hoaphat.com.vn'))]

FPT_PAGE = 'https://fpt.com/vi/nha-dau-tu/thong-tin-cong-bo'
VNR500 = [Source('FPT', 'technology', FPT_PAGE, ('fpt.com',), 'fpt')]
VNR500 += [Source('CMG', 'technology', url, ('cdn.cmc.com.vn',), 'pdf', 'https://www.cmc.com.vn/') for url in (
    'https://cdn.cmc.com.vn/img/posts/files/20250730%20-%20CMG%20-%20Bao%20cao%20tai%20chinh%20hop%20nhat%20Q1.2025%20-%20signed.pdf',
    'https://cdn.cmc.com.vn/img/posts/files/20241030%20-%20Bao%20cao%20tai%20chinh%20hop%20nhat%20quy%202.%202024.signed.pdf',
    'https://cdn.cmc.com.vn/img/posts/files/20231027%20-%20CMG%20-%20Bao%20cao%20tai%20chinh%20hop%20nhat%20Quy%202%202023.signed.pdf',
)]
