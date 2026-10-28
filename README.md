# Career Connect — Website kết nối doanh nghiệp với sinh viên

> **Tài liệu triển khai cho nhóm/AI coding assistant.** Đọc `README.md`, sau đó đọc `docs/API_CONTRACT.md` và `docs/SEARCH_UI_SPEC.md` trước khi sửa code. Contract mô tả **đích cần đạt**; bảng kiểm kê bên dưới nói rõ phần nào đã có trong starter và phần nào còn phải làm. Không được coi endpoint có tên trong contract là đã chạy nếu code chưa triển khai và test.

## 1. Mục tiêu và phạm vi MVP

Career Connect giúp khách truy cập/sinh viên tìm việc và thực tập, giúp doanh nghiệp đăng tuyển và quản lý ứng viên, đồng thời cho phép staff duyệt doanh nghiệp/tin và quản lý nội dung hướng nghiệp.

**Luồng end-to-end bắt buộc:**

1. Doanh nghiệp đăng ký và hoàn thiện hồ sơ.
2. Admin/Moderator duyệt hồ sơ doanh nghiệp.
3. Doanh nghiệp tạo tin tuyển dụng.
4. Admin/Moderator duyệt tin.
5. Guest hoặc sinh viên tìm kiếm/lọc và xem tin đã duyệt.
6. Sinh viên đăng nhập và ứng tuyển; không được ứng tuyển trùng cùng một tin.
7. Doanh nghiệp tìm/lọc hồ sơ ứng viên và cập nhật trạng thái đơn.
8. Sinh viên xem trạng thái mới.

Chỉ tin đang mở, đã duyệt, thuộc doanh nghiệp đã duyệt/đang hoạt động và chưa quá hạn mới xuất hiện ở tìm kiếm công khai.

## 2. Vai trò

- **Guest (khách chưa đăng nhập):** tìm kiếm/lọc việc làm, xem chi tiết tin, xem bài hướng nghiệp đã xuất bản. Muốn ứng tuyển phải đăng nhập/đăng ký student.
- **Student:** toàn bộ chức năng công khai; hồ sơ, CV, gợi ý theo hồ sơ, ứng tuyển, theo dõi/rút đơn và lưu bộ lọc trên trình duyệt.
- **Business:** hồ sơ doanh nghiệp; CRUD tin của chính mình; tìm/lọc tin của mình; tìm/lọc ứng viên thuộc tin của mình; cập nhật trạng thái đơn.
- **Moderator:** kiểm duyệt doanh nghiệp/tin; tìm/lọc hàng chờ và lịch sử kiểm duyệt; quản lý nội dung hướng nghiệp; xem danh mục.
- **Admin:** toàn bộ quyền Moderator, cộng quản lý tài khoản, vai trò, trạng thái tài khoản và CRUD danh mục.

Guest không phải giá trị `users.role`; Guest chỉ là người dùng chưa có phiên đăng nhập.

## 3. Yêu cầu giao diện bắt buộc

### 3.1. Trang tìm việc công khai (Guest + Student)

Giao diện phải lấy cảm hứng từ ảnh mẫu trong yêu cầu, có tối thiểu:

1. **Thanh tìm kiếm chính:** chọn danh mục nghề, nhập từ khóa/vị trí tuyển dụng, nhập địa điểm, nút Xóa và nút Tìm kiếm. Cho phép nhấn Enter để tìm; không mặc định khóa cứng địa điểm Hà Nội.
2. **Bảng gợi ý khi focus ô tìm kiếm:** hai khu vực khi màn hình đủ rộng: “Từ khóa phổ biến/gợi ý” và “Việc làm có thể bạn quan tâm”. Chọn từ khóa sẽ điền vào ô tìm kiếm; chọn tin sẽ mở chi tiết.
3. **Bộ lọc nâng cao:** danh mục nghề (chọn nhiều), loại công việc, ngành học phù hợp, địa điểm, lịch làm việc/thứ Bảy, thời gian đăng. Tất cả bộ lọc phải thực sự thay đổi truy vấn API, không chỉ đổi hình thức trên giao diện.
4. **Nút Xóa lọc:** xóa toàn bộ lựa chọn bộ lọc và tải lại kết quả không lọc.
5. **Nút Lưu bộ lọc:** bản MVP lưu bộ lọc ở `localStorage`; sau khi tải lại trang, bộ lọc đã lưu vẫn dùng được. Không cần API/database riêng cho chức năng này.
6. **Danh mục nghề phổ biến:** hiển thị danh mục và số tin đang công khai trong từng danh mục; số lượng phải lấy từ API/DB, không tự viết số giả.
7. **Danh sách kết quả:** tên vị trí, doanh nghiệp, địa điểm, loại công việc, danh mục, hạn ứng tuyển, mức lương (nếu doanh nghiệp cung cấp), trạng thái phù hợp và nút xem chi tiết.
8. **Gợi ý theo vai trò:** Guest thấy tin mới/được đề xuất công khai; Student đã đăng nhập có thể thấy gợi ý dựa trên ngành/kỹ năng từ `/api/students/me/recommendations`.
9. **Trạng thái giao diện:** đang tải, không có kết quả, lỗi API, xóa bộ lọc, màn hình nhỏ. Không dùng danh sách giả thay cho dữ liệu backend.

### 3.2. Tìm kiếm trong khu vực có đăng nhập

Không tạo một thanh tìm kiếm chung vô nghĩa cho mọi trang. Tìm kiếm phải khớp loại dữ liệu mà vai trò đó quản lý:

- **Student — Đơn đã ứng tuyển:** tìm theo tên vị trí/doanh nghiệp; lọc trạng thái đơn.
- **Business — Tin của tôi:** từ khóa tiêu đề/mô tả, trạng thái tin, danh mục, địa điểm, loại công việc; sắp xếp mới nhất/hạn gần nhất.
- **Business — Ứng viên:** từ khóa tên/email/ngành/kỹ năng ứng viên; lọc theo tin tuyển dụng và trạng thái đơn; chỉ trong các tin thuộc doanh nghiệp đang đăng nhập.
- **Moderator — Kiểm duyệt:** tìm theo tên/email doanh nghiệp hoặc tiêu đề/tên doanh nghiệp của tin; lọc theo trạng thái nếu xem danh sách tất cả, và theo danh mục/địa điểm/loại công việc cho tin.
- **Admin — Tài khoản:** tìm theo email/tên sinh viên/tên doanh nghiệp; lọc role và trạng thái hoạt động.
- **Admin/Moderator — Danh mục/nội dung hướng nghiệp:** tìm theo tên/tiêu đề; lọc trạng thái và loại nội dung.

Profile form, trang đổi mật khẩu và trang chi tiết đơn không bắt buộc có thanh search vì bản thân chúng không phải danh sách dữ liệu.

Chi tiết tương tác nằm trong [`docs/SEARCH_UI_SPEC.md`](docs/SEARCH_UI_SPEC.md); endpoint, tham số, quyền và JSON nằm trong [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md).

## 4. Kiểm kê code starter — không được hiểu nhầm

| Khu vực | Đã có trong starter | Còn phải làm để đạt yêu cầu |
|---|---|---|
| App/DB | Flask factory, Blueprint, SQLite schema, health check | Kiểm tra migration khi thêm cột mới; seed tài khoản/dữ liệu demo |
| Auth | Register/login/logout/session, email, đổi mật khẩu, vô hiệu hóa; role guard | Giao diện đầy đủ; test toàn bộ luồng và quyền |
| Student | Đọc/sửa hồ sơ, CV CRUD, gợi ý rule-based, tạo/xem/sửa/rút đơn | Giao diện; search/filter đơn; tích hợp các trang; lưu bộ lọc ở browser |
| Job search | API `GET /api/jobs` hiện hỗ trợ `q`, `major`, `location`, `job_type`, `category_id`; chi tiết tin public | Thanh search và bộ lọc UI; danh mục public/count; keyword suggestions; lọc lịch thứ Bảy/ngày đăng; salary display; search UX; test query phối hợp |
| Business | Hồ sơ, CRUD tin, xem đơn của tin mình, detail và đổi trạng thái; danh sách tin/đơn hiện chỉ có bộ lọc hạn chế | UI; mở rộng tìm/lọc tin và ứng viên; kiểm tra quyền sở hữu |
| Admin/Moderator | Duyệt/từ chối, review history; user/category/content CRUD | UI; search/filter trên danh sách duyệt và các màn quản lý |
| Career content | API public đọc nội dung đã xuất bản; staff CRUD | UI public và admin; search/filter title/category/status |
| Search across roles | Một phần tìm kiếm public jobs đã có trong BE | Các API lọc phụ trợ và UI ở các khu vực còn thiếu; xem contract v2 |

**Quan trọng:** `app/templates/index.html` hiện chỉ là trang giới thiệu/health check, không phải giao diện Career Connect hoàn chỉnh. Backend có một số filter không có nghĩa là frontend đã có chức năng lọc.

## 5. Module và phân công cho 3 người

Chia theo **module nghiệp vụ**, mỗi người làm cả BE + FE trong phạm vi module của mình. Cả nhóm cùng chốt contract và schema trước; không chia cứng “một người toàn FE, một người toàn BE” trong dự án một tuần.

### TV1 — Public Discovery + Student Journey

**Phạm vi:** trang công khai cho Guest và khu vực Student.

- FE: thanh tìm việc theo mẫu, gợi ý từ khóa/tin, bộ lọc nâng cao, danh mục phổ biến, kết quả/chi tiết, hồ sơ student, CV, ứng tuyển, lịch sử đơn.
- BE: `GET /api/jobs*`, `GET /api/jobs/categories`, `GET /api/jobs/suggestions`, `/api/students/*`, `/api/applications/*`, `GET /api/career-contents*`.
- Search: q, category multi-select, location, job type, major/skills, Saturday policy, posting age; tìm/lọc đơn student.
- Test: khách không đăng nhập vẫn xem/tìm; chỉ student đăng nhập mới ứng tuyển; không đọc được đơn/CV người khác.

### TV2 — Business Recruitment Journey

**Phạm vi:** doanh nghiệp từ quản lý hồ sơ đến quản lý tin và ứng viên.

- FE: hồ sơ doanh nghiệp, danh sách/tạo/sửa/đóng tin, danh sách ứng viên, chi tiết ứng viên/đơn, cập nhật trạng thái.
- BE: `/api/company/*`.
- Search: tin của doanh nghiệp theo q/status/category/location/job type; ứng viên theo q/job/status.
- Test: không sửa tin của business khác; không xem ứng viên thuộc tin của business khác; sửa tin phải quay về pending để duyệt lại.

### TV3 — Platform + Staff/Admin + Integration

**Phạm vi:** nền tảng chung, quản trị và kiểm duyệt.

- BE: `/api/auth/*`, `/api/admin/*`, schema/migration/seed, role guards và cấu hình.
- FE: login/register, navigation dùng chung theo role, dashboard kiểm duyệt, tìm/lọc doanh nghiệp/tin chờ duyệt, lịch sử duyệt, quản lý user/category/content.
- Search: tên/email doanh nghiệp, title/tin, status/category/location cho hàng chờ; user theo email/tên/role/active; content theo title/category/status.
- Test/integration: không làm thay phần test của TV1/TV2; review pull request, chạy smoke tests, hướng dẫn chạy và chuẩn bị demo.

### Quy ước chia việc

- TV1 là owner của public job search UX; TV2 là owner của job/applicant management search; TV3 là owner của moderation/admin search.
- TV3 không được giữ toàn bộ kiểm thử: TV1/TV2 phải tự test module rồi mới bàn giao.
- Mỗi module phải tự có trang FE thật gọi API thật, loading/empty/error state, và ít nhất 1 ca thành công + 1 ca lỗi.
- Khi TV3 quá tải, TV1 có thể nhận trang nội dung hướng nghiệp public; TV2 có thể nhận một màn CRUD admin UI phụ sau khi luồng tuyển dụng của mình hoàn thành.

## 6. Thứ tự ưu tiên trong một tuần

- **P0 — bắt buộc:** auth/role, duyệt business/job, public job search/filter, job detail, apply, business xem ứng viên/cập nhật status, student theo dõi đơn, search/filter ở các danh sách quản trị cơ bản.
- **P1 — nên có, theo ảnh mẫu:** keyword suggestions, danh mục nổi bật + số lượng tin, saved filter localStorage, job recommendations, tìm/lọc nội dung hướng nghiệp, CV upload.
- **P2 — chỉ làm nếu P0/P1 ổn:** logo thật, autocomplete địa điểm, lọc lương nâng cao, gợi ý thống kê từ lịch sử tìm kiếm, chatbot AI, email tự động, phỏng vấn video, ATS/payment.

Không được hy sinh luồng tuyển dụng P0 để làm hiệu ứng UI. Tuy nhiên, thanh tìm kiếm và các bộ lọc cốt lõi đã nằm trong P0, không phải tính năng trang trí.

## 7. Công nghệ và cấu trúc

- Backend: Python + Flask, SQLite, Blueprint.
- Frontend: Jinja/HTML, CSS, Bootstrap (nếu hữu ích), JavaScript `fetch()`; chưa cần React cho MVP một tuần.
- API base local: `http://127.0.0.1:5000/api`.
- Session dùng cookie Flask; frontend cần gửi cookie khi gọi API cùng nguồn. Nếu chia frontend server riêng, cấu hình CORS/credentials thống nhất thay vì tắt bảo mật tùy tiện.
- Không gọi database trực tiếp từ frontend.

## 8. Cài đặt/chạy local (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
flask --app run.py init-db
python run.py
```

Mở `http://127.0.0.1:5000/`, API health `http://127.0.0.1:5000/api/health`.

Nếu schema thay đổi sau khi đã có database, không xóa DB của nhóm một cách mù quáng. Cần migration idempotent (kiểm tra cột/bảng đã tồn tại trước khi `ALTER TABLE`) hoặc dùng database demo có thể tái tạo. Không đưa mật khẩu thật, `.env`, `.venv`, `__pycache__`, upload CV hoặc database có dữ liệu cá nhân lên GitHub.

## 9. Hướng dẫn Git nhóm

```text
main
feature/public-student
feature/business-recruitment
feature/core-admin
```

Mỗi người làm branch riêng, commit rõ ràng, mở PR/trao đổi trước khi merge. Nếu sửa field/endpoint thì cập nhật code + schema/migration + contract + frontend + test cùng nhau.

## 10. Checklist nghiệm thu

- [ ] Guest tìm/lọc/xem tin công khai mà không cần đăng nhập.
- [ ] Student có thanh tìm kiếm giống đặc tả, lọc kết hợp nhiều tiêu chí, xóa/lưu bộ lọc, và xem trạng thái đơn.
- [ ] Keyword suggestions / job suggestions không dùng dữ liệu giả làm kết quả API.
- [ ] Business tìm/lọc tin và ứng viên trong phạm vi doanh nghiệp của mình.
- [ ] Admin/Moderator tìm/lọc hàng chờ duyệt và xem lịch sử.
- [ ] Admin tìm/lọc user theo keyword, role và trạng thái.
- [ ] Bài hướng nghiệp tìm/lọc theo title/category; draft không lộ ra public.
- [ ] Chỉ tin đã duyệt, doanh nghiệp đã duyệt, tài khoản doanh nghiệp active, deadline còn hạn mới xuất hiện trong public search.
- [ ] Các role không vượt quyền; thử truy cập dữ liệu của account khác.
- [ ] Test luồng end-to-end từ đăng ký doanh nghiệp tới student thấy kết quả đơn.
- [ ] Chạy tests trên máy nhóm; ghi trung thực test nào đã/chưa chạy.
