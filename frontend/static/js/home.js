const homeEscape = value => String(value ?? '').replace(/[&<>'"]/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));

async function homeFetch(url) {
  const response = await fetch(url);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw Error(data.message || 'Không thể tải dữ liệu.');
  return data;
}

async function loadHomeJobs() {
  const container = document.querySelector('#homeJobs');
  try {
    const jobs = await homeFetch('/api/jobs');
    container.innerHTML = jobs.length
      ? jobs.slice(0, 3).map(job => `
        <a class="home-job-card" href="/jobs?q=${encodeURIComponent(job.title)}">
          <span class="home-job-mark" aria-hidden="true">↗</span>
          <span class="home-job-type">${homeEscape(job.job_type === 'internship' ? 'Thực tập' : 'Việc làm')}</span>
          <b>${homeEscape(job.title)}</b>
          <small>${homeEscape(job.company_name)} · ${homeEscape(job.location || 'Chưa cập nhật')}</small>
          <span class="home-job-salary">${homeEscape(job.salary_text || 'Thỏa thuận')}</span>
        </a>`).join('')
      : '<div class="empty">Chưa có việc làm phù hợp. Hãy quay lại sau nhé.</div>';
  } catch (error) {
    container.innerHTML = `<div class="error">${homeEscape(error.message)}</div>`;
  }
}

async function loadHomeBlogs() {
  const container = document.querySelector('#homeBlogs');
  try {
    const posts = await homeFetch('/api/career-contents');
    container.innerHTML = posts.length
      ? posts.slice(0, 3).map((post, index) => `
        <a class="career-card home-blog-card" href="/blog#blog-${post.id}">
          <img src="/static/assets/${['neu_3.jpg', 'images_toa_A2.jpg', 'neu_2.jpg'][index % 3]}"
               alt="" loading="lazy">
          <div>
            <span class="career-tag">${homeEscape(post.category)}</span>
            <h3>${homeEscape(post.title)}</h3>
            <p>${homeEscape(post.summary)}</p>
            <span class="home-read-more">Đọc bài viết →</span>
          </div>
        </a>`).join('')
      : '<div class="empty">Bài viết hướng nghiệp đang được cập nhật.</div>';
  } catch (error) {
    container.innerHTML = `<div class="error">${homeEscape(error.message)}</div>`;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const statIds = ['#statJobs', '#statCategories', '#statCompanies'];
  try {
    const [suggestions, categories] = await Promise.all([
      homeFetch('/api/jobs/suggestions'),
      homeFetch('/api/jobs/categories')
    ]);
    const stats = suggestions.stats;
    if (stats) {
      document.querySelector(statIds[0]).textContent = stats.total_jobs;
      document.querySelector(statIds[2]).textContent = stats.total_companies;
    }
    document.querySelector(statIds[1]).textContent = categories.length;
  } catch (error) {
    console.error('Không thể tải thống kê trang chủ:', error);
  }
  loadHomeJobs();
  loadHomeBlogs();
});
