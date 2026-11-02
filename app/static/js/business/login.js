(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const q = new URLSearchParams(location.search);
  const errBox = $('authError');
  const showError = (m) => { errBox.textContent = m; errBox.hidden = !m; };

  const reason = q.get('reason');
  const notices = {
    expired: 'Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.',
    role: 'Trang này dành cho tài khoản doanh nghiệp. Hãy đăng nhập bằng tài khoản doanh nghiệp.',
  };
  if (notices[reason]) { $('authNoticeText').textContent = notices[reason]; $('authNotice').hidden = false; }

  function safeNext() {
    const n = q.get('next') || '';
    return n.startsWith('/business/') && !n.startsWith('//') ? n : '/business/dashboard';
  }

  function setTab(register) {
    $('tabLogin').setAttribute('aria-selected', String(!register));
    $('tabRegister').setAttribute('aria-selected', String(register));
    $('formLogin').hidden = register;
    $('formRegister').hidden = !register;
    $('authTitle').textContent = register ? 'Đăng ký nhà tuyển dụng' : 'Đăng nhập nhà tuyển dụng';
    $('authLead').textContent = register ? 'Tạo tài khoản để đăng tin tuyển dụng đến sinh viên NEU.' : 'Dùng tài khoản doanh nghiệp để quản lý tin tuyển dụng và ứng viên.';
    showError('');
  }
  $('tabLogin').addEventListener('click', () => setTab(false));
  $('tabRegister').addEventListener('click', () => setTab(true));
  if (q.get('tab') === 'register') setTab(true);

  document.querySelectorAll('[data-toggle]').forEach((b) => b.addEventListener('click', () => {
    const input = $(b.dataset.toggle);
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    b.textContent = show ? 'Ẩn' : 'Hiện';
    b.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
  }));

  async function login(email, password) {
    const res = await BZ.api('/api/auth/login', { method: 'POST', body: { email, password }, noRedirect: true });
    if (res.user.role !== 'business') {
      await BZ.api('/api/auth/logout', { method: 'POST', noRedirect: true });
      throw new BZ.Error(403, 'wrong_role', 'Đây không phải tài khoản doanh nghiệp. Sinh viên và quản trị viên dùng trang đăng nhập riêng.');
    }
  }

  $('formLogin').addEventListener('submit', async (e) => {
    e.preventDefault();
    showError('');
    const email = $('loginEmail').value.trim(), password = $('loginPassword').value;
    if (!email || !password) { showError('Nhập email và mật khẩu.'); return; }
    BZ.busy($('btnLogin'), true, 'Đang đăng nhập…');
    try { await login(email, password); location.href = safeNext(); }
    catch (err) { showError(err.message); BZ.busy($('btnLogin'), false); }
  });

  $('formRegister').addEventListener('submit', async (e) => {
    e.preventDefault();
    showError('');
    const email = $('regEmail').value.trim(), pw = $('regPassword').value;
    if (!email.includes('@')) { showError('Nhập email hợp lệ.'); return; }
    if (pw.length < 6) { showError('Mật khẩu tối thiểu 6 ký tự.'); return; }
    if (pw !== $('regConfirm').value) { showError('Hai mật khẩu chưa khớp.'); return; }
    BZ.busy($('btnRegister'), true, 'Đang tạo tài khoản…');
    try {
      await BZ.api('/api/auth/register', { method: 'POST', body: { email, password: pw, role: 'business' }, noRedirect: true });
      await login(email, pw);
      location.href = '/business/profile?welcome=1';
    } catch (err) { showError(err.message); BZ.busy($('btnRegister'), false); }
  });
})();
