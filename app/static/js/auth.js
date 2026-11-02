const form = document.querySelector('#loginForm, #registerForm');
const message = document.querySelector('#formMessage');
const submitButton = form?.querySelector('button[type="submit"]');

// Hiện / ẩn mật khẩu
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
  if (!response.ok) throw new Error(result.message || 'Không thể kết nối máy chủ.');
  return result;
}

form?.addEventListener('submit', async event => {
  event.preventDefault();
  showMessage('');

  const data = Object.fromEntries(new FormData(form));
  const registering = form.id === 'registerForm';
  data.email = (data.email || '').trim();

  if (!data.email || !data.email.includes('@')) return showMessage('Vui lòng nhập email hợp lệ.');
  if (!data.password) return showMessage('Vui lòng nhập mật khẩu.');
  if (registering && data.password.length < 6) return showMessage('Mật khẩu cần có ít nhất 6 ký tự.');

  const label = submitButton.textContent;
  submitButton.disabled = true;
  submitButton.textContent = registering ? 'Đang tạo tài khoản…' : 'Đang đăng nhập…';
  try {
    if (registering) await send('/api/auth/register', data);
    await send('/api/auth/login', { email: data.email, password: data.password });
    showMessage('Thành công! Đang chuyển hướng…', 'success');
    location.assign('/dashboard');
  } catch (error) {
    showMessage(error.message);
    submitButton.disabled = false;
    submitButton.textContent = label;
  }
});
