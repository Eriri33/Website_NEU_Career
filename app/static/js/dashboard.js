document.querySelector('#logoutButton').addEventListener('click', async () => {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
  location.assign('/');
});
