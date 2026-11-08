const publicApi = async url => {
  const response = await fetch(url, { credentials: 'same-origin' });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw Error(data.message || 'Không thể kết nối máy chủ.');
  return data;
};

document.addEventListener('DOMContentLoaded', async () => {
  const authButton = document.querySelector('#authButton');
  if (!authButton) return;
  try {
    const user = await publicApi('/api/auth/me');
    const label = document.querySelector('#sessionLabel');
    if (label) label.textContent = user.email;
    const accountDestinations = {
      student: ['/student/profile', 'Hồ sơ của tôi'],
      business: ['/business/dashboard', 'Khu vực doanh nghiệp'],
      moderator: ['/admin/', 'Khu vực quản trị'],
      admin: ['/admin/', 'Khu vực quản trị']
    };
    const [destination, labelText] = accountDestinations[user.role] || ['/dashboard', 'Tài khoản'];
    authButton.textContent = labelText;
    authButton.href = destination;
  } catch (_) {
    authButton.textContent = 'Đăng nhập';
    authButton.href = '/login';
  }
});
