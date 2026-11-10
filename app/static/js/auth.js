
const form = document.querySelector('#loginForm, #registerForm');
const message = document.querySelector('#formMessage');
const submitButton = form?.querySelector('button[type="submit"]');

document.querySelectorAll('.toggle-password').forEach(button => {
  button.addEventListener('click', () => {
    const input = button.parentElement.querySelector('input');
    const show = input.type === 'password';

    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'Ẩn' : 'Hiện';
    button.setAttribute('aria-pressed', String(show));
    button.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
  });
});

function showMessage(text, type = 'error') {
  if (!message) return;
  message.textContent = text;
  message.className = 'form-message ' + (text ? type : '');
}

async function send(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(result.message || 'Không thể kết nối máy chủ.');
  }

  return result;
}

function getRedirectByRole(role, registering) {
  // Đăng ký doanh nghiệp: chuyển tới trang hoàn thiện hồ sơ.
  if (registering && role === 'business') {
    return '/business/profile?welcome=1';
  }

  if (role === 'student') return '/';
  if (role === 'business') return '/business/dashboard';
  if (role === 'admin' || role === 'moderator') return '/admin/';

  return '/';
}

function getSafeNext(role) {
  const next = new URLSearchParams(window.location.search).get('next');

  if (!next || !next.startsWith('/') || next.startsWith('//')) {
    return null;
  }

  // Không cho phép chuyển sang khu vực của role khác.
  if (role === 'business' && next.startsWith('/business/')) return next;
  if ((role === 'admin' || role === 'moderator') && next.startsWith('/admin/')) return next;

  return null;
}

form?.addEventListener('submit', async event => {
  event.preventDefault();
  showMessage('');

  const data = Object.fromEntries(new FormData(form));
  const registering = form.id === 'registerForm';

  data.email = (data.email || '').trim().toLowerCase();

  if (!data.email || !data.email.includes('@')) {
    return showMessage('Vui lòng nhập email hợp lệ.');
  }

  if (!data.password) {
    return showMessage('Vui lòng nhập mật khẩu.');
  }

  if (registering && data.password.length < 6) {
    return showMessage('Mật khẩu cần có ít nhất 6 ký tự.');
  }

  const originalLabel = submitButton.textContent;
  submitButton.disabled = true;
  submitButton.textContent = registering
    ? 'Đang tạo tài khoản…'
    : 'Đang đăng nhập…';

  try {
    if (registering) {
      await send('/api/auth/register', data);
    }

    const result = await send('/api/auth/login', {
      email: data.email,
      password: data.password
    });

    const role = result.user?.role;

    if (!role) {
      throw new Error('Máy chủ không trả về thông tin vai trò tài khoản.');
    }

    showMessage('Thành công! Đang chuyển hướng…', 'success');

    const next = registering ? null : getSafeNext(role);
    location.assign(next || getRedirectByRole(role, registering));

  } catch (error) {
    showMessage(error.message);
    submitButton.disabled = false;
    submitButton.textContent = originalLabel;
  }
});
