(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const SEG = ['submitted', 'reviewing', 'accepted', 'rejected', 'withdrawn'];

  function welcome(profile, jobs, stats) {
    const named = profile.company_name !== BZ.DEFAULT_COMPANY_NAME;
    $('welcomeTitle').textContent = named ? `Xin chào, ${profile.company_name}` : 'Chào mừng bạn đến NEU Career';
    let text = '', actions = '';
    const newJob = '<a class="btn btn-gold js-new-job" href="/business/jobs/new">' + BZ.icon('plus') + 'Đăng tin mới</a>';
    if (profile.approval_status === 'approved') {
      const live = jobs.filter((j) => j.status === 'approved' && !j.is_expired).length;
      text = `Công ty có ${live} tin đang hiển thị và ${stats.submitted} hồ sơ mới chờ xem.`;
      actions = newJob + `<a class="btn btn-light" href="/business/applicants?status=submitted">Xem hồ sơ mới</a>`;
    } else if (!named) {
      text = 'Điền tên và giới thiệu công ty, sau đó chờ nhà trường duyệt để bắt đầu đăng tin.';
      actions = '<a class="btn btn-gold" href="/business/profile">Hoàn thiện hồ sơ</a>';
    } else if (profile.approval_status === 'rejected') {
      text = 'Hồ sơ công ty chưa được duyệt. Chỉnh sửa theo ghi chú và gửi duyệt lại.';
      actions = '<a class="btn btn-gold" href="/business/profile">Chỉnh sửa hồ sơ</a>';
    } else {
      text = 'Hồ sơ đang chờ nhà trường duyệt. Bạn sẽ đăng được tin ngay khi hồ sơ được duyệt.';
      actions = '<a class="btn btn-light" href="/business/profile">Xem hồ sơ công ty</a>';
    }
    $('welcomeText').textContent = text;
    $('welcomeActions').innerHTML = actions;
    if (profile.approval_status !== 'approved') document.querySelectorAll('.js-new-job').forEach((a) => a.setAttribute('aria-disabled', 'true'));
  }

  function statCards(jobs, stats) {
    const live = jobs.filter((j) => j.status === 'approved' && !j.is_expired).length;
    const pending = jobs.filter((j) => j.status === 'pending');
    const re = pending.filter((j) => j.needs_re_review).length;
    const cards = [
      ['/business/jobs?status=approved', live, 'Tin đang hiển thị', 'Sinh viên đang thấy'],
      ['/business/jobs?status=pending', pending.length, 'Tin chờ duyệt', re ? `${re} tin chờ duyệt lại` : 'Chờ nhà trường kiểm duyệt'],
      ['/business/applicants?status=submitted', stats.submitted, 'Hồ sơ mới', 'Chưa được xem'],
      ['/business/applicants', stats.total, 'Tổng hồ sơ', 'Từ mọi tin tuyển dụng'],
    ];
    $('stats').innerHTML = cards.map(([href, n, l, note]) =>
      `<a class="card stat" href="${href}"><div class="num">${n}</div><div class="lbl">${l}</div><div class="note">${note}</div></a>`).join('');
  }

  function pipeline(stats) {
    if (!stats.total) {
      $('pipelineBox').innerHTML = BZ.emptyState({ icon: 'users', title: 'Chưa có hồ sơ ứng tuyển', text: 'Khi sinh viên ứng tuyển vào tin của công ty, hồ sơ sẽ xuất hiện ở đây.' });
      return;
    }
    const bar = SEG.filter((s) => stats[s]).map((s) => `<span class="seg-${s}" style="flex-grow:${stats[s]}" title="${BZ.APP_STATUS[s]}: ${stats[s]}"></span>`).join('');
    const legend = SEG.map((s) => `<a href="/business/applicants?status=${s}"><i class="seg-${s}"></i><small>${BZ.APP_STATUS[s]}</small><b>${stats[s]}</b></a>`).join('');
    $('pipelineBox').innerHTML = `<div class="pipeline" role="img" aria-label="Tỷ lệ hồ sơ theo trạng thái">${bar}</div><div class="legend">${legend}</div>`;
  }

  function latest(apps) {
    const items = apps.filter((a) => a.status === 'submitted').slice(0, 5);
    if (!items.length) { $('latestList').innerHTML = `<li class="muted">Không có hồ sơ mới. Mọi hồ sơ đã được xem.</li>`; return; }
    $('latestList').innerHTML = items.map((a) => {
      const name = a.full_name || a.email;
      return `<li><div class="avatar">${BZ.esc(BZ.initials(a.full_name || a.email))}</div>
        <div class="grow"><div class="title truncate">${BZ.esc(name)}</div><div class="meta truncate">Ứng tuyển ${BZ.esc(a.title)}, ${BZ.relTime(a.created_at)}</div></div>
        <a class="btn btn-outline btn-sm" href="/business/applicants?open=${a.application_id}">Xem hồ sơ</a></li>`;
    }).join('');
  }

  function attention(jobs) {
    const out = [];
    jobs.forEach((j) => {
      const link = `<a href="/business/jobs/${j.id}">${BZ.esc(j.title)}</a>`;
      if (j.status === 'rejected') out.push(['red', `${link} bị từ chối${j.review_note ? ': ' + BZ.esc(j.review_note.replace(/[.\s]+$/, '')) : ''}. <a href="/business/jobs/${j.id}/edit">Sửa và gửi lại</a>`]);
      else if (j.status === 'approved' && j.is_expired) out.push(['red', `${link} đã hết hạn nộp nên không còn hiển thị. <a href="/business/jobs/${j.id}/edit">Gia hạn</a>`]);
      else if (j.status === 'approved' && j.deadline && BZ.daysUntil(j.deadline) <= 7) out.push(['gold', `${link} hết hạn sau ${BZ.daysUntil(j.deadline)} ngày.`]);
      else if (j.status === 'pending' && j.needs_re_review) out.push(['blue', `${link} đang chờ duyệt lại sau khi chỉnh sửa, tạm thời chưa hiển thị.`]);
    });
    $('attnList').innerHTML = out.length
      ? out.slice(0, 6).map(([c, h]) => `<div class="attn"><span class="dot dot-${c}"></span><div>${h}</div></div>`).join('')
      : `<div class="state" style="padding:28px 20px">${BZ.icon('check', 'ic-big')}<p style="margin:0">Không có tin nào cần xử lý.</p></div>`;
  }

  async function load(profile) {
    $('dashError').hidden = true;
    try {
      const [jobs, apps, stats] = await Promise.all([
        BZ.api('/api/company/jobs'),
        BZ.api('/api/company/applications', { query: { sort: 'latest' } }),
        BZ.api('/api/company/applications/stats'),
      ]);
      welcome(profile, jobs, stats); statCards(jobs, stats); pipeline(stats); latest(apps); attention(jobs);
    } catch (e) {
      $('dashCols').hidden = true;
      $('dashError').innerHTML = `<div class="card">${BZ.errorState(e.message)}</div>`;
      $('dashError').hidden = false;
    }
  }

  document.addEventListener('DOMContentLoaded', async () => {
    let profile;
    try { profile = await BZ.init(); } catch (e) { return; }
    BZ.onRetry($('dashError'), () => { $('dashCols').hidden = false; load(profile); });
    load(profile);
  });
})();
