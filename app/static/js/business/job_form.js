(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const mode = document.body.dataset.mode;
  const jobId = document.body.dataset.jobId;
  const MAJORS = ['Kinh tế', 'Kinh tế quốc tế', 'Quản trị kinh doanh', 'Marketing', 'Tài chính - Ngân hàng', 'Kế toán', 'Kiểm toán',
    'Thương mại điện tử', 'Logistics và quản lý chuỗi cung ứng', 'Hệ thống thông tin quản lý', 'Khoa học dữ liệu', 'Công nghệ thông tin',
    'Luật kinh tế', 'Quản trị nhân lực', 'Kinh tế đầu tư', 'Bất động sản', 'Du lịch và lữ hành'];
  let skills = [];
  let freeLocation = false; // true khi chưa có dữ liệu provinces -> nhập tay

  function renderSkills() {
    $('skillsBox').querySelectorAll('.tag').forEach((t) => t.remove());
    const input = $('skillInput');
    skills.forEach((s, i) => {
      const t = document.createElement('span');
      t.className = 'tag';
      t.innerHTML = `${BZ.esc(s)}<button type="button" aria-label="Xóa kỹ năng ${BZ.esc(s)}" data-i="${i}">&times;</button>`;
      $('skillsBox').insertBefore(t, input);
    });
  }
  function addSkills(raw) {
    BZ.splitList(raw).forEach((s) => { if (!skills.some((x) => BZ.fold(x) === BZ.fold(s))) skills.push(s); });
    renderSkills();
  }

  function setErr(field, msg) {
    const f = document.querySelector(`[data-field="${field}"]`);
    if (!f) return false;
    f.classList.toggle('invalid', !!msg);
    const e = f.querySelector('.err'); if (e) e.textContent = msg || '';
    return true;
  }
  function clearErrs() { document.querySelectorAll('[data-field]').forEach((f) => { f.classList.remove('invalid'); const e = f.querySelector('.err'); if (e) e.textContent = ''; }); }

  function composeLocation() {
    if (freeLocation) return $('address_detail').value.trim();
    const p = $('province'), w = $('ward');
    return [$('address_detail').value.trim(), w.value ? w.selectedOptions[0].textContent : '', p.value ? p.selectedOptions[0].textContent : ''].filter(Boolean).join(', ');
  }

  async function fillWards(code, selectedCode) {
    const w = $('ward');
    if (!code) { w.innerHTML = '<option value="">Chọn tỉnh/thành trước</option>'; w.disabled = true; return; }
    w.disabled = true; w.innerHTML = '<option value="">Đang tải…</option>';
    try {
      const wards = await BZ.loadWards(code);
      w.innerHTML = '<option value="">Chọn phường/xã (không bắt buộc)</option>' + wards.map((x) => `<option value="${x.code}">${BZ.esc(x.name)}</option>`).join('');
      w.disabled = false;
      if (selectedCode) w.value = selectedCode;
    } catch (e) { w.innerHTML = '<option value="">Không tải được phường/xã</option>'; }
  }

  // Tách chuỗi location đã lưu thành tỉnh / phường / địa chỉ cụ thể
  async function applyLocation(loc, provinces) {
    const parts = String(loc || '').split(',').map((s) => s.trim()).filter(Boolean);
    const prov = parts.length ? provinces.find((p) => BZ.fold(p.name) === BZ.fold(parts[parts.length - 1])) : null;
    if (!prov) { $('address_detail').value = parts.join(', '); return; }
    parts.pop();
    $('province').value = prov.code;
    const wards = await BZ.loadWards(prov.code);
    const ward = parts.length ? wards.find((x) => BZ.fold(x.name) === BZ.fold(parts[parts.length - 1])) : null;
    if (ward) parts.pop();
    await fillWards(prov.code, ward && ward.code);
    $('address_detail').value = parts.join(', ');
  }

  function collect() {
    return {
      title: $('title').value.trim(),
      description: $('description').value.trim(),
      category_id: $('category_id').value ? Number($('category_id').value) : null,
      job_type: $('job_type').value,
      major_required: $('major_required').value.trim(),
      skills_required: skills.join(', '),
      location: composeLocation(),
      saturday_policy: document.querySelector('input[name=saturday_policy]:checked').value,
      salary_text: $('salary_text').value.trim(),
      deadline: $('deadline').value || null,
    };
  }

  function validate(d, original) {
    clearErrs();
    let ok = true;
    const bad = (f, m) => { setErr(f, m); ok = false; };
    if (!d.title) bad('title', 'Nhập chức danh tuyển dụng.');
    if (!d.description) bad('description', 'Nhập mô tả công việc.');
    if (d.skills_required.length > 500) bad('skills_required', 'Danh sách kỹ năng quá dài (tối đa 500 ký tự).');
    if (d.deadline && d.deadline < BZ.todayStr() && d.deadline !== (original && original.deadline)) bad('deadline', 'Hạn nộp không được là ngày đã qua.');
    return ok;
  }

  document.addEventListener('DOMContentLoaded', async () => {
    let profile;
    try { profile = await BZ.init(); } catch (e) { return; }
    const form = $('jobForm');
    $('majorList').innerHTML = MAJORS.map((m) => `<option value="${BZ.esc(m)}">`).join('');
    $('deadline').min = BZ.todayStr();

    if (mode === 'create' && profile.approval_status !== 'approved') {
      $('formLoadError').innerHTML = `<div class="card">${BZ.emptyState({ icon: 'lock', title: 'Chưa thể đăng tin', text: 'Hồ sơ công ty cần được nhà trường duyệt trước khi đăng tin.', actionHtml: '<a class="btn btn-primary" href="/business/profile">Mở hồ sơ công ty</a>' })}</div>`;
      $('formLoadError').hidden = false;
      return;
    }
    $('btnCancel').href = mode === 'edit' ? `/business/jobs/${jobId}` : '/business/jobs';

    // danh mục + địa điểm (dữ liệu thật từ API)
    let provinces = [];
    try {
      const cats = await BZ.api('/api/company/categories');
      $('category_id').insertAdjacentHTML('beforeend', cats.map((c) => `<option value="${c.id}">${BZ.esc(c.name)}</option>`).join(''));
    } catch (e) { BZ.toast('Không tải được danh mục nghề: ' + e.message, 'error'); }
    try { provinces = await BZ.loadProvinces(); } catch (e) { provinces = []; }
    if (provinces.length) {
      $('province').insertAdjacentHTML('beforeend', provinces.map((p) => `<option value="${p.code}">${BZ.esc(p.name)}</option>`).join(''));
    } else {
      freeLocation = true;
      $('province').closest('.grid-2').hidden = true;
      $('address_detail').placeholder = 'Ví dụ: Hà Nội';
      $('locationHint').textContent = 'Chưa có dữ liệu tỉnh/thành trong hệ thống nên bạn nhập địa điểm trực tiếp.';
    }

    let original = null;
    if (mode === 'edit') {
      try { original = await BZ.api(`/api/company/jobs/${jobId}`); }
      catch (e) {
        $('formLoadError').innerHTML = `<div class="card">${e.status === 404
          ? BZ.emptyState({ icon: 'search', title: 'Không tìm thấy tin', text: 'Tin không tồn tại hoặc không thuộc công ty của bạn.', actionHtml: '<a class="btn btn-primary" href="/business/jobs">Về danh sách tin</a>' })
          : BZ.errorState(e.message)}</div>`;
        $('formLoadError').hidden = false;
        BZ.onRetry($('formLoadError'), () => location.reload());
        return;
      }
      $('title').value = original.title; $('description').value = original.description;
      $('category_id').value = original.category_id || ''; $('job_type').value = original.job_type;
      $('major_required').value = original.major_required || ''; addSkills(original.skills_required);
      $('salary_text').value = original.salary_text === 'Thỏa thuận' ? '' : original.salary_text;
      $('deadline').value = original.deadline || '';
      const radio = document.querySelector(`input[name=saturday_policy][value="${original.saturday_policy}"]`); if (radio) radio.checked = true;
      if (freeLocation) $('address_detail').value = original.location || ''; else await applyLocation(original.location, provinces);
      $('btnSubmit').textContent = 'Lưu và gửi duyệt lại';
      if (original.status === 'approved') {
        $('formNotice').innerHTML = `<div class="banner banner-warn">${BZ.icon('alert')}<div><b>Tin đang hiển thị công khai</b>Khi bạn lưu thay đổi, tin sẽ tạm ẩn với sinh viên cho đến khi nhà trường duyệt lại.</div></div>`;
      } else if (original.status === 'closed') {
        $('formNotice').innerHTML = `<div class="banner banner-info">${BZ.icon('info')}<div><b>Tin đã đóng</b>Lưu thay đổi sẽ gửi tin đi duyệt để đăng lại.</div></div>`;
      } else if (original.status === 'rejected' && original.review_note) {
        $('formNotice').innerHTML = `<div class="banner banner-danger">${BZ.icon('alert')}<div><b>Tin bị từ chối</b>Lý do: ${BZ.esc(original.review_note)}</div></div>`;
      }
    }

    // sự kiện
    const counter = (src, dst) => { const f = () => { $(dst).textContent = $(src).value.length; }; $(src).addEventListener('input', f); f(); };
    counter('title', 'titleCount'); counter('description', 'descCount');
    $('province').addEventListener('change', () => fillWards($('province').value));
    $('skillInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addSkills($('skillInput').value); $('skillInput').value = ''; }
      else if (e.key === 'Backspace' && !$('skillInput').value && skills.length) { skills.pop(); renderSkills(); }
    });
    $('skillInput').addEventListener('blur', () => { if ($('skillInput').value.trim()) { addSkills($('skillInput').value); $('skillInput').value = ''; } });
    $('skillsBox').addEventListener('click', (e) => { const b = e.target.closest('button[data-i]'); if (b) { skills.splice(Number(b.dataset.i), 1); renderSkills(); } });
    form.hidden = false;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if ($('skillInput').value.trim()) { addSkills($('skillInput').value); $('skillInput').value = ''; }
      const data = collect();
      if (!validate(data, original)) { const first = document.querySelector('.invalid input, .invalid textarea'); if (first) first.focus(); return; }
      BZ.busy($('btnSubmit'), true, 'Đang gửi…');
      try {
        if (mode === 'edit') {
          await BZ.api(`/api/company/jobs/${jobId}`, { method: 'PUT', body: data });
          BZ.flash('Đã lưu tin. Tin đang chờ nhà trường duyệt lại.');
          location.href = `/business/jobs/${jobId}`;
        } else {
          const res = await BZ.api('/api/company/jobs', { method: 'POST', body: data });
          BZ.flash('Đã gửi tin. Tin đang chờ nhà trường duyệt.');
          location.href = `/business/jobs/${res.job_id}`;
        }
      } catch (err) {
        BZ.busy($('btnSubmit'), false);
        const map = { invalid_category: 'category_id' };
        const msg = err.message;
        const field = map[err.code] || (/deadline|Hạn nộp/i.test(msg) ? 'deadline' : /title|Tiêu đề/i.test(msg) ? 'title' : /description|Mô tả/i.test(msg) ? 'description' : /salary/i.test(msg) ? 'salary_text' : /location/i.test(msg) ? 'location' : null);
        if (!(field && setErr(field, msg))) BZ.toast(msg, 'error'); else BZ.toast('Kiểm tra lại các trường được đánh dấu.', 'error');
      }
    });
  });
})();
