# Courscape

[🇺🇸 Read the English documentation](README.md)

## Yêu cầu

- Python 3.8 trở lên
- Một trong các trình duyệt sau:
  - Google Chrome
  - Chromium
  - Firefox
- Các gói Python (cài đặt bằng `pip install -r requirements.txt`):

  ```
  loguru==0.7.3
  pybrowsers==0.6.0
  python-dotenv==1.0.1
  selenium==4.28.1
  webdriver-manager==4.0.2
  ```

## Cách sử dụng

1. Clone repository:

   ```bash
   git clone https://github.com/yourusername/courscape.git
   cd courscape
   ```

2. Cài đặt các thư viện cần thiết:

   ```bash
   pip install -r requirements.txt
   ```

3. Thiết lập ban đầu:
   - Sao chép `.env.example` và đổi tên thành `.env`
   - Chỉnh sửa `.env` để thiết lập tùy chọn (thông tin đăng nhập là không bắt buộc, nếu để trống bạn sẽ đăng nhập thủ công):

     ```bash
     # Lựa chọn trình duyệt
     DEFAULT_BROWSER=chrome  # hoặc firefox/chromium
     
     # Không bắt buộc: Thông tin đăng nhập tự động
     ACCOUNT_EMAIL=your.email@example.com
     ACCOUNT_PASSWORD=your_password
     ```

   - Chỉ định courses và specializations trong `.env` (không bắt buộc):

     ```bash
     # Courses và specializations cần xử lý
     COURSES=course1-slug,course2-slug
     SPECS=spec1-slug,spec2-slug
     ```

4. Chạy công cụ:

   ```bash
   # Xử lý course (nếu có nhiều course, phân cách bằng dấu phẩy)
   python main.py --course course-slug

   # Xử lý specialization (nếu có nhiều specialization, phân cách bằng dấu phẩy)
   python main.py --spec specialization-slug

   # Nếu muốn đăng nhập thủ công
   python main.py --course course-slug --manual-login
   
   # Đọc course/specialization từ tệp cấu hình (chỉ khi được chỉ định trong .env, dùng tùy chọn này thì không cần --course và --spec nữa)
   python main.py --from-config
   ```

## Các tùy chọn command line

- `--course`, `-c`: Slug của course cần xử lý (phân cách bằng dấu phẩy)
- `--spec`, `-s`: Slug của specialization cần xử lý (phân cách bằng dấu phẩy)
- `--manual-login`, `-m`: Bắt buộc đăng nhập thủ công
- `--from-config`, `-f`: Đọc course/specialization hóa từ tệp cấu hình. Để sử dụng tùy chọn này, hãy chỉ định course và specialization trong tệp `.env`. Tùy chọn này sẽ bỏ qua các tùy chọn `--course` và `--spec`.

## Lấy Slug của course/specialization

Slug là định danh duy nhất trong URL của trang:

- Đối với course: `https://www.course.org/learn/[course-slug]` (chỉ lấy phần `[course-slug]`)
- Đối với specialization: `https://www.course.org/specializations/[specialization-slug]` (chỉ lấy phần `[specialization-slug]`)

## Credit

Cảm ơn [skipera](https://github.com/serv0id/skipera) là nguồn cảm hứng cho dự án này.
