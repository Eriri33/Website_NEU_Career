(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  let saved = null;

  function normalizeSite(v) {
    v = v.trim();
    return v && !/^https?:\/\//i.test(v) ? 'https://' + v : v;
  }

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
    const items = [
      [named, 'Có tên công ty'],
      [!!(p.description || '').trim(), 'Có giới thiệu công ty'],
      [!!(p.website || '').trim(), 'Có website'],
      [!!(p.company_size || '').trim(), 'Có quy mô công ty'],
      [!!(p.primary_industry || '').trim(), 'Có ngành nghề chính'],
      [!!(p.business_industries || '').trim(), 'Có lĩnh vực kinh doanh'],
      [!!(p.address || '').trim(), 'Có địa điểm công ty'],
    ];
    const done = items.filter((i) => i[0]).length;
    $('checkCard').innerHTML = `<h2 class="section-title">Mức hoàn thiện</h2><div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="${items.length}" aria-valuenow="${done}"><i style="width:${done / items.length * 100}%"></i></div>
      <ul class="checklist">${items.map(([ok, t]) => `<li class="${ok ? 'ok' : 'todo'}">${BZ.icon(ok ? 'check' : 'x', 'ic-sm')}<span style="color:var(--ink-2)">${t}</span></li>`).join('')}</ul>`;
  }

  function renderPublicDetails(p) {
    const publicUrl = `${location.origin}/companies/${p.id}`;
    $('companyInfoCard').innerHTML = `<h2 class="section-title">Thông tin chung</h2><dl class="company-info-list">
      <div><dt>Quy mô</dt><dd>${BZ.esc(p.company_size || 'Đang cập nhật')}</dd></div>
      <div><dt>Lĩnh vực kinh doanh</dt><dd>${BZ.esc(p.business_industries || 'Đang cập nhật')}</dd></div>
      <div><dt>Ngành nghề chính</dt><dd>${BZ.esc(p.primary_industry || 'Đang cập nhật')}</dd></div>
    </dl>`;
    $('mapCard').innerHTML = p.address ? `<h2 class="section-title">Địa điểm công ty</h2>
      <iframe class="profile-map" title="Bản đồ địa điểm công ty" loading="lazy" src="https://www.google.com/maps?q=${encodeURIComponent(p.address)}&output=embed"></iframe>
      <p class="muted" style="margin:0 0 8px">${BZ.esc(p.address)}</p><a class="link" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(p.address)}">Mở trong Google Maps ↗</a>` : `<h2 class="section-title">Địa điểm công ty</h2><p class="muted">Thêm địa chỉ để hiển thị bản đồ cho sinh viên.</p>`;
    $('shareCard').innerHTML = `<h2 class="section-title">Chia sẻ công ty</h2><p class="muted" style="margin-top:-6px">Sao chép đường dẫn hồ sơ công khai.</p><div class="share-link"><input class="input" value="${BZ.esc(publicUrl)}" readonly aria-label="Đường dẫn hồ sơ công khai"><button type="button" class="btn btn-secondary" id="copyShare">Sao chép</button></div>`;
    $('copyShare').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(publicUrl); BZ.toast('Đã sao chép đường dẫn hồ sơ công ty.'); }
      catch (_) { $('shareCard input').select(); document.execCommand('copy'); BZ.toast('Đã sao chép đường dẫn hồ sơ công ty.'); }
    });
  }

  function fill(p) {
    saved = p;
    $('company_name').value = p.company_name === BZ.DEFAULT_COMPANY_NAME ? '' : p.company_name;
    $('website').value = p.website || '';
    $('company_size').value = p.company_size || '';
    $('primary_industry').value = p.primary_industry || '';
    $('business_industries').value = p.business_industries || '';
    $('address').value = p.address || '';
    $('description').value = p.description || '';
    $('descCount').textContent = $('description').value.length;
    renderStatus(p);
    renderPublicDetails(p);
  }
  function setErr(field, msg) {
    const f = document.querySelector(`[data-field="${field}"]`);
    f.classList.toggle('invalid', !!msg); f.querySelector('.err').textContent = msg || '';
  }

  async function load() {
    $('profileError').hidden = true; $('profileLayout').hidden = false;
    try { fill(await BZ.api('/api/company/profile')); }
    catch (e) { $('profileLayout').hidden = true; $('profileError').innerHTML = `<div class="card">${BZ.errorState(e.message)}</div>`; $('profileError').hidden = false; }
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try { await BZ.init(); } catch (e) { return; }
    if (BZ.readQuery(['welcome']).welcome) {
      $('welcomeNotice').innerHTML = `<div class="banner banner-info">${BZ.icon('info')}<div><b>Tài khoản đã sẵn sàng</b>Điền thông tin công ty bên dưới rồi lưu. Hồ sơ sẽ được nhà trường duyệt trước khi bạn đăng tin.</div></div>`;
    }
    BZ.onRetry($('profileError'), load);
    $('description').addEventListener('input', () => { $('descCount').textContent = $('description').value.length; });
    $('website').addEventListener('blur', () => { $('website').value = normalizeSite($('website').value); });
    await load();

    $('profileForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      ['company_name', 'website', 'company_size', 'primary_industry', 'business_industries', 'address', 'description'].forEach((f) => setErr(f, ''));
      const body = { company_name: $('company_name').value.trim(), website: normalizeSite($('website').value), company_size: $('company_size').value, primary_industry: $('primary_industry').value.trim(), business_industries: $('business_industries').value.trim(), address: $('address').value.trim(), description: $('description').value.trim() };
      $('website').value = body.website;
      if (!body.company_name) { setErr('company_name', 'Nhập tên công ty.'); $('company_name').focus(); return; }
      if (body.website) { try { new URL(body.website); } catch (x) { setErr('website', 'Website không hợp lệ.'); return; } }
      const unchanged = saved && Object.keys(body).every((key) => body[key] === (saved[key] || ''));
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
        if (/website/i.test(err.message)) setErr('website', err.message); else if (/Tên/i.test(err.message)) setErr('company_name', err.message); else BZ.toast(err.message, 'error');
      }
    });
  });
})();
