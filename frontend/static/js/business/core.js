(function () {
  'use strict';
  const BZ = (window.BZ = {});

  // nhãn hiển thị
  BZ.JOB_STATUS = { pending: 'Chờ duyệt', approved: 'Đang hiển thị', rejected: 'Bị từ chối', closed: 'Đã đóng' };
  BZ.APP_STATUS = { submitted: 'Mới nộp', reviewing: 'Đang xem xét', accepted: 'Đã nhận', rejected: 'Từ chối', withdrawn: 'Đã rút' };
  BZ.JOB_TYPE = { internship: 'Thực tập', full_time: 'Toàn thời gian', part_time: 'Bán thời gian', contract: 'Hợp đồng' };
  BZ.SATURDAY = { off: 'Nghỉ thứ Bảy', working: 'Làm thứ Bảy', negotiable: 'Thỏa thuận thứ Bảy', unknown: 'Chưa nêu rõ' };
  BZ.COMPANY_STATUS = { pending: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Bị từ chối' };
  BZ.COMPANY_SIZE = { '1-9': '1-9 nhân viên', '10-24': '10-24 nhân viên', '25-99': '25-99 nhân viên', '100-499': '100-499 nhân viên', '500-999': '500-999 nhân viên', '1000+': 'Từ 1000 nhân viên' };
  BZ.DEFAULT_COMPANY_NAME = 'Chưa cập nhật';

  // chuỗi
  BZ.esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  BZ.fold = (s) => String(s == null ? '' : s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'd').toLowerCase().trim();
  BZ.icon = (name, cls) => `<svg class="ic ${cls || ''}" aria-hidden="true"><use href="#i-${name}"/></svg>`;
  BZ.initials = (name) => {
    const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return '?';
    const pick = parts.length === 1 ? parts[0][0] : parts[0][0] + parts[parts.length - 1][0];
    return pick.toUpperCase();
  };
  BZ.splitList = (s) => String(s || '').split(/[,;]/).map((x) => x.trim()).filter(Boolean);
  BZ.debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

  // ngày giờ
  const pad = (n) => String(n).padStart(2, '0');
  BZ.parseTs = (s) => (s ? new Date(String(s).replace(' ', 'T') + 'Z') : null); // DB lưu UTC
  BZ.fmtDate = (s) => {
    if (!s) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) { const [y, m, d] = s.split('-'); return `${d}/${m}/${y}`; }
    const dt = BZ.parseTs(s);
    return `${pad(dt.getDate())}/${pad(dt.getMonth() + 1)}/${dt.getFullYear()}`;
  };
  BZ.fmtDateTime = (s) => {
    const dt = BZ.parseTs(s);
    return dt ? `${pad(dt.getHours())}:${pad(dt.getMinutes())} ${BZ.fmtDate(s)}` : '';
  };
  BZ.relTime = (s) => {
    const dt = BZ.parseTs(s);
    if (!dt) return '';
    const sec = Math.max(0, Math.round((Date.now() - dt.getTime()) / 1000));
    if (sec < 60) return 'Vừa xong';
    if (sec < 3600) return `${Math.floor(sec / 60)} phút trước`;
    if (sec < 86400) return `${Math.floor(sec / 3600)} giờ trước`;
    if (sec < 86400 * 2) return 'Hôm qua';
    if (sec < 86400 * 30) return `${Math.floor(sec / 86400)} ngày trước`;
    return BZ.fmtDate(s);
  };
  BZ.todayStr = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };
  BZ.daysUntil = (ds) => {
    const [y, m, d] = ds.split('-').map(Number);
    const t = new Date();
    return Math.round((Date.UTC(y, m - 1, d) - Date.UTC(t.getFullYear(), t.getMonth(), t.getDate())) / 86400000);
  };
  BZ.deadlineHtml = (job) => {
    if (!job.deadline) return '<span class="muted">Không giới hạn</span>';
    const text = BZ.fmtDate(job.deadline);
    if (job.is_expired) return `<span class="due-over">${text}</span><div class="cell-sub due-over">Đã hết hạn</div>`;
    const left = BZ.daysUntil(job.deadline);
    if (left <= 7) return `<span class="due-soon">${text}</span><div class="cell-sub due-soon">${left === 0 ? 'Hết hạn hôm nay' : `Còn ${left} ngày`}</div>`;
    return text;
  };

  // gọi API
  class BZError extends Error {
    constructor(status, code, message) { super(message); this.status = status; this.code = code; }
  }
  BZ.Error = BZError;

  BZ.goLogin = (reason) => {
    const next = encodeURIComponent(location.pathname + location.search);
    location.href = `/business/login?next=${next}${reason ? '&reason=' + reason : ''}`;
  };

  BZ.api = async (path, opts = {}) => {
    const { method = 'GET', body, query } = opts;
    let url = path;
    if (query) {
      const p = new URLSearchParams();
      Object.entries(query).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') p.set(k, v); });
      const qs = p.toString();
      if (qs) url += (url.includes('?') ? '&' : '?') + qs;
    }
    const init = { method, credentials: 'same-origin', headers: { Accept: 'application/json' } };
    if (body !== undefined) { init.headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(body); }
    let res;
    try { res = await fetch(url, init); } catch (e) {
      throw new BZError(0, 'network', 'Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.');
    }
    let data = null;
    try { data = await res.json(); } catch (e) { /* body rỗng hoặc không phải JSON */ }
    if (res.status === 401 && !opts.noRedirect) { BZ.goLogin('expired'); throw new BZError(401, 'unauthorized', 'Phiên đăng nhập đã hết hạn.'); }
    if (!res.ok) {
      throw new BZError(res.status, data && data.error, (data && data.message) || `Có lỗi xảy ra (mã ${res.status}). Thử lại sau.`);
    }
    return data;
  };

  // giao diện chung
  BZ.chip = (kind, text, extra) => `<span class="chip chip-${kind} ${extra || ''}">${BZ.esc(text)}</span>`;

  BZ.toast = (message, type) => {
    let box = document.getElementById('toasts');
    if (!box) { box = document.createElement('div'); box.id = 'toasts'; box.className = 'toasts'; box.setAttribute('role', 'status'); document.body.appendChild(box); }
    const el = document.createElement('div');
    el.className = 'toast' + (type === 'error' ? ' error' : '');
    el.innerHTML = (type === 'error' ? BZ.icon('alert') : BZ.icon('check')) + `<span>${BZ.esc(message)}</span>`;
    box.appendChild(el);
    setTimeout(() => el.remove(), type === 'error' ? 6500 : 4000);
  };
  // Thông báo giữ qua một lần chuyển trang (vd. sau khi tạo tin xong)
  BZ.flash = (message) => { try { sessionStorage.setItem('bz.flash', message); } catch (e) { /* bỏ qua */ } };
  BZ.showFlash = () => {
    try { const m = sessionStorage.getItem('bz.flash'); if (m) { sessionStorage.removeItem('bz.flash'); BZ.toast(m); } } catch (e) { /* bỏ qua */ }
  };

  BZ.confirm = ({ title, message, confirmText = 'Xác nhận', cancelText = 'Hủy', danger = false }) => new Promise((resolve) => {
    const dlg = document.getElementById('confirmDialog');
    dlg.querySelector('#cfTitle').textContent = title;
    dlg.querySelector('#cfMsg').textContent = message;
    const ok = dlg.querySelector('#cfOk');
    ok.textContent = confirmText;
    ok.className = 'btn ' + (danger ? 'btn-danger-solid' : 'btn-primary');
    dlg.querySelector('#cfCancel').textContent = cancelText;
    dlg.returnValue = 'cancel';
    dlg.addEventListener('close', () => resolve(dlg.returnValue === 'ok'), { once: true });
    dlg.showModal();
  });

  BZ.busy = (btn, on, label) => {
    if (!btn) return;
    if (on) {
      btn.dataset.html = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="spin" aria-hidden="true"></span><span>${BZ.esc(label || 'Đang xử lý…')}</span>`;
    } else {
      btn.disabled = false;
      if (btn.dataset.html != null) btn.innerHTML = btn.dataset.html;
    }
  };

  BZ.emptyState = ({ icon = 'inbox', title, text, actionHtml = '' }) =>
    `<div class="state">${BZ.icon(icon, 'ic-big')}<h3>${BZ.esc(title)}</h3><p>${BZ.esc(text || '')}</p>${actionHtml}</div>`;
  BZ.errorState = (message) =>
    `<div class="state error" role="alert">${BZ.icon('alert', 'ic-big')}<h3>Không tải được dữ liệu</h3><p>${BZ.esc(message)}</p><button type="button" class="btn btn-outline" data-retry>Thử lại</button></div>`;
  BZ.skeletonRows = (rows, cols) =>
    Array.from({ length: rows }, () => `<tr>${Array.from({ length: cols }, (_, i) => `<td><span class="skel" style="width:${i === 0 ? 70 : 45}%"></span></td>`).join('')}</tr>`).join('');

  BZ.readQuery = (keys) => {
    const p = new URLSearchParams(location.search);
    const out = {};
    keys.forEach((k) => { out[k] = p.get(k) || ''; });
    return out;
  };
  BZ.writeQuery = (obj) => {
    const p = new URLSearchParams();
    Object.entries(obj).forEach(([k, v]) => { if (v) p.set(k, v); });
    const qs = p.toString();
    history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
  };

  // danh mục địa điểm (bảng provinces/wards dùng chung)
  let provincesCache = null;
  const wardsCache = {};
  BZ.loadProvinces = async () => { if (!provincesCache) provincesCache = await BZ.api('/api/locations/provinces'); return provincesCache; };
  BZ.loadWards = async (code) => { if (!wardsCache[code]) wardsCache[code] = await BZ.api(`/api/locations/provinces/${encodeURIComponent(code)}/wards`); return wardsCache[code]; };

  // khung trang (sidebar, banner, nút đăng tin)
  BZ.refreshBadge = async () => {
    const badge = document.getElementById('navBadge');
    if (!badge) return;
    try {
      const stats = await BZ.api('/api/company/applications/stats');
      badge.textContent = stats.submitted > 99 ? '99+' : stats.submitted;
      badge.hidden = !stats.submitted;
      badge.setAttribute('aria-label', `${stats.submitted} hồ sơ mới`);
    } catch (e) { badge.hidden = true; }
  };

  function renderBanner(profile) {
    const slot = document.getElementById('bannerSlot');
    if (!slot) return;
    const isDefault = profile.company_name === BZ.DEFAULT_COMPANY_NAME;
    const onProfile = document.body.dataset.page === 'profile';
    const link = onProfile ? '' : ' <a href="/business/profile">Mở hồ sơ công ty</a>';
    let html = '';
    if (profile.approval_status === 'rejected') {
      const note = profile.review_note ? `Lý do: ${BZ.esc(profile.review_note)}. ` : '';
      html = `<div class="banner banner-danger" role="status">${BZ.icon('alert')}<div><b>Hồ sơ công ty chưa được duyệt</b>${note}Hãy chỉnh sửa và lưu lại để gửi duyệt lại.${link}</div></div>`;
    } else if (profile.approval_status === 'pending' && isDefault) {
      html = `<div class="banner banner-info" role="status">${BZ.icon('info')}<div><b>Hoàn thiện hồ sơ công ty để bắt đầu</b>Bạn cần điền tên công ty và chờ nhà trường duyệt trước khi đăng tin.${link}</div></div>`;
    } else if (profile.approval_status === 'pending') {
      html = `<div class="banner banner-warn" role="status">${BZ.icon('clock')}<div><b>Hồ sơ công ty đang chờ duyệt</b>Bạn sẽ đăng được tin sau khi nhà trường duyệt hồ sơ.${link}</div></div>`;
    }
    slot.innerHTML = html;
  }

  function lockNewJobButtons(profile) {
    const approved = profile.approval_status === 'approved';
    document.querySelectorAll('.js-new-job').forEach((a) => {
      if (approved) { a.removeAttribute('aria-disabled'); a.removeAttribute('title'); return; }
      a.setAttribute('aria-disabled', 'true');
      a.setAttribute('title', 'Cần được duyệt hồ sơ công ty trước khi đăng tin');
      a.style.opacity = '.55';
    });
  }

  BZ.init = async () => {
    // menu di động
    const sidebar = document.getElementById('sidebar');
    const scrim = document.getElementById('scrim');
    const menuBtn = document.getElementById('menuBtn');
    const setMenu = (open) => {
      sidebar.classList.toggle('open', open);
      scrim.hidden = !open;
      menuBtn.setAttribute('aria-expanded', String(open));
    };
    menuBtn.addEventListener('click', () => setMenu(!sidebar.classList.contains('open')));
    scrim.addEventListener('click', () => { if (sidebar.classList.contains('open')) setMenu(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && sidebar.classList.contains('open')) setMenu(false); });

    const logoutButton = document.getElementById('btnLogout');
    logoutButton.addEventListener('click', async () => {
      logoutButton.disabled = true;
      try {
        await BZ.api('/api/auth/logout', { method: 'POST', noRedirect: true });
        location.href = '/business/login';
      } catch (e) {
        BZ.toast(e.message, 'error');
        logoutButton.disabled = false;
      }
    });
    document.addEventListener('click', (e) => {
      const a = e.target.closest('.js-new-job[aria-disabled="true"]');
      if (a) { e.preventDefault(); BZ.toast('Cần được duyệt hồ sơ công ty trước khi đăng tin.', 'error'); }
    });
    BZ.showFlash();

    let profile = null;
    try {
      profile = await BZ.api('/api/company/profile');
    } catch (e) {
      if (e.status === 403) { location.href = '/business/login?reason=role'; throw e; }
      document.getElementById('sideCompany').textContent = 'Không tải được hồ sơ';
      BZ.toast(e.message, 'error');
      throw e;
    }
    BZ.profile = profile;
    document.getElementById('sideCompany').textContent = profile.company_name === BZ.DEFAULT_COMPANY_NAME ? 'Chưa đặt tên công ty' : profile.company_name;
    document.getElementById('sideEmail').textContent = profile.email || '';
    renderBanner(profile);
    lockNewJobButtons(profile);
    BZ.refreshBadge();
    return profile;
  };

  // Gắn nút "Thử lại" trong vùng trạng thái lỗi
  BZ.onRetry = (container, fn) => {
    container.addEventListener('click', (e) => { if (e.target.closest('[data-retry]')) fn(); });
  };
})();
