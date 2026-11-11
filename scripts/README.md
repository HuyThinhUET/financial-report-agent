# Crawler báo cáo tài chính

`crawl_reports.py` là crawler khám phá và tải PDF từ các trang Quan hệ nhà đầu
tư (IR) công khai mà người dùng khai báo rõ trong file cấu hình. Công cụ này
phù hợp để khảo sát dữ liệu ban đầu; nó chưa phải crawler toàn bộ HOSE/HNX/UPCoM.

## Nguyên tắc

- Chỉ crawl URL công bố thông tin hoặc trang IR công khai trong cấu hình.
- Mặc định tôn trọng `robots.txt`, chỉ tải liên kết cùng domain, và chờ tối
  thiểu một giây giữa các yêu cầu.
- Không vượt CAPTCHA, đăng nhập, paywall hay cơ chế chống truy cập của website.
- Manifest lưu URL nguồn, URL trang phát hiện, hash SHA-256 và trạng thái tải.

## Chạy

Yêu cầu Python 3.11+; crawler chỉ dùng thư viện chuẩn, không cần cài package.
Nếu Python từ chối chứng chỉ TLS của một nguồn nhưng Windows vẫn xác thực được
nguồn đó, crawler tự động thử `curl.exe` với kiểm tra TLS mặc định. Nó không tắt
xác thực chứng chỉ.

`config/report_sources.json` gồm các trang báo cáo thường niên của FPT,
Digiworld và SAM Holdings. Nguồn Digiworld khai báo từng trang theo năm; nguồn
SAM là trang tổng hợp và có thể có cả bản tiếng Việt lẫn tiếng Anh.
Digiworld phân phối sản phẩm công nghệ; SAM là tập đoàn đa ngành. Nhãn
`technology` ở đây là nhóm khảo sát, không khẳng định cùng phân ngành chính thức.
Nguồn Digiworld dùng `ajax: true` để yêu cầu đúng phần HTML do trang tải động.

Không cần sửa config ở mỗi lần chạy. File này đồng thời là **registry**: khai
báo nguồn một lần, rồi chọn theo mã/tên doanh nghiệp hoặc ngành.

```powershell
# Xem các doanh nghiệp và ngành hiện có trong registry.
python scripts/crawl_reports.py --list-sources

# Crawl một doanh nghiệp theo mã hoặc tên (hỗ trợ tên Việt có/không dấu).
python scripts/crawl_reports.py --company FPT --dry-run
python scripts/crawl_reports.py --company "Công ty Cổ phần FPT"

# Crawl tất cả doanh nghiệp đã đăng ký thuộc ngành đó.
python scripts/crawl_reports.py --industry technology --output data/annual-reports --dry-run
```

Khi bổ sung một doanh nghiệp mới, chỉ thêm một entry vào registry; mọi lần chạy
sau chỉ dùng `--company` hoặc `--industry`. `--industry` chỉ crawl các doanh
nghiệp đã có URL IR được kiểm chứng trong registry, không tự đoán website từ
tên công ty để tránh tải nhầm nguồn không chính thức.

Khảo sát an toàn trước:

```powershell
python scripts/crawl_reports.py `
  --config config/report_sources.json `
  --output data/annual-reports `
  --dry-run
```

Để thêm/tự thử nguồn khác mà không ghi đè cấu hình FPT sẵn có:

```powershell
Copy-Item config/report_sources.example.json config/report_sources.local.json
# Sửa config/report_sources.local.json: thay URL mẫu bằng trang IR chính thức.

python scripts/crawl_reports.py `
  --config config/report_sources.local.json `
  --output data/annual-reports `
  --dry-run
```

Sau khi kiểm tra các URL được phát hiện, bỏ `--dry-run` để tải PDF:

```powershell
python scripts/crawl_reports.py `
  --config config/report_sources.local.json `
  --output data/annual-reports
```

Kết quả:

```text
data/annual-reports/<industry>/<ticker>/
  manifest.jsonl
  pdf/<ticker>_<year>_<source-name>.pdf
```

`manifest.jsonl` là một JSON object trên mỗi dòng. Trường `status` có thể là
`dry_run`, `downloaded`, `skipped_existing` hoặc `failed`. Crawler thêm record
ngay sau mỗi URL, nên vẫn giữ tiến độ nếu một lần chạy bị ngắt.
Để tải bộ báo cáo thường niên đã cấu hình, chạy:
`python scripts/crawl_reports.py --industry technology --output data/annual-reports`.

## Cấu hình nguồn

Mỗi nguồn cần một trang IR hiển thị liên kết trực tiếp tới PDF và danh sách
domain được phép. Không đặt domain quá rộng nếu không cần thiết.

```json
{
  "company_code": "ABC",
  "company_name": "Công ty cổ phần ABC",
  "exchange": "HOSE",
  "ir_url": "https://ir.example.vn/bao-cao-tai-chinh",
  "allowed_domains": ["ir.example.vn", "static.example.vn"]
}
```

Nếu một website tải danh sách báo cáo qua JavaScript hoặc không công khai PDF
trực tiếp, hãy ghi lại đây như một nguồn cần adapter riêng.
