const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));
const statusLabels = {
  submitted: 'Đã gửi',
  reviewing: 'Đang xem xét',
  accepted: 'Đã nhận',
  rejected: 'Từ chối',
  withdrawn: 'Đã rút'
};

let profile;
let cvs = [];
let currentApplication = null;
let applicationTimer;
let toastTimer;

async function api(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || 'Không thể kết nối máy chủ.');
  return data;
}

function toast(message) {
  const element = $('#toast');
  element.textContent = message;
  element.style.display = 'block';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { element.style.display = 'none'; }, 3200);
}

function timeAgo(value) {
  if (!value) return '';
  const timestamp = new Date(value.replace(' ', 'T') + 'Z').getTime();
  if (!Number.isFinite(timestamp)) return '';
  const days = Math.max(0, Math.floor((Date.now() - timestamp) / 86400000));
  if (days === 0) return 'Hôm nay';
  if (days === 1) return 'Hôm qua';
  if (days < 30) return `${days} ngày trước`;
  if (days < 365) return `${Math.floor(days / 30)} tháng trước`;
  return `${Math.floor(days / 365)} năm trước`;
}

function updateCompletion() {
  const fields = ['full_name', 'major', 'phone', 'skills', 'bio'];
  const completed = fields.filter(field => String(profile[field] || '').trim()).length + (cvs.length ? 1 : 0);
  const percent = Math.round(completed / 6 * 100);
  $('#completionValue').textContent = `${percent}%`;
  $('#completionBar').style.width = `${percent}%`;
  $('.completion-track').setAttribute('aria-valuenow', String(percent));
  $('#completionHint').textContent = percent === 100
    ? 'Hồ sơ của bạn đã đầy đủ. Hãy tiếp tục cập nhật khi có thông tin mới.'
    : `Hoàn thiện ${6 - completed} mục còn thiếu, bao gồm thông tin cá nhân và CV.`;
  $('#profileWelcome').textContent = profile.full_name ? `Xin chào, ${profile.full_name}` : 'Hoàn thiện hồ sơ của bạn';
}

function renderCvs() {
  $('#cvList').innerHTML = cvs.length ? cvs.map(cv => `
    <article class="cv-item">
      <div class="cv-name"><span aria-hidden="true">📄</span><div><b>${esc(cv.original_filename)}</b><small class="muted">Cập nhật ${esc(timeAgo(cv.created_at))}</small></div></div>
      <div class="cv-actions">
        <a class="btn btn-soft btn-sm" href="/api/students/me/cvs/${cv.id}/download">Tải xuống</a>
        <label class="btn btn-soft btn-sm cv-replace-label">Thay thế
          <input class="cv-replace-input" type="file" data-replace-cv="${cv.id}" accept=".pdf,.doc,.docx" aria-label="Chọn file thay thế ${esc(cv.original_filename)}">
        </label>
        <button class="btn btn-danger btn-sm" type="button" data-delete-cv="${cv.id}">Xóa</button>
      </div>
    </article>`).join('') : '<p class="empty-state">Chưa có CV nào. Tải lên CV đầu tiên để hoàn thiện hồ sơ.</p>';
  updateCompletion();
}

async function loadProfile() {
  profile = await api('/api/students/me');
  $('#sessionLabel').textContent = profile.email;
  const form = $('#profileForm');
  ['full_name', 'major', 'phone', 'skills', 'bio'].forEach(field => {
    form.elements[field].value = profile[field] || '';
  });
  updateCompletion();
}

async function loadCvs() {
  cvs = await api('/api/students/me/cvs');
  renderCvs();
}

async function loadApplications() {
  const params = new URLSearchParams();
  const query = $('#applicationQuery').value.trim();
  const status = $('#applicationStatus').value;
  if (query) params.set('q', query);
  if (status) params.set('status', status);

  const applications = await api('/api/applications/me?' + params);
  if (!query && !status) {
    const active = applications.filter(item => ['submitted', 'reviewing'].includes(item.status)).length;
    $('#applicationCount').textContent = String(applications.length);
    $('#activeApplicationCount').textContent = String(active);
  }
  $('#applicationList').innerHTML = applications.length ? applications.map(item => `
    <article class="application-item">
      <div class="app-info">
        <b>${esc(item.title)}</b>
        <span class="muted">${esc(item.company_name)} · ${esc(timeAgo(item.created_at))}</span>
      </div>
      <div class="application-actions">
        <span class="status-badge status-${esc(item.status)}">${esc(statusLabels[item.status] || item.status)}</span>
        <button class="text-button" type="button" data-application-id="${item.application_id}">Chi tiết</button>
      </div>
    </article>`).join('') : '<p class="empty-state">Không tìm thấy đơn ứng tuyển phù hợp.</p>';
}

async function loadRecommendations() {
  const jobs = await api('/api/students/me/recommendations');
  $('#recommendationList').innerHTML = jobs.length ? jobs.slice(0, 4).map(job => `
    <article class="recommendation-item">
      <div><b>${esc(job.title)}</b><span class="muted">${esc(job.company_name)} · ${esc(job.location || 'Chưa cập nhật địa điểm')}</span></div>
      <a href="/jobs?q=${encodeURIComponent(job.title)}" aria-label="Xem việc làm ${esc(job.title)}">Xem việc làm →</a>
    </article>`).join('') : '<p class="empty-state">Chưa có gợi ý phù hợp. Hãy cập nhật ngành học và kỹ năng trong hồ sơ.</p>';
}

async function openApplication(applicationId) {
  currentApplication = await api(`/api/applications/${applicationId}`);
  $('#dialogJobTitle').textContent = currentApplication.title;
  $('#dialogCompany').textContent = currentApplication.company_name;
  $('#dialogCoverLetter').value = currentApplication.cover_letter || '';
  $('#dialogStatus').textContent = `Trạng thái: ${statusLabels[currentApplication.status] || currentApplication.status}`;
  const editable = currentApplication.status === 'submitted';
  $('#dialogCoverLetter').disabled = !editable;
  $('#saveApplicationMessage').hidden = !editable;
  $('#withdrawApplication').hidden = !['submitted', 'reviewing'].includes(currentApplication.status);
  $('#applicationDialog').showModal();
}

async function initialize() {
  try {
    await loadProfile();
    await Promise.all([loadCvs(), loadApplications(), loadRecommendations()]);
  } catch (error) {
    toast(error.message);
  }

  $('#profileForm').addEventListener('submit', async event => {
    event.preventDefault();
    const message = $('#profileMessage');
    try {
      const data = Object.fromEntries(new FormData(event.currentTarget));
      await api('/api/students/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      profile = { ...profile, ...data };
      message.textContent = 'Hồ sơ đã được lưu.';
      message.style.color = 'var(--green)';
      updateCompletion();
      loadRecommendations().catch(error => toast(error.message));
    } catch (error) {
      message.textContent = error.message;
      message.style.color = 'var(--red)';
    }
  });

  $('#cvFileInput').addEventListener('change', event => {
    $('#cvFileLabel').textContent = event.currentTarget.files[0]?.name || 'Chọn file CV (.pdf, .doc, .docx)';
  });

  $('#cvForm').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      await api('/api/students/me/cvs', { method: 'POST', body: new FormData(event.currentTarget) });
      event.currentTarget.reset();
      $('#cvFileLabel').textContent = 'Chọn file CV (.pdf, .doc, .docx)';
      await loadCvs();
      toast('Đã tải CV lên thành công.');
    } catch (error) {
      toast(error.message);
    }
  });

  $('#cvList').addEventListener('change', async event => {
    const input = event.target.closest('[data-replace-cv]');
    if (!input || !input.files.length) return;
    const data = new FormData();
    data.append('file', input.files[0]);
    try {
      await api(`/api/students/me/cvs/${input.dataset.replaceCv}`, { method: 'PUT', body: data });
      await loadCvs();
      toast('Đã thay thế CV.');
    } catch (error) {
      toast(error.message);
      input.value = '';
    }
  });

  $('#cvList').addEventListener('click', async event => {
    const button = event.target.closest('[data-delete-cv]');
    if (!button || !confirm('Bạn có chắc muốn xóa CV này?')) return;
    try {
      await api(`/api/students/me/cvs/${button.dataset.deleteCv}`, { method: 'DELETE' });
      await loadCvs();
      toast('Đã xóa CV.');
    } catch (error) {
      toast(error.message);
    }
  });

  $('#applicationQuery').addEventListener('input', () => {
    clearTimeout(applicationTimer);
    applicationTimer = setTimeout(() => loadApplications().catch(error => toast(error.message)), 300);
  });
  $('#applicationStatus').addEventListener('change', () => loadApplications().catch(error => toast(error.message)));
  $('#applicationList').addEventListener('click', event => {
    const button = event.target.closest('[data-application-id]');
    if (button) openApplication(button.dataset.applicationId).catch(error => toast(error.message));
  });
  $('#closeApplicationDialog').addEventListener('click', () => $('#applicationDialog').close());

  $('#saveApplicationMessage').addEventListener('click', async () => {
    if (!currentApplication) return;
    try {
      await api(`/api/applications/${currentApplication.application_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cover_letter: $('#dialogCoverLetter').value })
      });
      $('#applicationDialog').close();
      await loadApplications();
      toast('Đã cập nhật lời nhắn ứng tuyển.');
    } catch (error) {
      toast(error.message);
    }
  });

  $('#withdrawApplication').addEventListener('click', async () => {
    if (!currentApplication || !confirm('Bạn có chắc muốn rút đơn ứng tuyển này?')) return;
    try {
      await api(`/api/applications/${currentApplication.application_id}`, { method: 'DELETE' });
      $('#applicationDialog').close();
      await loadApplications();
      toast('Đã rút đơn ứng tuyển.');
    } catch (error) {
      toast(error.message);
    }
  });
}

document.addEventListener('DOMContentLoaded', initialize);
