document.querySelector('#logoutButton')?.addEventListener('click', async event => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    const response = await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.message || 'Không thể đăng xuất. Vui lòng thử lại.');
    location.assign('/');
  } catch (error) {
    window.alert(error.message || 'Không thể kết nối máy chủ. Vui lòng thử lại.');
    button.disabled = false;
  }
});
