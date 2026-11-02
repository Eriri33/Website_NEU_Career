(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const TABS = [['', 'Tất cả'], ['approved', 'Đã duyệt'], ['pending', 'Chờ duyệt'], ['rejected', 'Bị từ chối'], ['closed', 'Đã đóng']];
  const state = { q: '', status: '', category_id: '', location: '', job_type: '', sort: 'latest' };
  let seq = 0;

  const hasFilters = () => Object.entries(state).some(([k, v]) => k !== 'sort' && v) || state.sort !== 'latest';

  function renderTabs(counts) {
    $('statusTabs').innerHTML = TABS.map(([v, label]) => {
      const n = counts ? (v ? counts[v] || 0 : counts.all) : '';
      return `<button type="button" role="tab" data-status="${v}" aria-selected="${state.status === v}">${label}<span class="n">${n}</span></button>`;
    }).join('');
  }

  async function loadCounts() {
    try {
      const all = await BZ.api('/api/company/jobs');
      const c = { all: all.length };
      all.forEach((j) => { c[j.status] = (c[j.status] || 0) + 1; });
      renderTabs(c);
    } catch (e) { /* tab vẫn dùng được không có số */ }
  }

  function statusCell(j) {
    let html;
    if (j.status === 'pending' && j.needs_re_review) html = BZ.chip('warn', 'Chờ duyệt lại');
    else if (j.status === 'approved' && j.is_expired) html = BZ.chip('closed', 'Hết hạn nộp');
    else html = BZ.chip(j.status, BZ.JOB_STATUS[j.status]);
    if (j.status === 'rejected' && j.review_note) html += `<div class="cell-sub" title="${BZ.esc(j.review_note)}">Lý do: ${BZ.esc(j.review_note.length > 70 ? j.review_note.slice(0, 70) + '…' : j.review_note)}</div>`;
    return html;
  }

  function row(j) {
    const apps = j.application_count
      ? `<a href="/business/applicants?job_id=${j.id}"><b>${j.application_count}</b> hồ sơ</a>${j.new_application_count ? `<div class="cell-sub">${BZ.chip('submitted', j.new_application_count + ' mới', 'chip-flat')}</div>` : ''}`
      : '<span class="muted">Chưa có</span>';
    return `<tr>
      <td data-label="Tin" class="no-label"><div class="cell-title"><a href="/business/jobs/${j.id}">${BZ.esc(j.title)}</a></div>
        <div class="chips-mini">${j.category_name ? `<span class="pill">${BZ.esc(j.category_name)}</span>` : ''}<span class="pill">${BZ.JOB_TYPE[j.job_type] || ''}</span><span class="pill">${BZ.esc(j.salary_text || 'Thỏa thuận')}</span></div></td>
      <td data-label="Địa điểm">${j.location ? BZ.esc(j.location) : '<span class="muted">Chưa nhập</span>'}</td>
      <td data-label="Hạn nộp">${BZ.deadlineHtml(j)}</td>
      <td data-label="Hồ sơ">${apps}</td>
      <td data-label="Trạng thái">${statusCell(j)}</td>
      <td class="no-label"><div class="row-actions">
        <a class="btn btn-ghost btn-sm" href="/business/jobs/${j.id}">Xem</a>
        <a class="btn btn-ghost btn-sm" href="/business/jobs/${j.id}/edit">Sửa</a>
        ${j.status !== 'closed' ? `<button type="button" class="btn btn-danger btn-sm" data-close="${j.id}" data-title="${BZ.esc(j.title)}">Đóng tin</button>` : ''}
      </div></td></tr>`;
  }

  async function load() {
    const my = ++seq;
    BZ.writeQuery(Object.fromEntries(Object.entries(state).filter(([k, v]) => v && !(k === 'sort' && v === 'latest'))));
    $('jobState').innerHTML = '';
    $('jobRows').innerHTML = BZ.skeletonRows(4, 6);
    $('resultBar').textContent = 'Đang tải…';
    try {
      const jobs = await BZ.api('/api/company/jobs', { query: state });
      if (my !== seq) return; // có truy vấn mới hơn
      $('jobRows').innerHTML = jobs.map(row).join('');
      $('resultBar').innerHTML = `<span>${jobs.length} tin${hasFilters() ? ' phù hợp bộ lọc' : ''}</span><span class="spacer"></span>${hasFilters() ? '<button type="button" class="linklike" id="btnClear">Xóa lọc</button>' : ''}`;
      if (!jobs.length) {
        $('jobState').innerHTML = hasFilters()
          ? BZ.emptyState({ icon: 'search', title: 'Không có tin phù hợp', text: 'Thử bỏ bớt bộ lọc hoặc dùng từ khóa khác.', actionHtml: '<button type="button" class="btn btn-outline" id="btnClear2">Xóa lọc</button>' })
          : BZ.emptyState({ icon: 'briefcase', title: 'Công ty chưa có tin tuyển dụng', text: 'Đăng tin đầu tiên để sinh viên NEU biết đến vị trí của bạn.', actionHtml: '<a class="btn btn-primary js-new-job" href="/business/jobs/new">Đăng tin mới</a>' });
      }
    } catch (e) {
      if (my !== seq) return;
      $('jobRows').innerHTML = '';
      $('resultBar').textContent = '';
      $('jobState').innerHTML = BZ.errorState(e.message);
    }
  }

  function syncForm() {
    $('fQ').value = state.q; $('fCategory').value = state.category_id; $('fType').value = state.job_type; $('fSort').value = state.sort;
    if ($('fLocation')) $('fLocation').value = state.location;
  }
  function clearAll() {
    Object.assign(state, { q: '', status: '', category_id: '', location: '', job_type: '', sort: 'latest' });
    syncForm(); renderTabs(); loadCounts(); load();
  }

  async function fillSelects() {
    try {
      const cats = await BZ.api('/api/company/categories');
      $('fCategory').insertAdjacentHTML('beforeend', cats.map((c) => `<option value="${c.id}">${BZ.esc(c.name)}</option>`).join(''));
    } catch (e) { /* bộ lọc danh mục vẫn trống */ }
    try {
      const provs = await BZ.loadProvinces();
      if (provs.length) $('fLocation').insertAdjacentHTML('beforeend', provs.map((p) => `<option value="${BZ.esc(p.name)}">${BZ.esc(p.name)}</option>`).join(''));
      else throw new Error('empty');
    } catch (e) {
      // Chưa nạp bảng provinces: cho nhập tay để bộ lọc vẫn dùng được.
      $('fLocationField').innerHTML = '<label for="fLocation">Địa điểm</label><input class="input" id="fLocation" placeholder="Nhập tỉnh/thành phố">';
    }
    syncForm();
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try { await BZ.init(); } catch (e) { return; }
    const initial = BZ.readQuery(Object.keys(state));
    Object.keys(state).forEach((k) => { if (initial[k]) state[k] = initial[k]; });
    renderTabs(); loadCounts();
    await fillSelects();
    load();

    $('filters').addEventListener('submit', (e) => e.preventDefault());
    const onQ = BZ.debounce(() => { state.q = $('fQ').value.trim(); load(); }, 350);
    $('fQ').addEventListener('input', onQ);
    const bind = (id, key) => document.addEventListener('change', (e) => { if (e.target.id === id) { state[key] = e.target.value.trim(); load(); } });
    bind('fCategory', 'category_id'); bind('fType', 'job_type'); bind('fSort', 'sort'); bind('fLocation', 'location');
    $('fLocation').addEventListener && $('fLocation').addEventListener('input', BZ.debounce((e) => { if (e.target.tagName === 'INPUT') { state.location = e.target.value.trim(); load(); } }, 350));

    $('statusTabs').addEventListener('click', (e) => {
      const b = e.target.closest('[data-status]'); if (!b) return;
      state.status = b.dataset.status;
      document.querySelectorAll('#statusTabs [role=tab]').forEach((t) => t.setAttribute('aria-selected', String(t === b)));
      load();
    });
    document.addEventListener('click', async (e) => {
      if (e.target.closest('#btnClear, #btnClear2')) { clearAll(); return; }
      if (e.target.closest('[data-retry]')) { load(); return; }
      const close = e.target.closest('[data-close]');
      if (!close) return;
      const ok = await BZ.confirm({ title: 'Đóng tin tuyển dụng?', message: `“${close.dataset.title}” sẽ không còn hiển thị với sinh viên. Hồ sơ đã nhận vẫn được giữ lại.`, confirmText: 'Đóng tin', danger: true });
      if (!ok) return;
      try { await BZ.api(`/api/company/jobs/${close.dataset.close}`, { method: 'DELETE' }); BZ.toast('Đã đóng tin tuyển dụng.'); loadCounts(); load(); }
      catch (err) { BZ.toast(err.message, 'error'); }
    });
  });
})();
