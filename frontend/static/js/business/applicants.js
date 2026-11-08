(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const TABS = [['', 'Tất cả'], ['submitted', 'Mới nộp'], ['reviewing', 'Đang xem xét'], ['accepted', 'Đã nhận'], ['rejected', 'Từ chối'], ['withdrawn', 'Đã rút']];
  const state = { q: '', job_id: '', status: '', sort: 'latest' };
  let seq = 0, openId = null, opener = null, drawerData = null;

  const hasFilters = () => !!(state.q || state.job_id || state.status || state.sort !== 'latest');

  function renderTabs(stats) {
    $('statusTabs').innerHTML = TABS.map(([v, label]) => {
      const n = stats ? (v ? stats[v] : stats.total) : '';
      return `<button type="button" role="tab" data-status="${v}" aria-selected="${state.status === v}">${label}<span class="n">${n}</span></button>`;
    }).join('');
  }
  async function loadStats() {
    try { renderTabs(await BZ.api('/api/company/applications/stats', { query: { job_id: state.job_id, q: state.q } })); } catch (e) { renderTabs(); }
    BZ.refreshBadge();
  }

  // Nút thao tác nhanh theo trạng thái hiện tại
  function quickActions(a) {
    const b = (st, label, cls) => `<button type="button" class="btn btn-sm ${cls}" data-set="${st}" data-id="${a.application_id}">${label}</button>`;
    switch (a.status) {
      case 'submitted': return b('reviewing', 'Xem xét', 'btn-outline') + b('rejected', 'Từ chối', 'btn-danger');
      case 'reviewing': return b('accepted', 'Nhận', 'btn-outline') + b('rejected', 'Từ chối', 'btn-danger');
      case 'accepted': case 'rejected': return b('reviewing', 'Đưa về xem xét', 'btn-ghost');
      default: return '<span class="muted">Ứng viên đã rút</span>';
    }
  }

  function row(a) {
    const name = a.full_name || '(Chưa cập nhật tên)';
    const skills = BZ.splitList(a.skills).slice(0, 4).map((s) => `<span class="pill">${BZ.esc(s)}</span>`).join('');
    return `<tr class="clickable" data-open="${a.application_id}">
      <td class="no-label"><div class="cand"><div class="avatar">${BZ.esc(BZ.initials(a.full_name || a.email))}</div>
        <div style="min-width:0"><button type="button" class="linklike name" data-open-btn="${a.application_id}">${BZ.esc(name)}</button><div class="cell-sub truncate">${BZ.esc(a.email)}</div></div></div></td>
      <td data-label="Ngành">${a.major ? BZ.esc(a.major) : '<span class="muted">Chưa cập nhật</span>'}${skills ? `<div class="chips-mini">${skills}</div>` : ''}</td>
      <td data-label="Ứng tuyển"><a href="/business/jobs/${a.job_id}">${BZ.esc(a.title)}</a></td>
      <td data-label="Nộp lúc" title="${BZ.fmtDateTime(a.created_at)}">${BZ.relTime(a.created_at)}</td>
      <td data-label="Trạng thái">${BZ.chip(a.status, BZ.APP_STATUS[a.status])}</td>
      <td class="no-label"><div class="row-actions">${quickActions(a)}</div></td></tr>`;
  }

  async function load() {
    const my = ++seq;
    BZ.writeQuery({ ...state, sort: state.sort === 'latest' ? '' : state.sort });
    $('appState').innerHTML = '';
    $('appRows').innerHTML = BZ.skeletonRows(5, 6);
    $('resultBar').textContent = 'Đang tải…';
    try {
      const apps = await BZ.api('/api/company/applications', { query: state });
      if (my !== seq) return;
      $('appRows').innerHTML = apps.map(row).join('');
      $('resultBar').innerHTML = `<span>${apps.length} hồ sơ${hasFilters() ? ' phù hợp bộ lọc' : ''}</span><span class="spacer"></span>${hasFilters() ? '<button type="button" class="linklike" id="btnClear">Xóa lọc</button>' : ''}`;
      if (!apps.length) {
        $('appState').innerHTML = hasFilters()
          ? BZ.emptyState({ icon: 'search', title: 'Không có hồ sơ phù hợp', text: 'Thử bỏ bớt bộ lọc hoặc tìm bằng từ khóa khác.', actionHtml: '<button type="button" class="btn btn-outline" id="btnClear2">Xóa lọc</button>' })
          : BZ.emptyState({ icon: 'users', title: 'Chưa có hồ sơ ứng tuyển', text: 'Khi sinh viên ứng tuyển vào tin của công ty, hồ sơ sẽ hiện ở đây.', actionHtml: '<a class="btn btn-primary" href="/business/jobs">Xem tin tuyển dụng</a>' });
      }
    } catch (e) {
      if (my !== seq) return;
      $('appRows').innerHTML = ''; $('resultBar').textContent = '';
      $('appState').innerHTML = BZ.errorState(e.message);
    }
  }
  const reload = () => { loadStats(); load(); };

  // cập nhật trạng thái
  async function setStatus(id, status, btn) {
    if (status === 'accepted' || status === 'rejected') {
      const ok = await BZ.confirm({
        title: status === 'accepted' ? 'Nhận ứng viên này?' : 'Từ chối ứng viên này?',
        message: 'Sinh viên sẽ thấy trạng thái mới trong lịch sử ứng tuyển của họ. Bạn vẫn có thể đổi lại sau.',
        confirmText: status === 'accepted' ? 'Nhận ứng viên' : 'Từ chối', danger: status === 'rejected',
      });
      if (!ok) return;
    }
    BZ.busy(btn, true, 'Đang lưu…');
    try {
      await BZ.api(`/api/company/applications/${id}/status`, { method: 'PATCH', body: { status } });
      BZ.toast(`Đã chuyển sang “${BZ.APP_STATUS[status]}”.`);
      reload();
      if (openId === Number(id)) openDrawer(id, true);
    } catch (e) {
      BZ.busy(btn, false);
      BZ.toast(e.message, 'error');
      if (e.status === 409 || e.status === 404) reload();
    }
  }

  // drawer chi tiết
  const drawer = () => $('drawer');
  function closeDrawer() {
    drawer().classList.remove('open'); drawer().setAttribute('aria-hidden', 'true'); $('scrim').hidden = true;
    openId = null; drawerData = null;
    const p = new URLSearchParams(location.search); if (p.has('open')) { p.delete('open'); history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p : '')); }
    if (opener && document.contains(opener)) opener.focus();
  }
  async function openDrawer(id, keepFocus) {
    openId = Number(id);
    drawer().classList.add('open'); drawer().setAttribute('aria-hidden', 'false'); $('scrim').hidden = false;
    if (!keepFocus) $('drawerClose').focus();
    $('drawerBody').innerHTML = '<span class="skel" style="width:60%"></span><span class="skel" style="width:90%"></span><span class="skel" style="width:75%"></span>';
    $('drawerFoot').innerHTML = '';
    try {
      const d = await BZ.api(`/api/company/applications/${id}`);
      if (openId !== Number(id)) return;
      drawerData = d;
      renderDrawer(d);
    } catch (e) {
      $('drawerBody').innerHTML = e.status === 404 ? BZ.emptyState({ icon: 'search', title: 'Không tìm thấy hồ sơ', text: 'Hồ sơ không tồn tại hoặc không thuộc công ty của bạn.' }) : BZ.errorState(e.message);
    }
  }
  function renderDrawer(d) {
    $('drawerAvatar').textContent = BZ.initials(d.full_name || d.email);
    $('drawerTitle').textContent = d.full_name || '(Chưa cập nhật tên)';
    $('drawerSub').textContent = `Ứng tuyển ${d.title}`;
    const skills = BZ.splitList(d.skills).map((s) => `<span class="pill">${BZ.esc(s)}</span>`).join(' ') || '<span class="muted">Chưa cập nhật</span>';
    $('drawerBody').innerHTML = `
      <div>${BZ.chip(d.status, BZ.APP_STATUS[d.status])}</div>
      <dl class="dl">
        <dt>Email</dt><dd><a href="mailto:${BZ.esc(d.email)}">${BZ.esc(d.email)}</a></dd>
        <dt>Điện thoại</dt><dd>${d.phone ? `<a href="tel:${BZ.esc(d.phone)}">${BZ.esc(d.phone)}</a>` : '<span class="muted">Chưa cập nhật</span>'}</dd>
        <dt>Ngành học</dt><dd>${d.major ? BZ.esc(d.major) : '<span class="muted">Chưa cập nhật</span>'}</dd>
        <dt>Kỹ năng</dt><dd><div class="chips-mini" style="margin:0">${skills}</div></dd>
        <dt>Vị trí</dt><dd><a href="/business/jobs/${d.job_id}">${BZ.esc(d.title)}</a></dd>
        <dt>Nộp lúc</dt><dd>${BZ.fmtDateTime(d.created_at)}</dd>
        <dt>Cập nhật</dt><dd>${BZ.fmtDateTime(d.updated_at)}</dd>
      </dl>
      <div><h3 class="section-title" style="font-size:14px">Thư ứng tuyển</h3>${d.cover_letter ? `<div class="letter">${BZ.esc(d.cover_letter)}</div>` : '<p class="muted" style="margin:0">Ứng viên không để lại lời nhắn.</p>'}</div>
      ${d.bio ? `<div><h3 class="section-title" style="font-size:14px">Giới thiệu bản thân</h3><div class="letter">${BZ.esc(d.bio)}</div></div>` : ''}`;
    if (d.status === 'withdrawn') {
      $('drawerFoot').innerHTML = `<div class="banner banner-info" style="margin:0">${BZ.icon('info')}<div>Ứng viên đã rút đơn nên không thể cập nhật trạng thái.</div></div>`;
      return;
    }
    const btn = (st, label, cls) => `<button type="button" class="btn ${cls}" data-set="${st}" data-id="${d.application_id}" aria-pressed="${d.status === st}" ${d.status === st ? 'disabled' : ''}>${label}</button>`;
    $('drawerFoot').innerHTML = `<div class="muted" style="margin-bottom:8px;font-size:13px">Cập nhật trạng thái</div><div class="status-actions">${btn('reviewing', 'Đang xem xét', 'btn-outline')}${btn('accepted', 'Nhận ứng viên', 'btn-success')}${btn('rejected', 'Từ chối', 'btn-danger')}</div>`;
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try { await BZ.init(); } catch (e) { return; }
    const init = BZ.readQuery(['q', 'job_id', 'status', 'sort', 'open']);
    ['q', 'job_id', 'status', 'sort'].forEach((k) => { if (init[k]) state[k] = init[k]; });
    $('fQ').value = state.q; $('fSort').value = state.sort;
    renderTabs();
    try {
      const jobs = await BZ.api('/api/company/jobs');
      $('fJob').insertAdjacentHTML('beforeend', jobs.map((j) => `<option value="${j.id}">${BZ.esc(j.title)}${j.status === 'closed' ? ' (đã đóng)' : ''}</option>`).join(''));
      $('fJob').value = state.job_id;
    } catch (e) { /* bộ lọc tin vẫn trống */ }
    loadStats(); load();
    if (init.open) openDrawer(init.open);

    $('filters').addEventListener('submit', (e) => e.preventDefault());
    $('fQ').addEventListener('input', BZ.debounce(() => { state.q = $('fQ').value.trim(); reload(); }, 350));
    $('fJob').addEventListener('change', () => { state.job_id = $('fJob').value; reload(); });
    $('fSort').addEventListener('change', () => { state.sort = $('fSort').value; load(); });
    $('statusTabs').addEventListener('click', (e) => {
      const b = e.target.closest('[data-status]'); if (!b) return;
      state.status = b.dataset.status;
      document.querySelectorAll('#statusTabs [role=tab]').forEach((t) => t.setAttribute('aria-selected', String(t === b)));
      load();
    });
    $('drawerClose').addEventListener('click', closeDrawer);
    $('scrim').addEventListener('click', () => { if (drawer().classList.contains('open')) closeDrawer(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && drawer().classList.contains('open') && !$('confirmDialog').open) closeDrawer(); });

    document.addEventListener('click', (e) => {
      if (e.target.closest('#btnClear, #btnClear2')) {
        Object.assign(state, { q: '', job_id: '', status: '', sort: 'latest' });
        $('fQ').value = ''; $('fJob').value = ''; $('fSort').value = 'latest'; renderTabs(); reload(); return;
      }
      if (e.target.closest('[data-retry]')) { openId && !drawerData ? openDrawer(openId) : load(); return; }
      const set = e.target.closest('[data-set]');
      if (set) { e.stopPropagation(); setStatus(set.dataset.id, set.dataset.set, set); return; }
      if (e.target.closest('a, button') && !e.target.closest('[data-open-btn]')) return;
      const tr = e.target.closest('tr[data-open]');
      if (tr) { opener = tr.querySelector('[data-open-btn]'); openDrawer(tr.dataset.open); }
    });
  });
})();
