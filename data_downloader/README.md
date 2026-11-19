# Module tải dữ liệu BCTC

Chạy tại thư mục gốc repo (Python 3.11+):

```powershell
pip install -r data_downloader/requirements.txt
python -m data_downloader
python -m data_downloader --augment
python -m data_downloader --consolidated
```

`--consolidated` tải danh sách PDF BCTC hợp nhất đã chọn trong
`consolidated_sources.json`, tối đa 10 đường dẫn cho mỗi doanh nghiệp. Lệnh
dùng lại manifest và bỏ qua URL hoặc nội dung trùng đã có; không xóa những
báo cáo cũ ngoài danh sách. Không phải mọi doanh nghiệp đều có đủ 10 nguồn.
Các tài liệu vẫn cần rà soát nội dung, kỳ báo cáo và chất lượng scan; các bản
quý, bán niên và năm có thể có kỳ trùng lặp. Lệnh trả mã 1 nếu có lỗi tải.

Lệnh đầu chuẩn bị tối đa 100 PDF, ưu tiên HPT và ELCOM trước Hòa Phát; dùng `--target 50` để đổi mục tiêu. Lệnh thứ hai bổ sung nguồn FPT và CMC từ danh sách VNR500, không áp giới hạn 100. Nguồn được khai báo trong `sources.py`; để thêm nguồn cần kiểm tra domain, trang IR và định dạng liên kết tương ứng.

Cả hai lệnh dùng `data/data_raw/tech-manufacturing-statements/manifest.json` và tiếp tục dữ liệu hiện có. Manifest chứa URL, trang phát hiện, hash, số trang, ngành và trạng thái kiểm tra. SHA-256 được kiểm tra trước khi tiếp tục; nếu file thiếu hoặc thay đổi, lệnh dừng và giữ nguyên manifest để người dùng xử lý. File trùng hash được bỏ qua; file đã tồn tại với tên xung đột không bị ghi đè. Ghi manifest sau mỗi file bằng tệp tạm và đổi tên. Không chạy đồng thời hai tiến trình tải vào cùng thư mục.

Chế độ mặc định trả mã 1 nếu không đạt mục tiêu; `--augment` trả mã 1 nếu có lỗi tải. Số lượng và lỗi nằm trong manifest. Tài liệu chỉ là ứng viên: kiểm tra công ty, kỳ, phạm vi, chất lượng scan và nguồn trước khi dùng. Các phiên bản cùng kỳ không phải mẫu độc lập. BCTC scan có thể cần OCR.

Ứng dụng kiểm tra robots.txt; HTTP 4xx trừ 429 được xem là không có quy tắc, lỗi kết nối hoặc 429 thì không crawl. Bộ lọc URL không xác nhận nội dung toàn bộ PDF; một số tài liệu có trang công bố thông tin trước BCTC. Danh sách doanh nghiệp VNR500 và giới hạn nằm trong `evaluation/insights_builder/VNR500_CONG_NGHE_2026.md`.

Chạy kiểm thử không cần mạng: `python -m unittest data_downloader.test_downloader`.
