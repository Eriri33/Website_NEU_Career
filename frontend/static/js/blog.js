const blogEscape = value => String(value ?? '').replace(/[&<>'"]/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));

const blogApi = async url => {
  const response = await fetch(url);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw Error(data.message || 'Không thể kết nối máy chủ.');
  return data;
};

let blogCategory = '';
let blogRequest = 0;
let blogSearchTimer;
let blogPosts = [];

function renderBlogCategories(posts) {
  const categories = [...new Set(posts.map(post => post.category).filter(Boolean))];
  document.querySelector('#blogCategories').innerHTML = [
    '<button type="button" class="blog-category active" data-category="">Tất cả</button>',
    ...categories.map(category => `<button type="button" class="blog-category" data-category="${blogEscape(category)}">${blogEscape(category)}</button>`)
  ].join('');
  document.querySelectorAll('#blogCategories .blog-category').forEach(button => {
    button.classList.toggle('active', button.dataset.category === blogCategory);
  });
}

function renderBlogPosts() {
  const container = document.querySelector('#blogCards');
  const filtered = blogCategory ? blogPosts.filter(post => post.category === blogCategory) : blogPosts;
  document.querySelector('#blogState').innerHTML = '';
  container.innerHTML = filtered.length
    ? filtered.map((post, index) => `
      <article class="blog-card" id="blog-${post.id}">
        <div class="blog-card-image blog-card-image-${index % 3}" aria-hidden="true">
          <span>${blogEscape(post.category)}</span>
        </div>
        <div class="blog-card-content">
          <p class="eyebrow blue">${blogEscape(post.category)}</p>
          <h3>${blogEscape(post.title)}</h3>
          <p class="blog-summary">${blogEscape(post.summary)}</p>
          <div class="blog-card-footer">
            <span>${post.created_at ? blogEscape(post.created_at.split(' ')[0]) : 'NEU Career'}</span>
            <button type="button" class="text-button" data-open-post="${post.id}">Đọc bài viết →</button>
          </div>
        </div>
      </article>`).join('')
    : '<div class="empty">Không tìm thấy bài viết phù hợp.</div>';
}

async function loadBlogPosts() {
  const requestId = ++blogRequest;
  const state = document.querySelector('#blogState');
  const query = document.querySelector('#blogSearch').value.trim();
  state.innerHTML = '<div class="loading">Đang tải bài viết…</div>';
  try {
    const params = new URLSearchParams();
    if (query) params.set('q', query);
    const posts = await blogApi('/api/career-contents?' + params);
    if (requestId !== blogRequest) return;
    blogPosts = posts;
    blogCategory = '';
    renderBlogCategories(posts);
    renderBlogPosts();
  } catch (error) {
    if (requestId !== blogRequest) return;
    state.innerHTML = `<div class="error">${blogEscape(error.message)} <button type="button" class="text-button" id="retryBlog">Thử lại</button></div>`;
    document.querySelector('#blogCards').innerHTML = '';
  }
}

async function openBlogPost(id) {
  try {
    const post = await blogApi('/api/career-contents/' + encodeURIComponent(id));
    document.querySelector('#modalContent').innerHTML = `
      <p class="eyebrow blue">${blogEscape(post.category)}</p>
      <h2 id="blogModalTitle">${blogEscape(post.title)}</h2>
      <p class="blog-detail-date">${post.created_at ? blogEscape(post.created_at.split(' ')[0]) : ''}</p>
      <p class="blog-detail-summary">${blogEscape(post.summary)}</p>
      <div class="blog-detail-body">${blogEscape(post.body)}</div>`;
    document.querySelector('#modal').hidden = false;
  } catch (error) {
    const state = document.querySelector('#blogState');
    state.innerHTML = `<div class="error">${blogEscape(error.message)}</div>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const search = document.querySelector('#blogSearch');
  const cards = document.querySelector('#blogCards');
  const categories = document.querySelector('#blogCategories');
  const modal = document.querySelector('#modal');

  search.addEventListener('input', () => {
    clearTimeout(blogSearchTimer);
    blogSearchTimer = setTimeout(() => {
      blogCategory = '';
      loadBlogPosts();
    }, 250);
  });
  categories.addEventListener('click', event => {
    const button = event.target.closest('[data-category]');
    if (!button) return;
    blogCategory = button.dataset.category;
    categories.querySelectorAll('.blog-category').forEach(item =>
      item.classList.toggle('active', item === button)
    );
    renderBlogPosts();
  });
  cards.addEventListener('click', event => {
    const button = event.target.closest('[data-open-post]');
    if (button) openBlogPost(button.dataset.openPost);
  });
  document.querySelector('#blogState').addEventListener('click', event => {
    if (event.target.id === 'retryBlog') loadBlogPosts();
  });
  document.querySelector('#closeModal').addEventListener('click', () => { modal.hidden = true; });
  modal.addEventListener('click', event => {
    if (event.target === modal) modal.hidden = true;
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') modal.hidden = true;
  });
  loadBlogPosts().then(() => {
    const target = location.hash.match(/^#blog-(\d+)$/);
    if (target) {
      document.querySelector(`#blog-${CSS.escape(target[1])}`)?.scrollIntoView({ behavior: 'smooth' });
    }
  });
});
