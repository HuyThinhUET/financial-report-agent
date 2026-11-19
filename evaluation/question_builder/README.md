# Question builder

Chạy `python evaluation/question_builder/build.py data/data_evaluate/058_ELC_2026_1` (có thể truyền nhiều thư mục). Duyệt đệ quy các insights.json; mỗi insight nhận một câu hỏi. Kết quả lưu cạnh nguồn trong questions.json, còn questions_metrics.json ghi thời gian, token usage do Codex báo và lỗi nếu có. Mặc định dùng Codex CLI model gpt-6-luna, reasoning medium; có thể đổi bằng --model. Cần Codex CLI đã đăng nhập và có quyền dùng model. Kiểm tra kết quả trước khi sử dụng; câu hỏi sinh tự động không đảm bảo bao phủ hoàn toàn insight.
