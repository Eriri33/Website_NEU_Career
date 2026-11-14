(() => {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const dots = Array.from(document.querySelectorAll('.slide-dot'));
  const panel = document.querySelector('.login-panel');
  let activeIndex = 0;
  let timer = null;
  const interval = 5500;

  function showSlide(index) {
    activeIndex = (index + slides.length) % slides.length;
    slides.forEach((slide, i) => slide.classList.toggle('active', i === activeIndex));
    dots.forEach((dot, i) => {
      dot.classList.toggle('active', i === activeIndex);
      dot.setAttribute('aria-pressed', i === activeIndex ? 'true' : 'false');
    });
    panel.classList.remove('light-bg', 'dark-bg');
    panel.classList.add(slides[activeIndex].dataset.theme || 'dark-bg');
    restartTimer();
  }

  function restartTimer() {
    if (timer) window.clearInterval(timer);
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    timer = window.setInterval(() => showSlide(activeIndex + 1), interval);
  }

  dots.forEach(dot => dot.addEventListener('click', () => showSlide(Number(dot.dataset.slide))));
  showSlide(0);

  const toggle = document.getElementById('togglePassword');
  const password = document.getElementById('password');
  toggle?.addEventListener('click', () => {
    const visible = password.type === 'password';
    password.type = visible ? 'text' : 'password';
    toggle.setAttribute('aria-label', visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
  });

  document.getElementById('staffLogin')?.addEventListener('submit', async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const error = document.getElementById('loginError');
    const button = form.querySelector('button[type="submit"]');
    const label = button.querySelector('.submit-label');
    const originalLabel = label.textContent;
    button.disabled = true;
    label.textContent = 'Đang đăng nhập...';
    error.textContent = '';

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        credentials: 'same-origin',
        body: JSON.stringify({
          email: form.email.value.trim(),
          password: form.password.value
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || data.error || 'Không thể đăng nhập.');
      if (!data.user || !['admin', 'moderator'].includes(String(data.user.role).toLowerCase())) {
        await fetch('/api/auth/logout', {method: 'POST', credentials: 'same-origin'});
        throw new Error('Tài khoản này không có quyền truy cập khu vực quản trị.');
      }
      window.location.assign('/admin/');
    } catch (err) {
      error.textContent = err.message || 'Đã xảy ra lỗi. Vui lòng thử lại.';
    } finally {
      button.disabled = false;
      label.textContent = originalLabel;
    }
  });
})();
