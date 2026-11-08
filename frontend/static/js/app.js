/* ===== Career Connect — TV1 Frontend ===== */
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];

const api = async (url, opt = {}) => {
  const r = await fetch(url, { credentials: 'same-origin', ...opt });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw Error(data.message || 'Không thể kết nối máy chủ.');
  return data;
};

const toast = m => {
  const el = $('#toast');
  el.textContent = m;
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 3200);
};

const esc = s => String(s ?? '').replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));

const JOB_TYPE_LABELS = {
  internship: 'Thực tập', full_time: 'Toàn thời gian',
  part_time: 'Bán thời gian', contract: 'Hợp đồng'
};

const STATUS_LABELS = {
  submitted: 'Đã gửi', reviewing: 'Đang xem xét',
  accepted: 'Đã nhận', rejected: 'Từ chối', withdrawn: 'Đã rút'
};

const CATEGORY_ICONS = ['💼', '📊', '💻', '🎨', '📈', '🔬', '📱', '🏗️', '🎓', '⚙️', '📝', '🌐'];

let categories = [];
let currentJobs = [];
let currentUser = null;
let jobsRequestId = 0;

/* ===== QUERY PARAMS BUILDER ===== */
function params() {
  const p = new URLSearchParams();
  const q = $('#query').value.trim();
  const loc = $('#location').value.trim();
  if (q) p.set('q', q);
  if (loc) p.set('location', loc);
  const ids = $$('#categoryFilters input:checked').map(x => x.value);
  if (ids.length) p.set('category_ids', ids.join(','));
  if ($('#jobType').value) p.set('job_type', $('#jobType').value);
  if ($('#major').value.trim()) p.set('major', $('#major').value.trim());
  if ($('#skills').value.trim()) p.set('skills', $('#skills').value.trim());
  if ($('#saturday').value) p.set('saturday_policy', $('#saturday').value);
  if ($('#posted').value) p.set('posted_within', $('#posted').value);
  p.set('sort', $('#sort').value);
  return p;
}

/* ===== TIME HELPERS ===== */
function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr.replace(' ', 'T') + 'Z').getTime();
  const days = Math.floor(diff / 86400000);
  if (days < 1) return 'Hôm nay';
  if (days === 1) return 'Hôm qua';
  if (days < 30) return `${days} ngày trước`;
  return dateStr.split(' ')[0];
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const diff = new Date(dateStr) - new Date();
  return Math.ceil(diff / 86400000);
}

/* ===== RENDER JOBS ===== */
function renderJobs() {
  const box = $('#jobResults');
  if (!currentJobs.length) {
    box.innerHTML = '<div class="empty">Không tìm thấy việc làm phù hợp. Hãy thử nới rộng bộ lọc.</div>';
    return;
  }
  box.innerHTML = currentJobs.map(j => {
    const days = daysUntil(j.deadline);
    const deadlineText = j.deadline
      ? (days !== null && days >= 0 ? `Còn ${days} ngày` : 'Hết hạn')
      : 'Không giới hạn';
    const salary = j.salary_text || 'Thỏa thuận';
    return `<article class="job-card">
      <div>
        <h3>${esc(j.title)}</h3>
        <span class="company">${esc(j.company_name)}</span>
        <div class="job-meta">
          <span>📍 ${esc(j.location) || 'Chưa cập nhật'}</span>
          <span>📂 ${esc(j.category_name) || 'Khác'}</span>
          <span>⏰ ${JOB_TYPE_LABELS[j.job_type] || j.job_type}</span>
          <span>🕐 ${timeAgo(j.created_at)}</span>
        </div>
      </div>
      <div class="job-aside">
        <span class="salary">${esc(salary)}</span>
        <span class="deadline-badge">${deadlineText}</span>
        <button class="btn btn-soft btn-sm" onclick="openJob(${j.id})">Xem chi tiết</button>
      </div>
    </article>`;
  }).join('');
}

/* ===== LOAD JOBS ===== */
async function loadJobs() {
  const state = $('#resultState');
  const requestId = ++jobsRequestId;
  state.innerHTML = '<div class="loading">Đang tìm cơ hội phù hợp…</div>';
  try {
    const jobs = await api('/api/jobs?' + params());
    if (requestId !== jobsRequestId) return; // đã có lần tìm mới hơn
    currentJobs = jobs;
    state.innerHTML = '';
    $('#resultTitle').textContent = currentJobs.length ? `${currentJobs.length} việc làm phù hợp` : 'Không có kết quả';
    renderJobs();
  } catch (e) {
    if (requestId !== jobsRequestId) return;
    state.innerHTML = `<div class="error">${esc(e.message)} <button class="text-button" onclick="loadJobs()">Thử lại</button></div>`;
    $('#jobResults').innerHTML = '';
  }
}

/* ===== LOAD CATEGORIES ===== */
async function loadCategories() {
  try {
    categories = await api('/api/jobs/categories');
    // Hero category dropdown
    const option = categories.map(c => `<option value="${c.id}">${esc(c.name)}</option>`).join('');
    $('#heroCategory').insertAdjacentHTML('beforeend', option);

    // Sidebar checkboxes
    $('#categoryFilters').innerHTML = categories.map(c =>
      `<label><input type="checkbox" value="${c.id}"> ${esc(c.name)} <span class="muted">(${c.job_count})</span></label>`
    ).join('') || '<span class="muted">Chưa có danh mục</span>';

    $('#statCategories').textContent = categories.length;
  } catch (e) {
    $('#categoryFilters').innerHTML = `<div class="error">${esc(e.message)}</div>`;
  }
}

/* TV2 owns the province/ward dataset; TV1 reuses it for public search. */
async function loadLocationOptions() {
  try {
    const provinces = await api('/api/locations/provinces');
    $('#locationOptions').innerHTML = provinces.map(p =>
      `<option value="${esc(p.name)}"></option>`
    ).join('');
  } catch (_) {
    // Free-text location search remains available if the shared dataset is unavailable.
  }
}

function chooseCategory(id) {
  $$('#categoryFilters input').forEach(x => x.checked = (x.value == id));
  $('#heroCategory').value = id;
  loadJobs();
}

/* ===== SUGGESTIONS ===== */
async function loadSuggestions() {
  try {
    const d = await api('/api/jobs/suggestions');
    $('#keywordSuggestions').innerHTML = (d.keywords || []).map(k =>
      `<button type="button" class="keyword" data-keyword="${esc(k)}">${esc(k)}</button>`
    ).join('') || '<span class="muted">Chưa có gợi ý</span>';

    renderStats(d.stats);

    // If student is logged in, try to load recommendations instead
    let jobs = d.jobs || [];
    if (currentUser && currentUser.role === 'student') {
      try {
        const recs = await api('/api/students/me/recommendations');
        if (recs.length > 0) jobs = recs.slice(0, 6);
      } catch (_) { /* fallback to suggestions */ }
    }

    $('#jobSuggestions').innerHTML = jobs.length
      ? jobs.map(j =>
          `<div class="mini-job" onclick="openJob(${j.id})">
            <b>${esc(j.title)}</b>
            <small>${esc(j.company_name)} · ${esc(j.location) || 'Chưa rõ'}</small>
            ${j.salary_text ? `<span class="salary">${esc(j.salary_text)}</span>` : ''}
          </div>`
        ).join('')
      : '<span class="muted">Chưa có tin mới</span>';
  } catch (_) {
    $('#keywordSuggestions').innerHTML = '<span class="muted">Không tải được gợi ý</span>';
  }
}

function renderStats(stats) {
  if (!stats) return;
  $('#statJobs').textContent = stats.total_jobs;
  $('#statCompanies').textContent = stats.total_companies;
}

function useKeyword(k) {
  $('#query').value = k;
  $('#suggestions').hidden = true;
  loadJobs();
}

/* ===== JOB DETAIL MODAL ===== */
async function openJob(id) {
  try {
    const j = await api('/api/jobs/' + id);
    const days = daysUntil(j.deadline);
    const deadlineText = j.deadline
      ? (days !== null && days >= 0 ? `${j.deadline} (còn ${days} ngày)` : `${j.deadline} (đã hết hạn)`)
      : 'Không giới hạn';

    const saturdayLabels = { off: 'Nghỉ thứ Bảy', working: 'Làm thứ Bảy', negotiable: 'Thỏa thuận', unknown: 'Chưa rõ' };

    $('#modalContent').innerHTML = `
      <div class="job-detail-header">
        <p class="eyebrow blue">${esc(j.category_name) || 'CƠ HỘI NGHỀ NGHIỆP'}</p>
        <h2>${esc(j.title)}</h2>
        <span class="company">${esc(j.company_name)}</span>
      </div>
      <div class="job-detail-tags">
        <span class="detail-tag">📍 ${esc(j.location) || 'Chưa cập nhật'}</span>
        <span class="detail-tag">💰 ${esc(j.salary_text) || 'Thỏa thuận'}</span>
        <span class="detail-tag">⏰ ${JOB_TYPE_LABELS[j.job_type] || j.job_type}</span>
        <span class="detail-tag">📅 ${deadlineText}</span>
        <span class="detail-tag">🗓️ ${saturdayLabels[j.saturday_policy] || 'Chưa rõ'}</span>
      </div>
      <hr>
      <div class="detail-section">
        <h4>📋 Mô tả công việc</h4>
        <p>${esc(j.description)}</p>
      </div>
      <div class="detail-section">
        <h4>🎓 Ngành phù hợp</h4>
        <p>${esc(j.major_required) || 'Không giới hạn'}</p>
      </div>
      <div class="detail-section">
        <h4>🛠️ Kỹ năng yêu cầu</h4>
        <p>${esc(j.skills_required) || 'Chưa cập nhật'}</p>
      </div>
      ${j.company_description ? `<div class="detail-section"><h4>🏢 Về doanh nghiệp</h4><p>${esc(j.company_description)}</p></div>` : ''}
      ${j.company_website ? `<div class="detail-section"><h4>🌐 Website</h4><p><a href="${esc(j.company_website)}" target="_blank" style="color:var(--blue)">${esc(j.company_website)}</a></p></div>` : ''}
      <hr>
      <div class="apply-section">
        <h4>✍️ Ứng tuyển vào vị trí này</h4>
        <textarea id="coverLetter" placeholder="Lời nhắn cho nhà tuyển dụng (không bắt buộc)..."></textarea>
        <button class="btn btn-primary" onclick="applyJob(${j.id})">🚀 Ứng tuyển ngay</button>
      </div>
    `;
    $('#modal').hidden = false;
  } catch (e) {
    toast(e.message);
  }
}

/* ===== APPLY JOB ===== */
async function applyJob(id) {
  if (!currentUser) {
    location.href = '/login';
    toast('Bạn cần đăng nhập để ứng tuyển.');
    return;
  }
  if (currentUser.role !== 'student') {
    toast('Chỉ sinh viên mới có thể ứng tuyển.');
    return;
  }
  try {
    const coverLetter = ($('#coverLetter') || {}).value || '';
    const d = await api('/api/applications/jobs/' + id, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cover_letter: coverLetter })
    });
    toast('🎉 ' + d.message);
    $('#modal').hidden = true;
  } catch (e) {
    toast(e.message);
  }
}

/* ===== AUTH ===== */
async function checkSession() {
  try {
    const me = await api('/api/auth/me');
    currentUser = me;
    $('#sessionLabel').textContent = me.email;
    $('#authButton').textContent = 'Tài khoản';
    $('#authButton').href = '/dashboard';
  } catch (_) {
    currentUser = null;
    $('#authButton').textContent = 'Đăng nhập';
    $('#authButton').href = '/login';
  }
}

/* ===== FILTER SAVE/LOAD ===== */
const SAVED_FILTERS_KEY = 'careerConnect.savedJobFilters';

/* Luôn trả về mảng [{name, filters}]; chấp nhận định dạng cũ (object phẳng) và dữ liệu hỏng. */
function readSavedFilters() {
  try {
    const saved = JSON.parse(localStorage.getItem(SAVED_FILTERS_KEY) || '[]');
    if (Array.isArray(saved)) return saved.filter(x => x && typeof x === 'object');
    if (saved && typeof saved === 'object') return [{ name: 'Bộ lọc cũ', filters: saved }];
  } catch (_) { /* dữ liệu hỏng -> coi như chưa có */ }
  return [];
}

function writeSavedFilters(list) {
  try {
    localStorage.setItem(SAVED_FILTERS_KEY, JSON.stringify(list));
    return true;
  } catch (_) {
    toast('Không lưu được bộ lọc trên trình duyệt này.');
    return false;
  }
}

function saveFilters() {
  const filterData = Object.fromEntries(params());
  const name = (prompt('Đặt tên cho bộ lọc (hoặc bỏ trống):', '') || '').trim()
    || 'Bộ lọc ' + new Date().toLocaleDateString('vi');
  const list = readSavedFilters();
  list.push({ name, filters: filterData });
  if (writeSavedFilters(list)) toast('💾 Đã lưu bộ lọc "' + name + '"');
}

function loadSavedFilters() {
  const saved = readSavedFilters();
  if (!saved.length) { toast('Chưa có bộ lọc nào được lưu.'); return; }

  $('#modalContent').innerHTML = `
    <h2>📂 Bộ lọc đã lưu</h2>
    <hr>
    <div style="display:grid;gap:8px">
      ${saved.map((s, i) => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;border:1px solid var(--line);border-radius:8px">
          <span><b>${esc(s.name)}</b></span>
          <div style="display:flex;gap:6px">
            <button class="btn btn-soft btn-sm" onclick="applySavedFilter(${i})">Áp dụng</button>
            <button class="btn btn-danger btn-sm" onclick="deleteSavedFilter(${i})">Xóa</button>
          </div>
        </div>
      `).join('')}
    </div>
  `;
  $('#modal').hidden = false;
}

function applySavedFilter(index) {
  const item = readSavedFilters()[index];
  if (!item) return;
  applyFilterObject(item.filters || {});
  toast('Đã áp dụng bộ lọc.');
  $('#modal').hidden = true;
}

function deleteSavedFilter(index) {
  const list = readSavedFilters();
  list.splice(index, 1);
  writeSavedFilters(list);
  if (list.length) loadSavedFilters(); // vẽ lại danh sách
  else { $('#modal').hidden = true; toast('Đã xóa bộ lọc.'); }
}

/* Đặt lại toàn bộ filter về mặc định (dùng chung cho nút Xóa lọc và khi áp dụng bộ lọc đã lưu). */
function resetFilterControls() {
  ['query', 'location', 'major', 'skills'].forEach(id => $('#' + id).value = '');
  ['jobType', 'saturday', 'posted', 'heroCategory'].forEach(id => $('#' + id).value = '');
  $('#sort').value = 'latest';
  $$('#categoryFilters input').forEach(x => x.checked = false);
}

function applyFilterObject(s) {
  resetFilterControls(); // không cộng dồn với filter đang chọn
  const ids = { q: 'query', job_type: 'jobType', saturday_policy: 'saturday', posted_within: 'posted' };
  Object.entries(s).forEach(([k, v]) => {
    if (k === 'category_ids') {
      const chosen = String(v).split(',').filter(Boolean);
      chosen.forEach(x => {
        const b = $(`#categoryFilters input[value="${CSS.escape(x)}"]`);
        if (b) b.checked = true;
      });
      $('#heroCategory').value = chosen.length === 1 ? chosen[0] : '';
    } else {
      const el = $('#' + (ids[k] || k));
      if (el && 'value' in el) el.value = v;
    }
  });
  loadJobs();
}

/* ===== EVENT LISTENERS ===== */
document.addEventListener('DOMContentLoaded', () => {
  // Search form
  $('#searchForm').onsubmit = e => {
    e.preventDefault();
    $('#suggestions').hidden = true;
    loadJobs();
  };

  // Filter changes trigger search
  ['jobType', 'saturday', 'posted', 'sort'].forEach(id =>
    $('#' + id).addEventListener('change', loadJobs)
  );

  // Debounce text inputs
  let debounceTimer;
  ['major', 'skills'].forEach(id => {
    $('#' + id).addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(loadJobs, 400);
    });
  });

  $('#categoryFilters').addEventListener('change', () => {
    const checked = $$('#categoryFilters input:checked');
    $('#heroCategory').value = checked.length === 1 ? checked[0].value : '';
    loadJobs();
  });

  // Hero category -> sidebar sync
  $('#heroCategory').onchange = e => {
    const val = e.target.value;
    $$('#categoryFilters input').forEach(x => x.checked = false);
    if (val) chooseCategory(val);
    else loadJobs();
  };

  // Clear search inputs
  $('#clearSearch').onclick = () => {
    $('#query').value = '';
    $('#location').value = '';
    $('#query').focus();
  };

  // Reset all filters
  $('#resetFilters').onclick = () => {
    resetFilterControls();
    loadJobs();
  };

  // Save / Load filters
  $('#saveFilters').onclick = saveFilters;
  $('#loadFilters').onclick = loadSavedFilters;

  // Suggestions dropdown
  let suggestionsVisible = false;
  $('#query').addEventListener('focus', () => {
    $('#suggestions').hidden = false;
    suggestionsVisible = true;
    loadSuggestions();
  });
  $('#location').addEventListener('focus', () => {
    $('#suggestions').hidden = true;
    suggestionsVisible = false;
  });

  $('#query').addEventListener('input', () => {
    if ($('#suggestions').hidden) {
      $('#suggestions').hidden = false;
      suggestionsVisible = true;
      loadSuggestions();
    }
  });
  $('#keywordSuggestions').addEventListener('click', e => {
    const btn = e.target.closest('[data-keyword]');
    if (btn) useKeyword(btn.dataset.keyword);
  });

  document.addEventListener('click', e => {
    if (suggestionsVisible && !e.target.closest('.suggestions') && !e.target.closest('#query')) {
      $('#suggestions').hidden = true;
      suggestionsVisible = false;
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      $('#suggestions').hidden = true;
      suggestionsVisible = false;
      $('#modal').hidden = true;
    }
  });


  // Job detail modal
  $('#closeModal').onclick = () => $('#modal').hidden = true;
  $('#modal').onclick = e => { if (e.target === $('#modal')) $('#modal').hidden = true; };
  // Student profile
  // Smooth scroll for nav links
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // ===== INIT =====
  const initialParams = new URLSearchParams(location.search);
  ['q', 'location', 'job_type', 'major', 'skills', 'saturday_policy', 'posted_within', 'sort'].forEach(key => {
    const controlId = {
      q: 'query',
      job_type: 'jobType',
      saturday_policy: 'saturday',
      posted_within: 'posted'
    }[key] || key;
    const value = initialParams.get(key);
    if (value !== null && $('#' + controlId)) $('#' + controlId).value = value;
  });
  loadCategories().then(() => {
    const selectedIds = (initialParams.get('category_ids') || '').split(',').filter(Boolean);
    selectedIds.forEach(id => {
      const checkbox = $(`#categoryFilters input[value="${CSS.escape(id)}"]`);
      if (checkbox) checkbox.checked = true;
    });
    $('#heroCategory').value = selectedIds.length === 1 ? selectedIds[0] : '';
    loadJobs();
  });
  loadLocationOptions();
  loadSuggestions();
  checkSession();
});
