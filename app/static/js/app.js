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

const esc = s => (s || '').replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));

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
  state.innerHTML = '<div class="loading">Đang tìm cơ hội phù hợp…</div>';
  try {
    currentJobs = await api('/api/jobs?' + params());
    state.innerHTML = '';
    $('#resultTitle').textContent = currentJobs.length ? `${currentJobs.length} việc làm phù hợp` : 'Không có kết quả';
    renderJobs();
    // Update stat
    $('#statJobs').textContent = currentJobs.length;
  } catch (e) {
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

    // Category cards
    const totalJobs = categories.reduce((s, c) => s + c.job_count, 0);
    $('#statCategories').textContent = categories.length;

    $('#categories').innerHTML = categories.length
      ? categories.slice(0, 8).map((c, i) =>
          `<div class="category" onclick="chooseCategory(${c.id})">
            <span class="category-icon">${CATEGORY_ICONS[i % CATEGORY_ICONS.length]}</span>
            <b>${esc(c.name)}</b>
            <small>${c.job_count} vị trí đang tuyển</small>
          </div>`
        ).join('')
      : '<div class="empty">Chưa có dữ liệu danh mục.</div>';
  } catch (e) {
    $('#categories').innerHTML = '<div class="error">Không tải được danh mục.</div>';
  }
}

function chooseCategory(id) {
  $$('#categoryFilters input').forEach(x => x.checked = (x.value == id));
  $('#heroCategory').value = id;
  document.getElementById('jobs').scrollIntoView({ behavior: 'smooth' });
  loadJobs();
}

/* ===== SUGGESTIONS ===== */
async function loadSuggestions() {
  try {
    const d = await api('/api/jobs/suggestions');
    $('#keywordSuggestions').innerHTML = (d.keywords || []).map(k =>
      `<button type="button" class="keyword" onclick="useKeyword('${esc(k)}')">${esc(k)}</button>`
    ).join('') || '<span class="muted">Chưa có gợi ý</span>';

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
          </div>`
        ).join('')
      : '<span class="muted">Chưa có tin mới</span>';
  } catch (_) {
    $('#keywordSuggestions').innerHTML = '<span class="muted">Không tải được gợi ý</span>';
  }
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
    if (currentUser.role === 'student') loadApplications();
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
    $('#studentLink').hidden = me.role !== 'student';
    if (me.role === 'student') {
      $('#student').hidden = false;
      loadStudent();
    }
    $('#statCompanies').textContent = '—';
  } catch (_) {
    currentUser = null;
    $('#authButton').textContent = 'Đăng nhập';
    $('#authButton').href = '/login';
  }
}
/* ===== CAREER CONTENT ===== */
const CAREER_IMAGES = [
  '/static/assets/neu_3.jpg',
  '/static/assets/images_toa_A2.jpg',
  '/static/assets/images_thanxuan.jpg',
  '/static/assets/neu_2.jpg',
  '/static/assets/background1.webp'
];

async function loadCareer() {
  try {
    const items = await api('/api/career-contents');
    $('#careerCards').innerHTML = items.length
      ? items.map((x, i) =>
          `<article class="career-card" onclick="openCareer(${x.id})">
            <img src="${CAREER_IMAGES[i % CAREER_IMAGES.length]}" alt="${esc(x.title)}" loading="lazy">
            <div>
              <span class="career-tag">${esc(x.category)}</span>
              <h3>${esc(x.title)}</h3>
              <p>${esc(x.summary)}</p>
            </div>
          </article>`
        ).join('')
      : '<div class="empty">Nội dung hướng nghiệp đang được cập nhật.</div>';
  } catch (e) {
    $('#careerCards').innerHTML = '<div class="error">Không tải được nội dung hướng nghiệp.</div>';
  }
}

async function openCareer(id) {
  try {
    const c = await api('/api/career-contents/' + id);
    $('#modalContent').innerHTML = `
      <p class="eyebrow blue">${esc(c.category)}</p>
      <h2>${esc(c.title)}</h2>
      <p class="muted" style="margin-bottom:16px">${timeAgo(c.created_at)}</p>
      <hr>
      <div style="line-height:1.8;white-space:pre-line">${esc(c.body)}</div>
    `;
    $('#modal').hidden = false;
  } catch (e) {
    toast(e.message);
  }
}

/* ===== STUDENT SECTION ===== */
async function loadStudent() {
  try {
    const p = await api('/api/students/me');
    const f = $('#profileForm');
    ['full_name', 'major', 'phone', 'skills', 'bio'].forEach(k => {
      if (f.elements[k]) f.elements[k].value = p[k] || '';
    });

    // CVs
    const cvs = await api('/api/students/me/cvs');
    $('#cvList').innerHTML = cvs.length
      ? cvs.map(x =>
          `<div class="cv-item">
            <span>📄 ${esc(x.original_filename)} <span class="muted">(${timeAgo(x.created_at)})</span></span>
            <div style="display:flex;gap:6px">
              <button class="btn btn-soft btn-sm" onclick="downloadCv(${x.id})">⬇ Tải</button>
              <button class="btn btn-danger btn-sm" onclick="deleteCv(${x.id})">✕ Xóa</button>
            </div>
          </div>`
        ).join('')
      : '<p class="muted" style="padding:12px 0">Chưa có CV nào. Hãy tải lên CV đầu tiên của bạn!</p>';

    loadApplications();
  } catch (e) {
    toast(e.message);
  }
}

async function loadApplications() {
  const q = ($('#applicationQuery').value || '').trim();
  const s = $('#applicationStatus').value;
  try {
    const urlParams = new URLSearchParams();
    if (q) urlParams.set('q', q);
    if (s) urlParams.set('status', s);
    const a = await api('/api/applications/me?' + urlParams);
    $('#applicationList').innerHTML = a.length
      ? a.map(x => `
          <div class="application-item">
            <div class="app-info">
              <b>${esc(x.title)}</b>
              <span class="muted">${esc(x.company_name)} · ${timeAgo(x.created_at)}</span>
            </div>
            <span class="status-badge status-${x.status}">${STATUS_LABELS[x.status] || x.status}</span>
          </div>
        `).join('')
      : '<p class="muted" style="padding:12px 0">Chưa có đơn ứng tuyển nào.</p>';
  } catch (e) { /* silent */ }
}

async function downloadCv(id) {
  window.open('/api/students/me/cvs/' + id + '/download', '_blank');
}

async function deleteCv(id) {
  if (!confirm('Bạn có chắc muốn xóa CV này?')) return;
  try {
    await api('/api/students/me/cvs/' + id, { method: 'DELETE' });
    toast('Đã xóa CV.');
    loadStudent();
  } catch (e) {
    toast(e.message);
  }
}

/* ===== FILTER SAVE/LOAD ===== */
function saveFilters() {
  const filterData = Object.fromEntries(params());
  const name = prompt('Đặt tên cho bộ lọc (hoặc bỏ trống):', '') || 'Bộ lọc ' + new Date().toLocaleDateString('vi');
  const saved = JSON.parse(localStorage.getItem('careerConnect.savedJobFilters') || '[]');
  if (!Array.isArray(saved)) {
    // Migrate old format
    localStorage.setItem('careerConnect.savedJobFilters', JSON.stringify([{ name: 'Bộ lọc cũ', filters: saved }]));
  }
  const list = Array.isArray(saved) ? saved : [{ name: 'Bộ lọc cũ', filters: saved }];
  list.push({ name, filters: filterData });
  localStorage.setItem('careerConnect.savedJobFilters', JSON.stringify(list));
  toast('💾 Đã lưu bộ lọc "' + name + '"');
}

function loadSavedFilters() {
  const raw = localStorage.getItem('careerConnect.savedJobFilters');
  if (!raw) { toast('Chưa có bộ lọc nào được lưu.'); return; }
  let saved = JSON.parse(raw);
  // Handle old format (plain object)
  if (!Array.isArray(saved)) {
    applyFilterObject(saved);
    toast('Đã tải bộ lọc đã lưu.');
    return;
  }
  if (!saved.length) { toast('Chưa có bộ lọc nào được lưu.'); return; }

  // Show picker in modal
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
  const saved = JSON.parse(localStorage.getItem('careerConnect.savedJobFilters') || '[]');
  if (saved[index]) {
    applyFilterObject(saved[index].filters || saved[index]);
    toast('Đã áp dụng bộ lọc.');
    $('#modal').hidden = true;
  }
}

function deleteSavedFilter(index) {
  const saved = JSON.parse(localStorage.getItem('careerConnect.savedJobFilters') || '[]');
  saved.splice(index, 1);
  localStorage.setItem('careerConnect.savedJobFilters', JSON.stringify(saved));
  loadSavedFilters(); // re-render
}

function applyFilterObject(s) {
  Object.entries(s).forEach(([k, v]) => {
    const id = { q: 'query', job_type: 'jobType', saturday_policy: 'saturday', posted_within: 'posted' }[k] || k;
    if (k === 'category_ids') {
      String(v).split(',').forEach(x => {
        const b = $(`#categoryFilters input[value="${x}"]`);
        if (b) b.checked = true;
      });
    } else if ($('#' + id)) {
      $('#' + id).value = v;
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
    document.getElementById('jobs').scrollIntoView({ behavior: 'smooth' });
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

  $('#categoryFilters').addEventListener('change', loadJobs);

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
  };

  // Reset all filters
  $('#resetFilters').onclick = () => {
    ['query', 'location', 'major', 'skills'].forEach(id => $('#' + id).value = '');
    ['jobType', 'saturday', 'posted', 'heroCategory'].forEach(id => $('#' + id).value = '');
    $('#sort').value = 'latest';
    $$('#categoryFilters input').forEach(x => x.checked = false);
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
  $('#profileForm').onsubmit = async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.target));
    try {
      await api('/api/students/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      $('#profileMessage').textContent = '✅ Đã lưu hồ sơ thành công.';
      $('#profileMessage').style.color = 'var(--green)';
    } catch (err) {
      $('#profileMessage').textContent = err.message;
      $('#profileMessage').style.color = 'var(--red)';
    }
  };

  // CV upload
  const cvFileInput = $('#cvFileInput');
  const fileLabel = $('.file-label');
  if (cvFileInput && fileLabel) {
    cvFileInput.addEventListener('change', () => {
      fileLabel.textContent = cvFileInput.files.length
        ? cvFileInput.files[0].name
        : 'Chọn file CV (.pdf, .doc, .docx)';
    });
  }

  $('#cvForm').onsubmit = async e => {
    e.preventDefault();
    try {
      const r = await fetch('/api/students/me/cvs', { method: 'POST', body: new FormData(e.target) });
      if (!r.ok) throw Error((await r.json()).message);
      toast('📄 Đã tải CV lên thành công!');
      e.target.reset();
      if (fileLabel) fileLabel.textContent = 'Chọn file CV (.pdf, .doc, .docx)';
      loadStudent();
    } catch (err) {
      toast(err.message);
    }
  };

  // Application search/filter
  let appDebounce;
  $('#applicationQuery').addEventListener('input', () => {
    clearTimeout(appDebounce);
    appDebounce = setTimeout(loadApplications, 300);
  });
  $('#applicationStatus').onchange = loadApplications;

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
  loadCategories();
  loadJobs();
  loadCareer();
  checkSession();
});
