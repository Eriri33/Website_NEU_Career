(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const jobId = document.body.dataset.jobId;
  const SEG = ['submitted', 'reviewing', 'accepted', 'rejected', 'withdrawn'];

  function statusBlock(j) {
    if (j.status === 'pending') return j.needs_re_review
      ? ['warn', 'Tin đã chỉnh sửa và đang chờ nhà trường duyệt lại. Trong lúc này tin chưa hiển thị với sinh viên.']
      : ['warn', 'Tin đang chờ nhà trường kiểm duyệt. Sinh viên sẽ thấy tin sau khi được duyệt.'];
    if (j.status === 'approved') return j.is_expired
      ? ['danger', 'Tin đã qua hạn nộp nên không còn hiển thị. Sửa hạn nộp và gửi duyệt lại để đăng tiếp.']
      : ['info', 'Tin đang hiển thị công khai cho sinh viên.'];
    if (j.status === 'rejected') return ['danger', 'Tin bị từ chối' + (j.review_note ? `. Lý do: ${j.review_note}` : '.') + ' Sửa tin và gửi lại để được duyệt.'];
    return ['info', 'Tin đã đóng và không hiển thị. Hồ sơ đã nhận vẫn được giữ lại. Sửa tin để gửi duyệt đăng lại.'];
  }

  function render(j, stats, apps) {
    const [kind, msg] = statusBlock(j);
    const chip = j.status === 'pending' && j.needs_re_review ? BZ.chip('warn', 'Chờ duyệt lại') : BZ.chip(j.status, BZ.JOB_STATUS[j.status]);
    const skills = BZ.splitList(j.skills_required).map((s) => `<span class="pill">${BZ.esc(s)}</span>`).join(' ') || '<span class="muted">Không yêu cầu cụ thể</span>';
    const max = Math.max(1, ...SEG.map((s) => stats[s]));
    const bars = SEG.map((s) => `<a href="/business/applicants?job_id=${j.id}&status=${s}"><span>${BZ.APP_STATUS[s]}</span><span class="bar"><i class="seg-${s}" style="width:${stats[s] / max * 100}%"></i></span><b>${stats[s]}</b></a>`).join('');
    const recent = apps.slice(0, 5).map((a) => `<li><div class="avatar">${BZ.esc(BZ.initials(a.full_name || a.email))}</div><div class="grow"><div class="title truncate">${BZ.esc(a.full_name || a.email)}</div><div class="meta">${BZ.relTime(a.created_at)}</div></div>${BZ.chip(a.status, BZ.APP_STATUS[a.status])}</li>`).join('');
    document.title = j.title + ' - NEU Career';
    $('detailRoot').innerHTML = `
      <div class="banner banner-${kind}" role="status">${BZ.icon(kind === 'danger' || kind === 'warn' ? 'alert' : 'info')}<div>${BZ.esc(msg)}</div></div>
      <div class="cols">
        <div class="stack">
          <section class="card card-pad">
            <div class="job-head"><div class="grow"><h2>${BZ.esc(j.title)}</h2><div style="margin-top:8px">${chip}</div></div>
              <div class="row-actions"><a class="btn btn-outline" href="/business/jobs/${j.id}/edit">${BZ.icon('edit')}${j.status === 'closed' ? 'Sửa và đăng lại' : 'Sửa tin'}</a>
              ${j.status !== 'closed' ? '<button type="button" class="btn btn-danger" id="btnClose">Đóng tin</button>' : ''}</div></div>
            <div class="info-grid" style="margin-top:20px">
              <div><div class="k">Danh mục</div><div class="v">${BZ.esc(j.category_name || 'Chưa phân loại')}</div></div>
              <div><div class="k">Loại công việc</div><div class="v">${BZ.JOB_TYPE[j.job_type]}</div></div>
              <div><div class="k">Địa điểm</div><div class="v">${BZ.esc(j.location || 'Chưa nhập')}</div></div>
              <div><div class="k">Mức lương</div><div class="v">${BZ.esc(j.salary_text || 'Thỏa thuận')}</div></div>
              <div><div class="k">Thứ Bảy</div><div class="v">${BZ.SATURDAY[j.saturday_policy] || ''}</div></div>
              <div><div class="k">Hạn nộp</div><div class="v">${BZ.deadlineHtml(j)}</div></div>
              <div><div class="k">Ngành học phù hợp</div><div class="v">${BZ.esc(j.major_required || 'Mọi ngành')}</div></div>
              <div><div class="k">Đăng ngày</div><div class="v">${BZ.fmtDate(j.created_at)}</div></div>
            </div>
            <div style="margin-top:20px"><div class="k muted" style="font-size:12.5px;margin-bottom:6px">Kỹ năng yêu cầu</div><div class="chips-mini" style="margin:0">${skills}</div></div>
          </section>
          <section class="card card-pad"><h2 class="section-title">Mô tả công việc</h2><div class="prose">${BZ.esc(j.description)}</div></section>
        </div>
        <div class="stack">
          <section class="card card-pad"><h2 class="section-title">Hồ sơ ứng tuyển (${stats.total})</h2>
            ${stats.total ? `<div class="mini-bars">${bars}</div>` : '<p class="muted" style="margin:0">Chưa có sinh viên nào ứng tuyển tin này.</p>'}</section>
          ${apps.length ? `<section class="card"><div class="card-head"><h2>Hồ sơ gần đây</h2><a href="/business/applicants?job_id=${j.id}">Xem tất cả</a></div><ul class="list">${recent}</ul></section>` : ''}
        </div>
      </div>`;
    const closeBtn = $('btnClose');
    if (closeBtn) closeBtn.addEventListener('click', async () => {
      const ok = await BZ.confirm({ title: 'Đóng tin tuyển dụng?', message: 'Tin sẽ không còn hiển thị với sinh viên. Hồ sơ đã nhận vẫn được giữ lại.', confirmText: 'Đóng tin', danger: true });
      if (!ok) return;
      try { await BZ.api(`/api/company/jobs/${j.id}`, { method: 'DELETE' }); BZ.toast('Đã đóng tin tuyển dụng.'); load(); }
      catch (e) { BZ.toast(e.message, 'error'); }
    });
  }

  async function load() {
    try {
      const j = await BZ.api(`/api/company/jobs/${jobId}`);
      const [stats, apps] = await Promise.all([
        BZ.api('/api/company/applications/stats', { query: { job_id: jobId } }),
        BZ.api('/api/company/applications', { query: { job_id: jobId } }),
      ]);
      render(j, stats, apps);
    } catch (e) {
      $('detailRoot').innerHTML = `<div class="card">${e.status === 404
        ? BZ.emptyState({ icon: 'search', title: 'Không tìm thấy tin', text: 'Tin không tồn tại hoặc không thuộc công ty của bạn.', actionHtml: '<a class="btn btn-primary" href="/business/jobs">Về danh sách tin</a>' })
        : BZ.errorState(e.message)}</div>`;
    }
  }

  document.addEventListener('DOMContentLoaded', async () => {
    try { await BZ.init(); } catch (e) { return; }
    BZ.onRetry($('detailRoot'), load);
    load();
  });
})();
