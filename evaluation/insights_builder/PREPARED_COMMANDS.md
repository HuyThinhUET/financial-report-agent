# 20 l?nh tr?ch xu?t BCTC h?p nh?t

Ch?y t? th? m?c g?c d? ?n. N?m/qu? d??i ??y l?y t? nh?n ngu?n v? ph?i ???c Codex ??i chi?u trong PDF; xem `evaluation/README.md` tr??c khi ch?y. M?i l?nh m? m?t phi?n ??c l?p. STT th? m?c ???c c?p khi ch?y, kh?ng t??ng ?ng s? th? t? trong danh s?ch n?y.

```powershell
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_nam/PLX_5570d8cdb64de8f7.pdf' --company PLX --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_nam/GAS_fd3d1f4db3dc391f.pdf' --company GAS --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_nam/PVD_6ee20a554891c449.pdf' --company PVD --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dien/hop_nhat_nam/POW_64563ebb8ab5b365.pdf' --company POW --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/thuc_pham_do_uong/hop_nhat_nam/VNM_ee996ffcb87f0699.pdf' --company VNM --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/thuc_pham_do_uong/hop_nhat_nam/VHC_00629dd42ea6c9d3.pdf' --company VHC --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/thuc_pham_do_uong/hop_nhat_nam/HAG_b01fb85a00254d56.pdf' --company HAG --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/thuc_pham_do_uong/hop_nhat_nam/DBC_4e10208192ad4855.pdf' --company DBC --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/thep_vat_lieu/hop_nhat_nam/HPG_f38c5f75becf7d3f.pdf' --company HPG --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/thep_vat_lieu/hop_nhat_nam/NKG_ffcb04e447550aab.pdf' --company NKG --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/van_tai_logistics/hop_nhat_nam/VJC_91e9e25e46ff68d9.pdf' --company VJC --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/van_tai_logistics/hop_nhat_nam/GMD_fcb5cb9d53b0852f.pdf' --company GMD --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/van_tai_logistics/hop_nhat_nam/HAH_0d440679c82ea1f8.pdf' --company HAH --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/van_tai_logistics/hop_nhat_nam/VOS_0ee1a5068d1b2553.pdf' --company VOS --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_quy/PLX_925339daf7038fe2.pdf' --company PLX --year 2026 --quarter 2
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_quy/PLX_313a137962a9249f.pdf' --company PLX --year 2026 --quarter 1
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_quy/GAS_118f3b092ddce271.pdf' --company GAS --year 2026 --quarter 2
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_quy/GAS_853ad22dfe045d24.pdf' --company GAS --year 2026 --quarter 1
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dien/hop_nhat_quy/POW_4e888f2979eda1f5.pdf' --company POW --year 2026 --quarter 2
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dien/hop_nhat_quy/POW_e552ab844ec28cb5.pdf' --company POW --year 2026 --quarter 1
```

Ch?y c? danh s?ch tu?n t?, t?i ?a 20 b?o c?o ch?a c? th? m?c:

```powershell
python -m evaluation.insights_builder --manifest evaluation/insights_builder/prepared_statements.json --max_sample 20
```
