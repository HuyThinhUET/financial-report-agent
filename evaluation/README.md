# Trích xuất insight BCTC hợp nhất bằng Codex CLI

Dữ liệu gốc nằm trong `data/data_raw/`; insight và log nằm trong `data/data_evaluate/`. Bộ dữ liệu lịch sử nằm trong `data/data-evaluation từ đầu đỏ/`.

Chạy các lệnh từ thư mục gốc dự án; cần Python 3.10+, Codex CLI đã đăng nhập và công cụ đọc PDF của môi trường Codex (ví dụ PyMuPDF). Mỗi báo cáo khởi chạy một tiến trình `codex exec --ephemeral` riêng, không tiếp tục phiên trước. PDF được gửi cho nhà cung cấp model theo cấu hình Codex và có thể phát sinh chi phí.

Xem 20 lệnh cụ thể tại [PREPARED_COMMANDS.md](insights_builder/PREPARED_COMMANDS.md).

Danh sách bổ sung 50 báo cáo nằm tại [prepared_statements_additional_50.json](insights_builder/prepared_statements_additional_50.json), tách khỏi danh sách 20 báo cáo ban đầu. Kỳ dự kiến được lấy từ nhãn hoặc tên tệp nguồn, bao gồm các báo cáo ELC từ nhiều năm; cần đối chiếu công ty, phạm vi hợp nhất và kỳ trong chính PDF khi trích xuất. Xem trước hoặc chạy tuần tự:

```powershell
python -m evaluation.insights_builder --manifest evaluation/insights_builder/prepared_statements_additional_50.json --list
python -m evaluation.insights_builder --manifest evaluation/insights_builder/prepared_statements_additional_50.json --max_sample 50
```

Các thư mục kết quả đã có cùng công ty/kỳ vẫn bị bỏ qua, kể cả khi lần chạy trước thất bại. Có thể thêm `--codex` nếu CLI không nằm trên PATH. Ví dụ lệnh cho một báo cáo:

```powershell
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_nam/PLX_5570d8cdb64de8f7.pdf' --company PLX --year 2025
python -m evaluation.insights_builder --pdf 'data/data_raw/5-linh-vuc/dau_khi_khoang_san/hop_nhat_quy/PLX_925339daf7038fe2.pdf' --company PLX --year 2026 --quarter 2
```

Chạy tuần tự tối đa 20 báo cáo chưa có thư mục trong danh sách chuẩn bị, hoặc toàn bộ danh sách nếu bỏ `--max_sample`:

```powershell
python -m evaluation.insights_builder --manifest evaluation/insights_builder/prepared_statements.json --max_sample 20
```

Duyệt các manifest có tên `manifest.json` trong `data`, lấy PDF nằm trực tiếp trong thư mục `hop_nhat_nam` hoặc `hop_nhat_quy` và có nhãn nguồn xác định được năm/quý. Dùng `--list` để xem trước; không có manifest hoặc nhãn kỳ không rõ thì không tự suy đoán, chạy riêng bằng `--pdf` với kỳ đã kiểm tra hoặc thêm vào manifest chuẩn bị. Không dùng tên ngày công bố làm năm tài chính. Năm/quý của năm tài chính lệch năm dương lịch cần kiểm tra thủ công.

```powershell
python -m evaluation.insights_builder --list
python -m evaluation.insights_builder --max_sample 20
python -m evaluation.insights_builder
```

`--max_sample` đếm số báo cáo được thử sau khi bỏ qua báo cáo đã có thư mục; lỗi vẫn tính vào số lần thử. Có thể thêm `--model TEN_MODEL` nếu CLI hỗ trợ. Manifest chuẩn bị có dạng `{"reports": [{"pdf": "data/.../hop_nhat_quy/file.pdf", "company": "FPT", "year": 2024, "quarter": 2}]}`; báo cáo năm dùng `quarter: null`. Các nhãn dự kiến phải được đối chiếu với PDF trong phiên trích xuất.

Nếu PowerShell báo không tìm thấy `codex` trên PATH, có thể truyền đường dẫn Codex CLI bằng `--codex 'C:\duong-dan\codex.exe'`. Kiểm tra trước bằng `& 'C:\duong-dan\codex.exe' --version`. Một số bản cài extension VS Code có `codex.exe` trong thư mục extension; đường dẫn có thể đổi sau khi cập nhật. Nếu chưa có CLI, cài Codex CLI và đăng nhập trước khi chạy. Trong PowerShell, đặt toàn bộ lệnh trên một dòng; `\` không phải ký tự nối dòng PowerShell.

Kết quả nằm tại `data/data_evaluate/STT_MACONGTY_NAM[_QUY]`: `insights.json`, `run_config.json`, `metrics.json`, `events.jsonl`, `stderr.log`. STT tự tăng theo thư mục hiện có. Không chạy song song nhiều tiến trình vì cấp STT chưa có khóa. Nếu đã có thư mục cùng công ty/kỳ thì bỏ qua, kể cả thất bại hoặc có PDF khác cùng kỳ; kiểm tra và di chuyển thư mục cũ khi muốn chạy lại. Không ghi đè kết quả. Các thư mục cũ được bảo toàn.

`insights.json` là bản dự thảo, dẫn trang PDF và cần chuyên gia kiểm tra. Nếu PDF không đọc được hoặc nhãn không khớp, mô hình phải ghi giới hạn và không tạo insight; một danh sách rỗng được đánh dấu thất bại để kiểm tra. Script chỉ kiểm tra JSON, danh sách không rỗng và hash PDF, **không tự xác minh trích dẫn, phép tính, phạm vi hay độ bao phủ**. `metrics.json` ghi trạng thái, mã thoát, thread ID và token nếu CLI cung cấp. Nếu thất bại, xem log; không dùng thư mục lỗi như kết quả hoàn chỉnh.

Script cũng kiểm tra dấu hiệu mất mã tiếng Việt và đánh dấu lỗi nếu phát hiện, nhưng đây là kiểm tra gần đúng, không đảm bảo phát hiện mọi trường hợp. Nếu `insights.json` có nhiều dấu `?` thay chữ tiếng Việt, kiểm tra cả `events.jsonl`; không dùng dữ liệu lỗi để đánh giá.

Danh sách nhóm và các quy tắc về kỳ quý, lũy kế, dấu và đơn vị nằm trong [prompt mặc định](insights_builder/financial_statement_prompt.txt). [FEATURES.md](insights_builder/FEATURES.md) tổng hợp 5 bài nhóm và handout, kèm công thức, trang nguồn và lưu ý kiểm chứng; prompt mặc định đã cụ thể hóa các nhóm chỉ tiêu và insight từ những mẫu này. Các bài mẫu là nguồn gợi ý, không phải nhãn chuẩn đã được chuyên gia xác nhận. Bộ dữ liệu lịch sử không thuộc luồng chạy mặc định.

Khi tạo bộ đánh giá, khóa danh sách tài liệu và chia tập theo doanh nghiệp trước khi điều chỉnh prompt hoặc chấm điểm; cân nhắc xếp các công ty có liên quan vào cùng nhóm để giảm rò rỉ. Không coi từ khóa, lớp chữ OCR hay việc khớp trích dẫn tự động là bằng chứng đã kiểm tra đúng kỳ, phạm vi và bố cục bảng. Hash trong `run_config.json` ghi lại phiên bản PDF lúc chạy; script chưa so sánh hash với một manifest đã khóa trước đó.
