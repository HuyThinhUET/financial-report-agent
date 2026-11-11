Title: KLTN Agent phân tích báo cáo/hồ sơ tài chính

# 1. Tìm hiểu

## 1.1. Các khái niệm

- Check list cần tìm hiểu:
    - [ ]  HOSE/HNX/UPCoM
    - [ ]  khái niệm & cách tính: doanh thu, lợi nhuận sau thuế, tài sản, nợ, dòng tiền, EPS…  → Để tính toán và so sánh
    - [ ]  
- Báo cáo tài chính (Financial Statement): Là hệ thống thông tin kinh tế và tài chính của một doanh nghiệp được lập theo các biểu mẫu và chuẩn mực kế toán quy định. Tài liệu này phản ánh tổng quan tình hình tài sản, nguồn vốn, kết quả hoạt động kinh doanh và các luồng tiền trong một kỳ kế toán.
    - Thành phần:
        - Cân đối kế toán (Balance Sheet) → tài sản, nguồn vốn hình thành
        - Báo cáo kết quả hoạt động kinh doanh (Income Statement) → Doanh thu, chi phí, lãi, cổ tức
        - Báo cáo lưu chuyển tiền tệ (Cash Flow Statement) → Dòng tiền
        - Thuyết minh báo cáo tài chính → Phần còn lại, làm cho 3 thg trên dễ hiểu hơn
    - Đối tượng sử dụng:
        - Ng quản lý doanh nghiệp → nắm bắt tình hình kinh doanh, tình hình các khoản nợ đến hạn, nghĩa vụ tài chính phải thanh toán, kiểm soát nguồn lực tài chính để mở động HĐ KD
        - Tổ chức tín dụng, nhà đầu tư → Đánh giá tín dụng → có nên cho vay/đầu tư
        - Cơ quan thuế → cơ sở để thi hành nghĩa vụ thuế
    - Tiêu chuẩn
        - Khắt khe và phức tạp
        - Thế giới: Chuẩn IFRS và US GAAP
        - Việt Nam: VAS → Nhưng đang được hướng dẫn để chuyển sang chuẩn thế giới
    - Báo cáo tài chính phải được kiểm toán (kiểm tra và xác minh các con số là hợp lý, trung thực và đúng theo luật pháp) → Dịch vụ từ 4 kiểm toán lớn nhất thế giới (Big 4 kế kiểm): EY, PWC, KPMG, Deloitte
    - Một số vấn đề
        - Ban lãnh đạo doanh nghiệp có thể tác động làm thay đổi báo cáo tài chính → NMJ
        - Tất cả doanh nghiệp đều có xu hướng viết BCTC theo chiến lược, lợi ích của mình → Đều có sai lệch trong BCTC → Những nhà đầu tư chuyên nghiệp
- Hồ sơ tài chính

## 1.2. Cách đọc 1 báo cáo tài chính

- Nguyên tắc/ quy định nên làm:
    - Giá gốc:
        - Phần tài sản trên cân đối kế toán là giá gốc: Giá khi mua >< Giá thị trường
        - Doanh thu & chi phí trong báo cáo KQHĐKD thì lại ghi nhận giá mua khi phát sinh báo cáo (giá thị trường hiện tại) ⇒ Mismatch? → Cần đọc báo cáo lưu chuyển tiền tệ
    - Thiếu thông tin định tính:
        - Dữ liệu, xu hướng thị trường
        - Mức độ cạnh trành với cty đối thủ
        - Chất lượng lãnh đạo và nhân viên
        - Đổi mới, ứng dụng công nghệ
        - Chiến lược
        - ⇒ BCTC chỉ là 1 phần trong những thứ cần nắm được để đánh giá
    - Không có cách đọc BCTC đúng nhất. Tùy theo đối tượng và nhu cầu
    - So sánh:
        - So sánh cùng một doanh nghiệp qua nhiều năm
        - So sánh với các doanh nghiệp khác cùng ngành
- Chu kỳ kinh tế?

## 1.3. Bộ dữ liệu

## 1.4 Các chỉ số tối thiểu phải phân tích

# 2. Formulate bài toán

## 2.1 Định nghĩa bài toán và ý nghĩa

- Xây dựng Agent phân tích và giải thích báo cáo tài chính công khai của doanh nghiệp niêm yết Việt Nam cho nhà đầu tư cá nhân ít kinh nghiệm, bắt đầu với một tập doanh nghiệp đại diện
- MVP & Khóa luận:
    - Phạm vi:
        - 20-50 doanh nghiệp phi tài chính trong 2-3 năm gần nhất
        - 3 ngành đại diện: Bán lẻ, sản xuất, bất động sản
    - Mục tiêu: Tải báo cáo, hỏi đáp có nguồn, giải thích 8-12 chỉ số cơ bản → Giải thích và tổng hợp bằng chứng, không đưa ra khuyến nghị mua bán, giá mục tiêu hoặc cam kết lợi nhuận
    - Yêu cầu:
        - Trả lời chính xác >90%
        - Có citation chắc chắn trong câu trả lời
        - (Optional) So sánh cùng công ty trong nhiều năm gần nhất, so sánh với các đối thủ cùng ngành
        - Ưu tiên rule-based hơn LLM
        - Cách lưu dữ liệu: 2 lớp:
            - raw evidence: Nguyên văn từ PDF, kèm URL, trang, bảng
            - normalized metrics
        - Trả lời theo kiểu streaming
        - Văn phong dễ hiểu, súc tích
        - Giao diện?
        - Deploy?
    - Kiến trúc dự kiến:
        - Luồng xử lý dữ liệu (Hiện tại là tiền xử lý trước. Cải tiến: sub-agent search → nếu người dùng hỏi câu hỏi out-domain thì cũng có thể chạy thêm để lấy ttin về doanh nghiệp mới, nhóm ngành mới):
            
            Luồng sản phẩm/dữ liệu
            Nguồn công bố chính thức
            (HOSE/HNX/UPCoM + trang IR doanh nghiệp)
            → Crawler + manifest
            → PDF parser / table extractor
            → Phân loại ngành + chọn schema
            (CommonSchema + IndustrySchema)
            → Extractor theo schema + chuẩn hóa dữ liệu + citation
            → Kho dữ liệu evidence-first
            
        - Luồng truy vấn Financial-report-agent:
        
        ```
        Câu hỏi người dùng
        → Financial Analysis Agent
           ├─ Nhận diện ý định và mức độ hiểu biết của người dùng
           ├─ Lập kế hoạch phân tích
           ├─ RAG: tìm bằng chứng trong báo cáo
           ├─ Truy vấn dữ liệu chuẩn hóa
           ├─ Gọi calculator: tính ratio, tăng trưởng, so sánh
           ├─ Verifier: kiểm tra nguồn, đơn vị, kỳ báo cáo, phép tính
           └─ Sinh câu trả lời dễ hiểu + citation + cảnh báo
        → Giao diện
        → Đánh giá agent
        ```
        
- Mở rộng:
    - Quy mô:
        - Level 1: Toàn bộ doanh nghiệp trong 1 số ngành, tự động crawl dữ liệu định kỳ, tự động tìm dữ liệu doanh nghiệp/ ngành mới ngoài kho tri thức nếu câu trả lời của user hỏi về doanh nghiệp mới
        - Level 2: Toàn bộ HOSE/HNX/UPCoM
        - Level 3: Mở rộng ra các ngành tài chính như ngân hàng
    - Mức độ:
        - So sánh trong 5-10 năm
        - So sánh với các đối thủ cùng ngành
- Các pain point dự kiến:
    - Không tìm được BCTC trong 1 năm nào đó → Chuỗi data không phải BCTC của các năm liên tiếp
    - Chuẩn hóa dữ liệu, mapping cách các doanh nghiệp đặt tên khoản mục, định dạng bảng và kỳ kế toán