(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  // Gợi ý để chọn nhanh; vẫn nhập tự do được.
  const INDUSTRIES = ['Công nghệ thông tin', 'Tài chính - Ngân hàng', 'Bảo hiểm', 'Kế toán - Kiểm toán', 'Thương mại điện tử', 'Bán lẻ',
    'Sản xuất', 'Logistics - Vận tải', 'Bất động sản', 'Giáo dục - Đào tạo', 'Marketing - Truyền thông', 'Tư vấn doanh nghiệp',
    'Du lịch - Nhà hàng - Khách sạn', 'Y tế - Dược phẩm', 'Năng lượng', 'Xây dựng'];
  let saved = null;
  let freeAddress = false; // true khi chưa có dữ liệu provinces -> nhập tay

  const normalizeSite = (v) => { v = v.trim(); return v && !/^https?:\/\//i.test(v) ? 'https://' + v : v; };

  // địa chỉ (tỉnh -> phường/xã -> chi tiết)
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
  async function applyAddress(addr, provinces) {
    const parts = String(addr || '').split(',').map((s) => s.trim()).filter(Boolean);
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
  function composeAddress() {
    if (freeAddress) return $('address_detail').value.trim();
    const p = $('province'), w = $('ward');
    return [$('address_detail').value.trim(), w.value ? w.selectedOptions[0].textContent : '', p.value ? p.selectedOptions[0].textContent : ''].filter(Boolean).join(', ');
  }

  // cột bên phải
  function renderStatus(p) {
    const named = p.company_name !== BZ.DEFAULT_COMPANY_NAME;
    const msg = {
      approved: 'Công ty đã được duyệt và có thể đăng tin tuyển dụng.',
      pending: named ? 'Hồ sơ đang chờ nhà trường duyệt. Bạn sẽ đăng được tin sau khi được duyệt.' : 'Hãy điền tên công ty rồi lưu để gửi hồ sơ đi duyệt.',
      rejected: 'Hồ sơ chưa được duyệt. Chỉnh sửa theo ghi chú và lưu lại để gửi duyệt lại.',
    }[p.approval_status];
    $('statusCard').innerHTML = `<h2 class="section-title">Trạng thái duyệt</h2>${BZ.chip(p.approval_status, BZ.COMPANY_STATUS[p.approval_status])}
      <p style="margin:12px 0 0;color:var(--ink-2)">${BZ.esc(msg)}</p>
      ${p.review_note ? `<div class="letter" style="margin-top:12px"><b>Ghi chú của nhà trường</b><br>${BZ.esc(p.review_note)}</div>` : ''}
      ${p.reviewed_at ? `<p class="muted" style="margin:10px 0 0;font-size:12.5px">Duyệt lúc ${BZ.fmtDateTime(p.reviewed_at)}</p>` : ''}
      <p class="muted" style="margin:10px 0 0;font-size:12.5px">Tài khoản đăng nhập: ${BZ.esc(p.email)}</p>`;
  }

  function renderInfo(p) {
    const row = (icon, label, value) => `<div class="info-row">${BZ.icon(icon)}<div><div class="k">${label}</div><div class="v">${value ? BZ.esc(value) : '<span class="muted" style="font-weight:400">Chưa cập nhật</span>'}</div></div></div>`;
    const maps = p.address ? `<a class="btn btn-outline btn-sm" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(p.address)}">${BZ.icon('external', 'ic-sm')}Mở trong Google Maps</a>` : '';
    $('infoCard').innerHTML = `<h2 class="section-title">Thông tin chung</h2><div class="info-list">
      ${row('users', 'Quy mô', BZ.COMPANY_SIZE[p.company_size] || '')}
      ${row('briefcase', 'Ngành nghề chính', p.industry)}
      ${row('building', 'Địa điểm công ty', p.address)}</div>${maps ? `<div style="margin-top:14px">${maps}</div>` : ''}`;
  }

  function renderChecklist(p) {
    const items = [
      [p.company_name !== BZ.DEFAULT_COMPANY_NAME, 'Có tên công ty'],
      [!!(p.description || '').trim(), 'Có giới thiệu công ty'],
      [!!(p.website || '').trim(), 'Có website'],
      [!!p.company_size, 'Có quy mô nhân sự'],
      [!!(p.industry || '').trim(), 'Có ngành nghề'],
      [!!(p.address || '').trim(), 'Có địa điểm công ty'],
    ];
    const done = items.filter((i) => i[0]).length;
    $('checkCard').innerHTML = `<h2 class="section-title">Mức hoàn thiện</h2><div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="${items.length}" aria-valuenow="${done}"><i style="width:${done / items.length * 100}%"></i></div>
      <ul class="checklist">${items.map(([ok, t]) => `<li class="${ok ? 'ok' : 'todo'}">${BZ.icon(ok ? 'check' : 'x', 'ic-sm')}<span style="color:var(--ink-2)">${t}</span></li>`).join('')}</ul>`;
  }

  async function fill(p, provinces) {
    saved = p;
    $('company_name').value = p.company_name === BZ.DEFAULT_COMPANY_NAME ? '' : p.company_name;
    $('website').value = p.website || '';
    $('description').value = p.description || '';
    $('descCount').textContent = $('description').value.length;
    $('company_size').value = p.company_size || '';
    $('industry').value = p.industry || '';
    if (freeAddress) $('address_detail').value = p.address || ''; else await applyAddress(p.address, provinces);
    renderStatus(p); renderInfo(p); renderChecklist(p);
  }
  function setErr(field, msg) {
    const f = document.querySelector(`[data-field="${field}"]`);
    if (!f) return false;
    f.classList.toggle('invalid', !!msg); f.querySelector('.err').textContent = msg || '';
    return true;
  }

  let provincesList = [];
  async function load() {
    $('profileError').hidden = true; $('profileLayout').hidden = false;
    try { await fill(await BZ.api('/api/company/profile'), provincesList); }
    catch (e) { $('profileLayout').hidden = true; $('profileError').innerHTML = `<div class="card">${BZ.errorState(e.message)}</div>`; $('profileError').hidden = false; }
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try { await BZ.init(); } catch (e) { return; }
    if (BZ.readQuery(['welcome']).welcome) {
      $('welcomeNotice').innerHTML = `<div class="banner banner-info">${BZ.icon('info')}<div><b>Tài khoản đã sẵn sàng</b>Điền thông tin công ty bên dưới rồi lưu. Hồ sơ sẽ được nhà trường duyệt trước khi bạn đăng tin.</div></div>`;
    }
    $('industryList').innerHTML = INDUSTRIES.map((i) => `<option value="${BZ.esc(i)}">`).join('');
    try { provincesList = await BZ.loadProvinces(); } catch (e) { provincesList = []; }
    if (provincesList.length) {
      $('province').insertAdjacentHTML('beforeend', provincesList.map((p) => `<option value="${p.code}">${BZ.esc(p.name)}</option>`).join(''));
    } else {
      freeAddress = true;
      $('province').closest('.grid-2').hidden = true;
      $('address_detail').placeholder = 'Địa chỉ công ty';
      $('addressHint').textContent = 'Chưa có dữ liệu tỉnh/thành trong hệ thống nên bạn nhập địa chỉ trực tiếp.';
    }
    $('province').addEventListener('change', () => fillWards($('province').value));
    BZ.onRetry($('profileError'), load);
    $('description').addEventListener('input', () => { $('descCount').textContent = $('description').value.length; });
    $('website').addEventListener('blur', () => { $('website').value = normalizeSite($('website').value); });
    await load();

    $('profileForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      ['company_name', 'website', 'description', 'company_size', 'industry', 'address'].forEach((f) => setErr(f, ''));
      const body = {
        company_name: $('company_name').value.trim(), website: normalizeSite($('website').value), description: $('description').value.trim(),
        company_size: $('company_size').value, industry: $('industry').value.trim(), address: composeAddress(),
      };
      $('website').value = body.website;
      if (!body.company_name) { setErr('company_name', 'Nhập tên công ty.'); $('company_name').focus(); return; }
      if (body.website) { try { new URL(body.website); } catch (x) { setErr('website', 'Website không hợp lệ.'); return; } }
      const unchanged = saved && body.company_name === saved.company_name && body.website === (saved.website || '') && body.description === (saved.description || '')
        && body.company_size === (saved.company_size || '') && body.industry === (saved.industry || '') && body.address === (saved.address || '');
      if (unchanged) { BZ.toast('Chưa có thay đổi nào để lưu.'); return; }
      if (saved && saved.approval_status === 'approved') {
        const ok = await BZ.confirm({ title: 'Lưu và gửi duyệt lại?', message: 'Công ty đang ở trạng thái đã duyệt. Khi lưu, hồ sơ chuyển về “Chờ duyệt” và bạn chưa thể đăng tin mới cho đến khi được duyệt lại.', confirmText: 'Lưu và gửi duyệt lại' });
        if (!ok) return;
      }
      BZ.busy($('btnSave'), true, 'Đang lưu…');
      try {
        await BZ.api('/api/company/profile', { method: 'PUT', body });
        BZ.toast('Đã lưu hồ sơ. Hồ sơ đang chờ nhà trường duyệt.');
        location.href = '/business/profile'; // nạp lại để cập nhật banner và nút đăng tin
      } catch (err) {
        BZ.busy($('btnSave'), false);
        const f = /website/i.test(err.message) ? 'website' : /Tên/i.test(err.message) ? 'company_name' : /Ngành/i.test(err.message) ? 'industry' : /Địa chỉ/i.test(err.message) ? 'address' : /company_size/i.test(err.message) ? 'company_size' : null;
        if (!(f && setErr(f, err.message))) BZ.toast(err.message, 'error');
      }
    });
  });
})();
