# Kiến trúc MVP: Financial Report Analysis Agent

> Trạng thái: bản nháp để thảo luận. Kiến trúc này ưu tiên **agent phân tích**;
> thu thập và trích xuất dữ liệu chỉ là hạ tầng hỗ trợ. Nội dung sẽ được điều
> chỉnh dần khi xác định rõ hơn kiến thức tài chính, người dùng mục tiêu và bộ
> đánh giá.

## 1. Mục tiêu và phạm vi

Xây dựng agent hỗ trợ nhà đầu tư cá nhân ít kinh nghiệm đọc, hỏi và phân tích
báo cáo tài chính công khai của doanh nghiệp niêm yết Việt Nam. Agent phải giải
thích bằng ngôn ngữ dễ hiểu, tính toán có thể tái lập và dẫn chứng về tài liệu
gốc. Hệ thống **không** đưa khuyến nghị mua/bán, giá mục tiêu hoặc cam kết lợi
nhuận đầu tư.

Trước MVP, crawler được dùng để khảo sát và thu thập báo cáo công khai ban đầu.
Sau khi kiểm tra dữ liệu, một snapshot dataset có phạm vi kiểm soát được chọn để
chạy và đánh giá MVP. Mục tiêu “toàn bộ doanh nghiệp, mọi ngành” là hướng mở
rộng, không phải điều kiện hoàn thành MVP.

## 2. Tổng quan kiến trúc

```text
                         Đầu vào nghiên cứu / thiết kế
                       Scopus và các nguồn học thuật khác
                                      |
                                      v
               Phương pháp, baseline, tiêu chí/rubric đánh giá

Dataset báo cáo tài chính đã chuẩn bị                     Câu hỏi người dùng
(PDF + metadata, có thể kèm dữ liệu chuẩn hóa)                  |
                  |                                             v
                  v                              +---------------------------+
Chuẩn bị dữ liệu và bằng chứng              ->  | Financial Analysis Agent  |
                  |                              +---------------------------+
                  v                                    |  |  |   |      |
Kiểm tra dataset + manifest                              v  v  v   v      v
                  |                                  Plan RAG Data Calc Verify
                  v                                      \  |  |   |   /
   PDF parser / table extractor                            \ |  |   |  /
                  |                                        v  v   v v
                  v                                  Câu trả lời + citation
 Phân loại ngành + chọn schema
                  |
                  v
Extractor theo schema + chuẩn hóa + citation
                  |
                  v
       Kho tri thức evidence-first
```

Scopus là nguồn tìm tài liệu học thuật, **không phải** nguồn báo cáo tài chính
hay dataset cho MVP. Scopus giúp lựa chọn phương pháp agent, baseline và tiêu
chí đánh giá. Dataset MVP được chuẩn bị trước từ các báo cáo công bố công khai
hoặc nguồn dữ liệu có quyền sử dụng phù hợp.

## 3. Luồng chuẩn bị dữ liệu (hạ tầng hỗ trợ)

Luồng này chuẩn bị bằng chứng đáng tin cậy cho agent, nhưng không phải đóng góp
nghiên cứu chính của MVP.

```text
Dataset đã chuẩn bị sẵn
  -> kiểm tra chất lượng + manifest
  -> PDF parser / table extractor
  -> phân loại ngành + chọn schema
     (CommonSchema + IndustrySchema)
  -> extractor theo schema + chuẩn hóa dữ liệu + tạo citation
  -> kho tri thức evidence-first
```

### 3.1. Dataset đầu vào cho MVP

MVP bắt đầu từ một dataset được chuẩn bị trước. Dataset tối thiểu gồm PDF báo
cáo và metadata; có thể kèm bảng số liệu chuẩn hóa nếu có nguồn hợp lệ.

Crawler hỗ trợ tạo dataset ban đầu trước MVP: từ các trang IR công khai, phát
hiện và tải PDF, rồi ghi manifest có URL nguồn và hash. Sau khi khảo sát, chỉ
một phiên bản dataset được chọn và đóng băng cho thí nghiệm agent; crawler
không phải thành phần được đánh giá trong MVP.

Nguồn tạo dataset nên ưu tiên dữ liệu công khai chính thức:

- Cổng công bố thông tin của HOSE, HNX và UPCoM.
- Trang Quan hệ nhà đầu tư (Investor Relations - IR) của doanh nghiệp niêm yết.
- Báo cáo thường niên, báo cáo tài chính đã kiểm toán và một số báo cáo quý.

Trong MVP, dataset chỉ gồm một tập nhỏ có thể truy vết. Mỗi tài liệu phải lưu
URL nguồn gốc, kể cả khi file đã được tải sẵn.

### 3.2. Kiểm tra dataset và manifest

Thay vì crawler, MVP xác thực dataset đầu vào: kiểm tra file mở được, không
trùng lặp, đúng doanh nghiệp/năm/loại báo cáo, và có nguồn gốc rõ ràng. Manifest
làm cho bộ dữ liệu có thể tái lập.

Các trường manifest gợi ý:

```text
document_id, company_code, company_name, report_type, fiscal_year,
consolidation_scope, source_url, downloaded_at, file_name, sha256,
language, page_count
```

### 3.3. PDF parser và table extractor

Bước này chuyển PDF thành văn bản theo từng trang, bảng và, khi cần, kết quả
OCR. Phải giữ số trang và nhãn bảng để câu trả lời sau này có thể quay về đúng
bằng chứng gốc.

### 3.4. Phân loại ngành và chọn schema

Trong MVP, ngành nên lấy từ bảng mapping quản lý thủ công, ví dụ
`ticker -> industry`, dựa trên phân loại của sở giao dịch hoặc doanh nghiệp.
Chưa cần xây mô hình AI phân loại ngành.

Hệ thống chọn đồng thời:

- `CommonSchema`: các field xuất hiện ở đa số doanh nghiệp phi tài chính, ví dụ
  doanh thu, lợi nhuận sau thuế, tổng tài sản, nợ phải trả, vốn chủ sở hữu, hàng
  tồn kho và dòng tiền từ hoạt động kinh doanh.
- `IndustrySchema`: các field bổ sung có ý nghĩa trong một ngành. Ví dụ, bán lẻ
  có thể thêm số cửa hàng; bất động sản thêm tồn kho dự án và người mua trả
  tiền trước; ngân hàng sẽ là schema chuyên biệt trong giai đoạn sau.

Trong tài liệu này:

- *Field* là trường trong JSON/data model.
- *Khoản mục báo cáo tài chính* (*financial statement line item*) là mục kế
  toán nguồn, ví dụ doanh thu hoặc tổng tài sản.
- *Chỉ số tài chính* (*financial metric*) là giá trị được tính, ví dụ tăng
  trưởng doanh thu, biên lợi nhuận gộp, ROA hoặc nợ trên vốn chủ.
- Các khái niệm trên không đồng nghĩa với KPI vận hành/kinh doanh.

### 3.5. Extractor theo schema và chuẩn hóa

Extractor dùng schema đã chọn như danh sách mục tiêu và hợp đồng kiểm tra dữ
liệu: tìm khoản mục nguồn, map nhãn nguồn sang field chuẩn, chuẩn hóa ngày,
đơn vị, tiền tệ, phạm vi hợp nhất và gắn bằng chứng.

Mỗi giá trị trích xuất theo nguyên tắc evidence-first:

```json
{
  "field": "revenue",
  "source_label": "Doanh thu thuần về bán hàng và cung cấp dịch vụ",
  "value": 61824000000000,
  "currency": "VND",
  "period": "2024",
  "consolidation_scope": "consolidated",
  "citation": {
    "document_id": "VNM_2024_audited_fs",
    "page": 14,
    "table": "Báo cáo kết quả hoạt động kinh doanh"
  }
}
```

Không được bỏ tài liệu/bảng/văn bản gốc. Field chuẩn hóa giúp truy vấn và so
sánh chính xác; dữ liệu thô vẫn là bằng chứng cuối cùng.

## 4. Financial Analysis Agent (trọng tâm MVP)

```text
Câu hỏi người dùng
  -> nhận diện ý định và mức độ hiểu biết tài chính
  -> lập kế hoạch phân tích
  -> RAG: truy xuất bằng chứng định tính trong báo cáo
  -> truy vấn dữ liệu tài chính đã chuẩn hóa
  -> gọi calculator cho chỉ số và so sánh xác định
  -> verifier kiểm tra công ty, kỳ, đơn vị, phạm vi báo cáo, nguồn và phép tính
  -> sinh câu trả lời dễ hiểu, có citation và giới hạn/cảnh báo
```

### 4.1. Nhận diện ý định và trình độ người dùng

Agent nhận diện người dùng đang hỏi tra cứu trực tiếp, so sánh, tính toán, giải
thích biến động hay tổng hợp rủi ro. Cách diễn đạt được điều chỉnh theo trình
độ: người mới nhận định nghĩa ngắn của thuật ngữ; người dùng nâng cao có thể
yêu cầu công thức và số liệu nguồn.

### 4.2. Analysis planner

Planner phân rã câu hỏi thành bằng chứng cần tìm và công cụ cần gọi. Ví dụ:

```text
"Doanh thu và lợi nhuận FPT năm 2024 thay đổi thế nào, và vì sao?"
  1. Lấy field revenue và net profit năm 2023, 2024.
  2. Kiểm tra công ty, kỳ báo cáo, đơn vị và phạm vi hợp nhất tương thích.
  3. Tính tăng trưởng theo năm.
  4. Truy xuất phần giải trình/ghi chú nói về nguyên nhân biến động.
  5. Sinh giải thích trung lập kèm citation.
```

### 4.3. RAG cho bằng chứng định tính

RAG tìm kiếm trong corpus báo cáo có nhận biết trang/bảng để lấy giải trình
biến động, rủi ro, kế hoạch kinh doanh và thuyết minh. Bằng chứng RAG phục vụ
giải thích; không nên là nguồn duy nhất cho con số nếu field chuẩn hóa đã có.

### 4.4. Truy vấn dữ liệu có cấu trúc

Agent truy vấn field chuẩn hóa cho câu hỏi định lượng. Truy vấn hợp lệ phải xác
định hoặc suy luận được doanh nghiệp, kỳ, loại báo cáo, đơn vị/tiền tệ và phạm
vi hợp nhất. Khi mơ hồ, agent cần hỏi lại hoặc nêu giả định, thay vì trộn số liệu
khác kỳ hay khác phạm vi.

### 4.5. Deterministic calculator

Calculator, thay vì LLM, thực hiện phép tính. Các chỉ số ban đầu của MVP có thể
gồm:

- Tăng trưởng theo năm.
- Biên lợi nhuận gộp, ròng và biên dòng tiền hoạt động khi đủ field.
- Nợ trên vốn chủ sở hữu.
- Hệ số thanh toán hiện hành khi đủ field.
- ROA và ROE, với công thức và quy ước lấy bình quân được nêu rõ.
- So sánh doanh nghiệp cùng ngành, chỉ khi kỳ và định nghĩa tương thích.

Mỗi kết quả tính phải lưu công thức, ID các field đầu vào, giá trị đầu vào và
kết quả để tái lập.

### 4.6. Verifier

Trước khi hiển thị câu trả lời, verifier kiểm tra:

- Bằng chứng thuộc đúng doanh nghiệp/pháp nhân được hỏi.
- Các giá trị so sánh cùng kỳ và cùng phạm vi báo cáo phù hợp.
- Đơn vị và quy mô tiền tệ khớp nhau.
- Có citation cho các khẳng định thực tế quan trọng.
- Kết quả calculator khớp với đầu vào và công thức đã lưu.
- Agent không trình bày suy luận như một sự thật được báo cáo nêu ra.

Nếu thiếu hoặc mâu thuẫn bằng chứng, agent phải nói rõ thay vì bịa giá trị hay
kết luận.

### 4.7. Sinh câu trả lời và giao diện

Câu trả lời gồm kết luận trực tiếp, số liệu chính, phép tính nếu có, giải thích
cho người mới, citation và giới hạn/cảnh báo trung lập. Giao diện cần cho phép
người dùng mở citation để xem đúng tài liệu/trang/bảng nguồn.

## 5. Ví dụ truy vấn đầu-cuối

```text
Câu hỏi:
"Doanh thu và lợi nhuận của [company] năm 2024 thay đổi thế nào so với 2023,
và báo cáo giải thích nguyên nhân gì?"

Kế hoạch agent:
1. Truy vấn revenue và net profit chuẩn hóa của 2023, 2024.
2. Xác minh cả hai thuộc báo cáo hợp nhất tương thích và cùng đơn vị.
3. Gọi calculator tính tỷ lệ tăng trưởng.
4. Dùng RAG lấy giải trình của ban lãnh đạo và thuyết minh liên quan.
5. Kiểm tra citation; phân biệt câu báo cáo nêu với diễn giải của agent.
6. Trả lời ngắn gọn, có nguồn; nêu rõ nếu báo cáo không giải thích nguyên nhân.
```

## 6. Kế hoạch đánh giá

Đối tượng đánh giá là agent, không phải độ phủ dataset hay crawler. Tạo một bộ test nhỏ
được rà soát thủ công, gồm câu hỏi tra cứu, tính toán, so sánh, giải thích và
tổng hợp rủi ro.

So sánh tối thiểu:

1. Text-only RAG.
2. RAG + calculator.
3. Agent đầy đủ: RAG + structured-data query + calculator + verifier.

Các thước đo:

- Độ chính xác trích xuất số liệu.
- Độ chính xác số học/chỉ số tính toán.
- Độ đúng và đầy đủ của citation.
- Độ đúng ngữ cảnh: doanh nghiệp, kỳ, đơn vị và phạm vi hợp nhất.
- Faithfulness: không có khẳng định không được bằng chứng hỗ trợ.
- Mức hữu ích và dễ hiểu với người dùng ít kinh nghiệm, dùng rubric rõ ràng
  hoặc một khảo sát người dùng quy mô nhỏ.

## 7. Ranh giới MVP và quyết định để ngỏ

Ranh giới ban đầu:

- Một nhóm nhỏ, cố định các doanh nghiệp niêm yết Việt Nam có báo cáo công khai.
- Bắt đầu với doanh nghiệp phi tài chính và một `IndustrySchema` được chọn.
- `CommonSchema` giới hạn và một số ít chỉ số tài chính.
- Báo cáo tiếng Việt trước; vẫn giữ nhãn tiếng Anh nếu xuất hiện trong tài liệu.
- Dataset được chuẩn bị và đóng băng phiên bản trước khi đánh giá để kết quả
  tái lập được.

Các quyết định để các phiên sau chốt dần:

- Danh sách doanh nghiệp, ngành, năm báo cáo và số lượng tài liệu.
- Công cụ parser/OCR/table extraction.
- LLM, embedding model, vector store và framework điều phối agent.
- Từ vựng schema chi tiết và công thức từng metric.
- Bộ câu hỏi ground truth và quy trình đánh giá.
- Crawler định kỳ từ HOSE/HNX/UPCoM và trang IR doanh nghiệp. Đây là hạng mục
  mở rộng sau khi MVP agent chạy ổn, không thuộc MVP hiện tại.
- Có thêm search sub-agent cho câu hỏi ngoài corpus cục bộ hay không. Nếu có,
  mọi dữ liệu ngoài báo cáo phải được gắn nhãn tách biệt với bằng chứng từ báo
  cáo.
