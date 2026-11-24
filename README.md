# TikTok Price Tool

Tool Windows dùng Chrome đang mở để lấy **giá trong từng trang sản phẩm**, giữ phân loại mặc định và xuất CSV mở bằng Excel.

## Tải và chạy

Tải gói `TikTokPriceTool_Public.zip` trong repository này và giải nén toàn bộ. Gói gồm:

- `TikTokPriceTool.exe`: dùng ngay trên máy.
- `TikTokPricePublic.exe`: tạo link HTTPS để truy cập từ Internet.
- Thư mục `extension`: tiện ích cầu nối với Chrome của bạn.

Trong đúng profile Chrome cần dùng, mở `chrome://extensions`, bật chế độ nhà phát triển, chọn **Tải tiện ích đã giải nén** và chọn thư mục `extension`.

## Truy cập qua Internet bằng máy treo

1. Mở Chrome/profile đã cài tiện ích.
2. Chạy `TikTokPricePublic.exe`, đặt mật khẩu truy cập, nhập lại để xác nhận.
3. Giữ tab nội bộ `127.0.0.1` do tool mở trong đúng Chrome đó. Nếu mở nhầm profile, sao chép địa chỉ sang profile đã cài tiện ích.
4. Chờ **Kết nối Chrome: Đã kết nối**.
5. Ứng dụng tải `cloudflared` từ kho chính thức Cloudflare, rồi in link HTTPS public. Link cũng nằm trong `LINK_PUBLIC.txt` cạnh EXE.
6. Truy cập link từ máy/điện thoại khác, đăng nhập bằng tài khoản `admin` và mật khẩu vừa đặt.
7. Nhập link, lấy giá và xuất CSV. Chrome trên máy treo sẽ mở lần lượt các sản phẩm để xử lý.

Giữ máy treo, ứng dụng, Chrome và tab nội bộ hoạt động. Đóng ứng dụng sẽ ngắt link public. Quick Tunnel tạo địa chỉ mới sau mỗi lần chạy; chưa phải tên miền cố định hoặc dịch vụ có cam kết uptime. Để dùng lâu dài với tên miền cố định cần cấu hình Named Tunnel riêng.

## Dữ liệu được lấy

Tool tìm toàn bộ link trong **Khám phá thêm sản phẩm từ / Explore more from / Discover more from**, sau đó mở từng link và đọc tên sản phẩm, giá gạch ngang và giá hiện tại ở đầu trang chi tiết. Không đổi phân loại mặc định, không bấm mua, không dùng giá thẻ ngoài làm dự phòng. Bảng bổ sung cột Shop để phân biệt nguồn.

Không đọc được giá, chỉ hiển thị khoảng giá hoặc bị xác minh thì báo lỗi riêng. Nếu TikTok yêu cầu CAPTCHA, tự hoàn tất trong tab TikTok trên máy treo; tool chờ tối đa 3 phút cho mỗi trang. Giá phụ thuộc thời điểm, tài khoản và phiên duyệt, chưa bao gồm điều kiện chỉ xuất hiện ở bước thanh toán.

## Mã nguồn

- `server.py`, `ui.html`: ứng dụng cục bộ và hàng đợi.
- `public_server.py`: giao diện public có mật khẩu; các endpoint cầu nối chỉ phục vụ trên máy treo, không mở qua tunnel.
- `manifest.json`, `background.js`, `connect.js`, `scanner.js`: tiện ích Chrome. Các file nguồn được đặt ở gốc repository để dễ tải qua GitHub; có thể chọn thư mục gốc làm tiện ích, hoặc dùng thư mục `extension` trong ZIP.
- `test_backend.py`, `test_detail.js`, `test_public.py`: kiểm tra hàng đợi, lấy giá chi tiết, xác thực và cách ly cầu nối.

Chạy nguồn cần Python 3.12 và Chrome: `python server.py` hoặc `python public_server.py`. Khi chạy nguồn, cần đặt `manifest.json` và ba file JS cạnh nhau rồi tải thư mục đó làm tiện ích.

## Riêng tư và kiểm tra

Không sao chép cookie, mật khẩu hoặc thư mục profile Chrome. Mật khẩu public chỉ giữ dạng mã băm trong bộ nhớ của phiên, không lưu trong mã nguồn. Dữ liệu đi qua Cloudflare khi dùng chế độ public; người có link và mật khẩu có thể xem kết quả và gửi tác vụ lấy giá. Không chia sẻ mật khẩu hoặc `LINK_PUBLIC.txt` công khai.

Ngày 24/11/2026 đã xác minh bộ chọn giá trên đủ 9 trang chi tiết của link mẫu; đã kiểm tra luồng hàng đợi, CSV, lấy giá chi tiết, từ chối khoảng giá và trang cũ. Chế độ public cần chạy thực tế trên máy treo để xác minh kết nối từ Internet. GitHub chứa mã nguồn và gói tải; việc đưa repository lên GitHub không tự biến máy treo thành dịch vụ online.
