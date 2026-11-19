# Danh sách doanh nghiệp công nghệ để mở rộng corpus

Nguồn: [VNR500 2026, nhóm hoạt động thông tin khác](https://vnr500.vn/Nganh-nghe/Hoat-dong-thong-tin-khac-Post/98.html), lấy 10 doanh nghiệp đầu tiên của bảng **500 doanh nghiệp tư nhân lớn nhất** theo thứ tự trong trang. Đây không phải top 10 toàn bộ doanh nghiệp công nghệ Việt Nam: phạm vi loại doanh nghiệp nhà nước, loại nhiều doanh nghiệp công nghệ/viễn thông thuộc nhóm ngành khác, và có thể có quan hệ công ty mẹ – con. Dữ liệu hồ sơ FPT ghi B2/2026. Tham chiếu thứ hạng của VNR500, không tự khẳng định đây là thứ tự doanh thu đã kiểm toán độc lập.

| Thứ tự nhóm | Thứ hạng tư nhân VNR500 | Doanh nghiệp | Tình trạng BCTC trong corpus |
|---|---:|---|---|
| 1 | 9 | Công ty CP FPT | Đã bổ sung 12 PDF từ trang công bố của FPT |
| 2 | 29 | Công ty CP Giải pháp Thanh toán Việt Nam (VNPAY) | Chưa tìm được PDF nguồn chính thức công khai phù hợp trong lượt tìm này |
| 3 | 38 | Công ty CP Công nghệ và Dịch vụ Imedia | Chưa tìm được PDF nguồn chính thức công khai phù hợp trong lượt tìm này |
| 4 | 82 | Công ty CP Tập đoàn Công nghệ CMC (CMG) | Đã bổ sung 3 PDF từ CDN chính thức CMC |
| 5 | 105 | Công ty TNHH FPT IS | Chưa tìm được PDF BCTC riêng; FPT là công ty mẹ, không thay thế BCTC riêng |
| 6 | 185 | Công ty CP Công nghệ Elite | Chưa tìm được PDF nguồn chính thức công khai phù hợp trong lượt tìm này |
| 7 | 301 | Công ty CP MISA | Chưa tìm được PDF nguồn chính thức công khai phù hợp trong lượt tìm này |
| 8 | 328 | Công ty CP Công nghệ Bằng Hữu | Chưa tìm được PDF nguồn chính thức công khai phù hợp trong lượt tìm này |
| 9 | 347 | Công ty CP Dịch vụ Công nghệ Tin học HPT | Đã có 10 PDF trong corpus ban đầu |
| 10 | 417 | Công ty CP Đầu tư Thương mại và Phát triển Công nghệ FSI | Chưa tìm được PDF nguồn chính thức công khai phù hợp trong lượt tìm này |

Trạng thái “chưa tìm được” chỉ phản ánh lượt tìm hiện tại, không khẳng định doanh nghiệp không công bố. Hai URL FPT cũ phát hiện qua tìm kiếm trả 404; chúng được ghi trong `augmentation_failures` của manifest ở lần tải đầu. Các URL FPT hiện tại được phát hiện tự động từ [trang công bố thông tin FPT](https://fpt.com/vi/nha-dau-tu/thong-tin-cong-bo); ba PDF CMG được lựa chọn từ [nguồn PDF CMC](https://cdn.cmc.com.vn/img/posts/files/20250730%20-%20CMG%20-%20Bao%20cao%20tai%20chinh%20hop%20nhat%20Q1.2025%20-%20signed.pdf). Chạy `python -m data_downloader --augment` để cập nhật thêm file FPT đang hiển thị và kiểm tra nguồn đã biết; file trùng hash được bỏ qua.

FPT có tài liệu công bố đi kèm đầu file; BCTC nằm ở các trang sau. Kiểm tra trực quan 4 file mới (2 FPT, 2 CMC): tất cả có bảng hoặc mục lục BCTC; xem `data/data_raw/tech-manufacturing-statements/vnr500-sample/selected.json` và ảnh. Mẫu không khẳng định các file đã đầy đủ, chính xác hoặc đại diện cho cả tập. PDF scan cần OCR hoặc xử lý hình ảnh.
