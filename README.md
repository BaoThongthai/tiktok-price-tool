# TikTok Price Tool — Link cố định

**Website dùng mỗi ngày: https://baothongthai.github.io/tiktok-price-tool/**

Giao diện đăng nhập, nhập link, lấy giá và xuất CSV đều ở địa chỉ GitHub Pages này. Một máy Windows giữ ứng dụng server, Chrome và tab nội bộ hoạt động để xử lý. Không nhập hoặc sao chép link tunnel mỗi lần dùng.

## Cài máy treo một lần

1. Tải `TikTokPriceTool_Server.zip`, giải nén vào thư mục cố định.
2. Mở đúng Chrome/profile đã đăng nhập TikTok. Vào `chrome://extensions` và tải tiện ích từ thư mục `extension`.
3. Chạy `TikTokPriceServer.exe`. Lần đầu đặt mật khẩu cho tài khoản `admin` nếu chưa có cấu hình riêng.
4. Lần đầu nhập GitHub Fine-grained personal access token, chỉ chọn repository `BaoThongthai/tiktok-price-tool`, quyền **Contents: Read and write**. Nhập token trực tiếp trên máy treo, không gửi qua chat hoặc đưa vào repository.
5. Ứng dụng lưu cấu hình riêng trong `settings.private.json` cạnh EXE. Mật khẩu lưu dạng mã băm; GitHub token lưu trong file riêng này để cập nhật kết nối lúc khởi động. Không tải file đó lên GitHub hoặc chia sẻ công khai.
6. Giữ tab `127.0.0.1` do ứng dụng mở trong Chrome có tiện ích. Đợi báo Chrome đã kết nối.
7. Ứng dụng mở đường kết nối HTTPS và tự cập nhật `connection.json` trên GitHub. File đó chỉ chứa địa chỉ kết nối, không chứa mật khẩu/token GitHub. Nếu cập nhật chưa hiện ngay, chờ khoảng một phút rồi đăng nhập lại website.

## Mỗi ngày

Mở ứng dụng server và Chrome trên máy treo, giữ tab nội bộ mở. Trên máy/điện thoại khác, vào link GitHub Pages cố định và đăng nhập `admin` cùng mật khẩu đã đặt. Nhập các link, mỗi dòng một link, bấm Lấy giá tất cả link và Xuất CSV.

Đóng ứng dụng trên máy treo sẽ ngắt xử lý; link GitHub Pages vẫn giữ nguyên nhưng báo không kết nối được server. Sau khi ứng dụng chạy lại, đăng nhập lại website để lấy kết nối mới. Máy treo cần được đặt không ngủ khi cắm điện. GitHub Pages không tự chạy Chrome hoặc mã Python.

## Dữ liệu được lấy

Tool tìm toàn bộ link trong **Khám phá thêm sản phẩm từ / Explore more from / Discover more from**, sau đó mở từng link và đọc tên sản phẩm, giá gạch ngang và giá hiện tại ở đầu trang chi tiết. Không đổi phân loại mặc định, không bấm mua, không dùng giá thẻ ngoài làm dự phòng. Bảng bổ sung cột Shop để phân biệt nguồn.

Không đọc được giá, chỉ hiển thị khoảng giá hoặc bị xác minh thì báo lỗi riêng. Nếu TikTok yêu cầu CAPTCHA, tự hoàn tất trong tab TikTok trên máy treo; tool chờ tối đa 3 phút cho mỗi trang. Giá phụ thuộc thời điểm, tài khoản và phiên duyệt, chưa bao gồm điều kiện chỉ xuất hiện ở bước thanh toán.

## Mã nguồn

- `server.py`, `ui.html`: ứng dụng cục bộ và hàng đợi.
- `public_server.py`: server cho giao diện GitHub Pages, có mật khẩu và cập nhật kết nối; các endpoint cầu nối chỉ phục vụ trên máy treo, không mở qua tunnel.
- `manifest.json`, `background.js`, `connect.js`, `scanner.js`: tiện ích Chrome. Các file nguồn được đặt ở gốc repository để dễ tải qua GitHub; có thể chọn thư mục gốc làm tiện ích, hoặc dùng thư mục `extension` trong ZIP.
- `test_backend.py`, `test_detail.js`, `test_public.py`: kiểm tra hàng đợi, lấy giá chi tiết, xác thực và cách ly cầu nối.

Chạy nguồn cần Python 3.12 và Chrome: `python server.py` hoặc `python public_server.py`. Khi chạy nguồn, cần đặt `manifest.json` và ba file JS cạnh nhau rồi tải thư mục đó làm tiện ích.

## Riêng tư và kiểm tra

Không sao chép cookie, mật khẩu hoặc thư mục profile Chrome. Mật khẩu public chỉ giữ dạng mã băm trong bộ nhớ của phiên, không lưu trong mã nguồn. Dữ liệu đi qua Cloudflare khi dùng chế độ public; người có link và mật khẩu có thể xem kết quả và gửi tác vụ lấy giá. Không chia sẻ mật khẩu hoặc `LINK_PUBLIC.txt` công khai.

Ngày 24/11/2026 đã xác minh bộ chọn giá trên đủ 9 trang chi tiết của link mẫu; đã kiểm tra luồng hàng đợi, CSV, lấy giá chi tiết, từ chối khoảng giá và trang cũ. Chế độ public cần chạy thực tế trên máy treo để xác minh kết nối từ Internet. GitHub chứa mã nguồn và gói tải; việc đưa repository lên GitHub không tự biến máy treo thành dịch vụ online.
