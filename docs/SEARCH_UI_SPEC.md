# SEARCH & FILTER UI SPEC — Career Connect

**Mục đích:** Mô tả hành vi bắt buộc của chức năng tìm kiếm/lọc theo ảnh mẫu người dùng gửi. Tài liệu này bổ sung, không thay thế endpoint/quyền trong `API_CONTRACT.md`.

## 1. Khu vực tìm việc công khai

### 1.1 Thanh tìm kiếm chính

Từ trái sang phải:

1. Dropdown **Danh mục nghề** lấy danh mục đang active từ `GET /api/jobs/categories`.
2. Input **Vị trí tuyển dụng** gắn với query `q`.
3. Input **Địa điểm** gắn với query `location`.
4. Nút xóa input; xóa input không tự gửi truy vấn cho tới khi người dùng chọn Tìm kiếm, trừ khi UI đang ở chế độ auto-search được thống nhất.
5. Nút **Tìm kiếm**; nhấn Enter trong input cũng thực hiện tìm kiếm.

Không hard-code Hà Nội làm địa điểm cố định. Có thể dùng địa điểm gần nhất/gợi ý ở bản sau, nhưng người dùng phải tự sửa/xóa được.

### 1.2 Dropdown gợi ý

Mở khi focus thanh search hoặc khi người dùng nhập ít nhất một ký tự; đóng khi nhấn Escape, click ngoài hoặc chọn mục.

- Cột trái: “Từ khóa phổ biến” (MVP dùng danh sách seed/curated; không gọi là số liệu real-time nếu chưa ghi nhận search logs). Nhấn từ khóa sẽ điền `q` và tìm.
- Cột phải: “Việc làm có thể bạn quan tâm”. Guest xem tin public mới nhất; student đã đăng nhập có thể dùng kết quả `/api/students/me/recommendations`. Mỗi card hiển thị title, company, location và `salary_text` nếu có.
- Không có gợi ý thì hiển thị trạng thái rỗng; lỗi gợi ý không được làm hỏng thanh search chính.
- Trên màn hình nhỏ, hai cột được xếp dọc; không để dropdown che toàn bộ input/nút tìm.

### 1.3 Bộ lọc nâng cao

Các bộ lọc phải được giữ trạng thái trên UI khi hiển thị kết quả và phải được gửi tới `GET /api/jobs`:

| Bộ lọc | Điều khiển | API param |
|---|---|---|
| Danh mục nghề | Checkbox, hỗ trợ chọn nhiều | `category_ids=1,3` |
| Từ khóa/vị trí | Input text | `q` |
| Địa điểm | Input text | `location` |
| Loại công việc | Select/checkbox | `job_type` |
| Ngành học | Input/select theo danh mục ngành tối giản | `major` |
| Kỹ năng | Input từ khóa | `skills` |
| Làm thứ Bảy | Radio: Không lọc / Nghỉ thứ Bảy / Làm thứ Bảy / Thỏa thuận-chưa rõ (nếu cần) | `saturday_policy` |
| Ngày đăng | Select: 1 ngày / 3 ngày / 7 ngày / 30 ngày | `posted_within` |
| Sắp xếp | Select: mới nhất / phù hợp / hạn gần nhất | `sort` |

Khi user chọn nhiều checkbox danh mục, kết quả khớp một trong các category được chọn; các loại filter khác kết hợp AND. Ví dụ chọn Marketing hoặc Kế toán và location Hà Nội thì tin phải thuộc một trong 2 danh mục **và** thỏa địa điểm Hà Nội.

Nút **Xóa lọc**: reset mọi filter về mặc định, cập nhật URL (nếu dùng query string) và tải lại danh sách public mặc định.

Nút **Lưu bộ lọc**: lưu object filter hiện tại vào `localStorage` với key có namespace `careerConnect.savedJobFilters`. Cho phép tải bộ lọc đã lưu về sau. Nếu có nhiều bộ lọc lưu, cho đặt tên đơn giản hoặc hiển thị danh sách để chọn/xóa. Không cần BE endpoint/database trong MVP.

### 1.4 Thẻ danh mục phổ biến

Bên dưới search/filter, hiển thị một khu vực kiểu “Thử lựa chọn ngay các nghề hot”. Mỗi thẻ chứa tên danh mục và `job_count` từ `/api/jobs/categories`. Nhấn thẻ sẽ chọn danh mục và thực hiện search. Nếu count = 0, ẩn thẻ hoặc hiển thị 0; không tự điền số.

### 1.5 Kết quả tìm kiếm

Mỗi card cần có:

- Chức danh/tên vị trí.
- Tên doanh nghiệp; logo thật chưa bắt buộc, có thể dùng placeholder/initial nếu DB chưa có logo.
- Địa điểm.
- Danh mục và loại công việc.
- Lương `salary_text` nếu doanh nghiệp có cung cấp; nếu thiếu thì hiển thị “Thỏa thuận” hoặc “Chưa cập nhật” đúng dữ liệu, không tự tạo con số.
- Hạn ứng tuyển và thời gian đăng.
- Nút “Xem chi tiết”; nút “Ứng tuyển” yêu cầu student đăng nhập.

Các trạng thái bắt buộc: loading skeleton/spinner, không có kết quả, lỗi API và nút thử lại. Khi tìm kiếm không có kết quả, vẫn giữ input/filter để người dùng dễ sửa.

## 2. Tìm/lọc cho Student

- Dùng chung trang tìm việc public.
- Phần gợi ý có thể gọi `/api/students/me/recommendations`; recommendation chỉ là rule-based theo major/skills, không quảng cáo là AI.
- Lịch sử ứng tuyển có input q tìm theo job title/company, filter `status`, sort latest/oldest. API chỉ trả đơn student hiện tại.
- Hồ sơ/CV của người dùng chỉ hiển thị ở trang cá nhân; không cho guest tải CV và không để student truy cập CV của student khác.

## 3. Tìm/lọc cho Business

### 3.1 Tin tuyển dụng của tôi

- Input q: title/description.
- Filters: status (`pending`, `approved`, `rejected`, `closed`), category, location, job_type.
- Sort: mới nhất/hạn gần nhất.
- Row/card hiển thị status rõ ràng; tin edited phải hiển thị “Chờ duyệt lại”.
- Dữ liệu chỉ thuộc company của session hiện tại.

### 3.2 Ứng viên

- Input q: full_name/email/major/skills.
- Filters: job_id, application status (`submitted`, `reviewing`, `accepted`, `rejected`, `withdrawn`).
- Sort theo ngày ứng tuyển.
- Chỉ xem đơn thuộc tin của business đang đăng nhập. Không nhận company_id từ FE như bằng chứng quyền; BE phải kiểm tra ownership qua session.

## 4. Tìm/lọc cho Moderator/Admin

- Hàng chờ doanh nghiệp: tìm tên doanh nghiệp/email, sort cũ nhất/mới nhất.
- Hàng chờ tin: tìm tiêu đề/mô tả/tên công ty; lọc category/location/job_type.
- Admin/Moderator xem danh sách tất cả company/job: filter status phù hợp và query q.
- Admin accounts: q email/tên sinh viên/tên doanh nghiệp; filter role và active/inactive.
- Danh mục: q theo name; filter active/inactive.
- Career content public: q title/summary/body và category, chỉ published.
- Career content staff: q, category, draft/published.
- Review history: filter entity type/id, reviewer/action/ngày nếu triển khai; lịch sử là read-only.
- Tất cả endpoint quản trị phải có role guard ở backend; ẩn nút trên FE không thay thế phân quyền BE.

## 5. Ví dụ luồng tìm kiếm

1. Guest mở trang chủ, chọn category “Marketing”, nhập `content` vào q, nhập `Hà Nội` vào location.
2. Nhấn Tìm kiếm; FE gọi ví dụ:

   `GET /api/jobs?q=content&location=H%C3%A0%20N%E1%BB%99i&category_ids=2&sort=latest`

3. Backend chỉ trả tin công khai hợp lệ; UI hiển thị kết quả.
4. Guest mở tin; nhấn Ứng tuyển sẽ được yêu cầu đăng nhập/đăng ký student, sau đó quay lại tin nếu có thể.
5. Student đăng nhập, chọn bộ lọc làm thứ Bảy = Nghỉ thứ Bảy và ngày đăng = 7 ngày; FE gửi `saturday_policy=off&posted_within=7`.
6. Chọn Xóa lọc sẽ bỏ query params và tải lại danh sách mặc định.
7. Nhấn Lưu bộ lọc sẽ ghi trạng thái vào localStorage; reload trang vẫn có thể nạp lại.

## 6. Tiêu chí nghiệm thu search

- [ ] Guest search không cần login và không thấy tin pending/rejected/closed/expired.
- [ ] Mỗi filter thực sự làm thay đổi kết quả từ backend.
- [ ] Có thể phối hợp q + location + category + job type + posting date + Saturday policy.
- [ ] Nhiều category hoạt động như OR nội bộ; các nhóm filter khác kết hợp AND.
- [ ] Category counts phản ánh số tin public hợp lệ, không phải số mọi tin trong DB.
- [ ] Popular keywords chọn được và điền vào input.
- [ ] Guest suggestions không chứa job private; student recommendations không yêu cầu AI/LLM.
- [ ] Clear filters và save/load filters hoạt động.
- [ ] Business applicant filters không lộ ứng viên của công ty khác.
- [ ] Admin/moderator tìm được hàng chờ và kết quả theo filters.
- [ ] Không dùng kết quả giả/hard-code danh sách tin trong frontend.
