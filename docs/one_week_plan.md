# Kế hoạch 1 tuần — Career Connect

## Luồng nghiệp vụ MVP
Doanh nghiệp đăng ký → admin/moderator duyệt doanh nghiệp → doanh nghiệp tạo tin → admin/moderator duyệt tin → guest/student tìm và lọc → student ứng tuyển → business tìm/lọc ứng viên và cập nhật trạng thái → student theo dõi trạng thái.

## Module và phân công

### TV1 — Public Discovery + Student Journey (FE + BE)
- Trang guest/student tìm việc theo `docs/SEARCH_UI_SPEC.md`: query, location, category multi-select, job type, major/skills, Saturday policy, posted date, sort.
- Search bar, suggestion dropdown, category counts, results/detail, no-result/error/loading states, clear/save filters (localStorage).
- Hồ sơ/CV, ứng tuyển, tìm/lọc lịch sử đơn và theo dõi trạng thái.
- Endpoint owner: `/api/jobs*`, `/api/students/*`, `/api/applications/*`, public `/api/career-contents*`.

### TV2 — Business Recruitment Journey (FE + BE)
- Hồ sơ doanh nghiệp.
- CRUD tin tuyển dụng: tạo/xem/sửa/đóng tin; search/filter tin của mình.
- Xem chi tiết và tìm/lọc ứng viên theo keyword/job/status; cập nhật trạng thái đơn.
- Endpoint owner: `/api/company/*`.

### TV3 — Platform + Staff/Admin + Integration (FE + BE)
- Flask/SQLite/schema/migration/demo seed, auth/session/role guards.
- Dashboard moderation và tìm/lọc doanh nghiệp/tin chờ duyệt; review history.
- Admin user/category/content CRUD kèm query filters; login/register và navigation theo role.
- Endpoint owner: `/api/auth/*`, `/api/admin/*`; chịu trách nhiệm integration nhưng không kiểm thử thay TV1/TV2.

## Lịch
- Ngày 1: Chốt contract/schema, repo/branch, trang khung; chạy app/init-db được.
- Ngày 2: Auth/core và search UI skeleton; mỗi module phát triển đồng thời.
- Ngày 3: Job search API + filters, company job CRUD/search, admin review/search.
- Ngày 4: Apply/tracking, applicant search/status; nối FE thật vào API.
- Ngày 5: Chạy end-to-end và giải quyết merge conflicts/API mismatches.
- Ngày 6: Test query filters kết hợp, ownership, status, dữ liệu rỗng; sửa lỗi.
- Ngày 7: Freeze code, test trên máy demo, tài khoản/data demo, báo cáo.

## Các quyết định bắt buộc
- Contract trước; BE/FE có thể làm song song sau khi request/response đã thống nhất.
- Tìm kiếm/lọc phải query dữ liệu thực; không tạo filter UI giả.
- Delete job = close, delete application = withdraw, delete account = deactivate.
- Không làm chatbot AI, email tự động, phỏng vấn video, ATS/payment trong MVP.
- Nếu trễ, cắt P2/hiệu ứng; không cắt public search/filter và luồng tuyển dụng.
