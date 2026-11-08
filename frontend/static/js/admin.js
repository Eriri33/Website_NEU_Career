(() => {
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const page = document.body.dataset.page;
  const role = document.body.dataset.role;
  const toastEl = $('#toast');
  let toastTimer;
  function toast(message, error=false){ toastEl.textContent=message; toastEl.style.background=error?'#f5365c':'#32325d'; toastEl.classList.add('show'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>toastEl.classList.remove('show'),2800); }
  async function api(url, options={}){
    const response=await fetch(url,{credentials:'same-origin',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});
    const data=await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(data.message||data.error||`Lỗi ${response.status}`);
    return data;
  }
  const esc = value => String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const date = value => value ? new Date(value.replace(' ','T')+'Z').toLocaleDateString('vi-VN') : '—';
  const status = value => `<span class="status ${esc(value)}">${({pending:'Chờ duyệt',approved:'Đã duyệt',rejected:'Từ chối',draft:'Bản nháp',published:'Đã xuất bản',active:'Hoạt động',inactive:'Đã khóa',closed:'Đã đóng'})[value]||esc(value)}</span>`;
  async function review(type,id,decision){
    let note=''; if(decision==='rejected'){note=prompt('Nhập lý do từ chối (có thể để trống):')??null;if(note===null)return;} 
    try{await api(`/api/admin/${type}/${id}/review`,{method:'POST',body:JSON.stringify({decision,note})});toast(decision==='approved'?'Đã phê duyệt.':'Đã từ chối.');type==='companies'?loadCompanies():loadJobs();}
    catch(e){toast(e.message,true);}
  }
  function bindSearch(input, callback){const el=$(input);if(el)el.addEventListener('input',callback);}
  async function loadCompanies(){
    const body=$('#companiesTable');if(!body)return;body.innerHTML='<tr><td colspan="6" class="empty-cell">Đang tải...</td></tr>';
    try{const rows=await api('/api/admin/pending/companies');const q=($('#companySearch')?.value||'').toLowerCase();const filtered=rows.filter(x=>`${x.company_name} ${x.email}`.toLowerCase().includes(q));$('#companyCount').textContent=`${filtered.length} hồ sơ`;
      body.innerHTML=filtered.length?filtered.map(x=>`<tr><td><div class="cell-main">${esc(x.company_name)}</div><div class="cell-sub">Mã doanh nghiệp #${x.id}</div></td><td>${esc(x.email)}</td><td>${x.website?`<a href="${esc(x.website)}" target="_blank" rel="noopener">${esc(x.website)}</a>`:'—'}</td><td>${date(x.created_at)}</td><td>${status('pending')}</td><td><div class="actions"><button class="action-btn action-approve" data-company-approve="${x.id}">Duyệt</button><button class="action-btn action-reject" data-company-reject="${x.id}">Từ chối</button></div></td></tr>`).join(''):'<tr><td colspan="6" class="empty-cell">Không có hồ sơ phù hợp.</td></tr>';
    }catch(e){body.innerHTML=`<tr><td colspan="6" class="empty-cell">${esc(e.message)}. Hãy đăng nhập bằng tài khoản Admin/Moderator.</td></tr>`;}
  }
  async function loadJobs() {
      const body = $('#jobsTable');
      if (!body) return;

      body.innerHTML = '<tr><td colspan="7" class="empty-cell">Đang tải...</td></tr>';

      try {
          const rows = await api('/api/admin/pending/jobs');

          const q = ($('#jobSearch')?.value || '').toLowerCase();

          // Tìm kiếm theo tiêu đề, doanh nghiệp, mô tả và địa điểm
          const filtered = rows.filter(x =>
              `${x.title} ${x.company_name} ${x.description} ${x.location || ''}`
                  .toLowerCase()
                  .includes(q)
          );

          $('#jobCount').textContent = `${filtered.length} tin`;

          body.innerHTML = filtered.length
              ? filtered.map(x => `
                  <tr>
                      <td>
                          <div class="cell-main">${esc(x.title)}</div>
                          <div class="cell-sub">Mã tin #${x.id}</div>
                      </td>
                      <td>${esc(x.company_name)}</td>
                      <td>${esc(x.location || '—')}</td>
                      <td>
                          <div class="cell-sub" title="${esc(x.description)}">
                              ${esc(x.description || '')}
                          </div>
                      </td>
                      <td>${date(x.created_at)}</td>
                      <td>${status('pending')}</td>
                      <td>
                          <div class="actions">
                              <button class="action-btn action-approve"
                                  data-job-approve="${x.id}">Duyệt</button>
                              <button class="action-btn action-reject"
                                  data-job-reject="${x.id}">Từ chối</button>
                          </div>
                      </td>
                  </tr>
              `).join('')
              : '<tr><td colspan="7" class="empty-cell">Không có tin tuyển dụng phù hợp.</td></tr>';

      } catch (e) {
          body.innerHTML = `<tr><td colspan="7" class="empty-cell">${esc(e.message)}. Hãy đăng nhập bằng tài khoản Admin/Moderator.</td></tr>`;
      }
  }
  async function loadUsers(){const body=$('#usersTable');if(!body)return;body.innerHTML='<tr><td colspan="5" class="empty-cell">Đang tải...</td></tr>';try{const p=new URLSearchParams();if($('#userRole').value)p.set('role',$('#userRole').value);if($('#userActive').value)p.set('is_active',$('#userActive').value);const rows=await api('/api/admin/users?'+p);const q=$('#userSearch').value.toLowerCase();const filtered=rows.filter(x=>x.email.toLowerCase().includes(q));body.innerHTML=filtered.length?filtered.map(x=>`<tr><td><div class="cell-main">${esc(x.email)}</div><div class="cell-sub">Tài khoản #${x.id}</div></td><td>${esc(x.role)}</td><td>${date(x.created_at)}</td><td>${status(x.is_active?'active':'inactive')}</td><td><div class="actions"><button class="action-btn action-edit" data-user-toggle="${x.id}" data-active="${x.is_active?0:1}">${x.is_active?'Khóa':'Mở khóa'}</button></div></td></tr>`).join(''):'<tr><td colspan="5" class="empty-cell">Không tìm thấy tài khoản.</td></tr>';}catch(e){body.innerHTML=`<tr><td colspan="5" class="empty-cell">${esc(e.message)}</td></tr>`;}}
  async function loadCategories(){const body=$('#categoriesTable');if(!body)return;try{const rows=await api('/api/admin/categories');const q=$('#categorySearch').value.toLowerCase();const filtered=rows.filter(x=>`${x.name} ${x.description||''}`.toLowerCase().includes(q));body.innerHTML=filtered.length?filtered.map(x=>`<tr><td><div class="cell-main">${esc(x.name)}</div><div class="cell-sub">Mã danh mục #${x.id}</div></td><td>${esc(x.description||'—')}</td><td>${status(x.is_active?'active':'inactive')}</td><td><div class="actions">${role==='admin'?`<button class="action-btn action-edit" data-category-edit="${x.id}">Sửa</button><button class="action-btn action-reject" data-category-delete="${x.id}">Xóa</button>`:'—'}</div></td></tr>`).join(''):'<tr><td colspan="4" class="empty-cell">Chưa có danh mục.</td></tr>';}catch(e){body.innerHTML=`<tr><td colspan="4" class="empty-cell">${esc(e.message)}</td></tr>`;}}
  async function loadContents(){const body=$('#contentsTable');if(!body)return;try{const rows=await api('/api/admin/career-contents');const q=$('#contentSearch').value.toLowerCase();const st=$('#contentStatus').value;const filtered=rows.filter(x=>`${x.title} ${x.summary||''}`.toLowerCase().includes(q)&&(!st||x.status===st));body.innerHTML=filtered.length?filtered.map(x=>`<tr><td><div class="cell-main">${esc(x.title)}</div><div class="cell-sub">${esc(x.summary||'')}</div></td><td>${esc(x.category||'—')}</td><td>${date(x.updated_at)}</td><td>${status(x.status)}</td><td><div class="actions"><button class="action-btn action-edit" data-content-edit="${x.id}">Sửa</button><button class="action-btn action-reject" data-content-delete="${x.id}">Xóa</button></div></td></tr>`).join(''):'<tr><td colspan="5" class="empty-cell">Chưa có nội dung phù hợp.</td></tr>';}catch(e){body.innerHTML=`<tr><td colspan="5" class="empty-cell">${esc(e.message)}</td></tr>`;}}
  async function loadHistory(){const body=$('#historyTable');if(!body)return;try{const type=$('#historyType').value;const rows=await api('/api/admin/review-histories'+(type?'?entity_type='+type:''));body.innerHTML=rows.length?rows.map(x=>`<tr><td>${x.entity_type==='company'?'Doanh nghiệp':'Tin tuyển dụng'}</td><td>#${x.entity_id}</td><td>${status(x.action)}</td><td>${esc(x.reviewer_email||'—')}</td><td><div class="cell-sub" title="${esc(x.note||'')}">${esc(x.note||'—')}</div></td><td>${date(x.created_at)}</td></tr>`).join(''):'<tr><td colspan="6" class="empty-cell">Chưa có lịch sử kiểm duyệt.</td></tr>';}catch(e){body.innerHTML=`<tr><td colspan="6" class="empty-cell">${esc(e.message)}</td></tr>`;}}
  function formatDateTime(value){
    if(!value)return '—';
    const normalized=value.includes('T')?value:value.replace(' ','T')+'Z';
    const parsed=new Date(normalized);
    return Number.isNaN(parsed.getTime())?value:parsed.toLocaleString('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
  }
  function renderRecentReviews(rows){
    const body=$('#recentReviews');
    if(!body)return;
    if(!Array.isArray(rows)||!rows.length){
      body.innerHTML='<tr><td colspan="5" class="empty-cell">Chưa có hoạt động kiểm duyệt.</td></tr>';
      return;
    }
    body.innerHTML=rows.map(item=>{
      const type=item.entity_type==='company'?'Doanh nghiệp':'Tin tuyển dụng';
      return `<tr>
        <td>${type}</td>
        <td><div class="cell-main">${esc(item.entity_name||`${type} #${item.entity_id}`)}</div><div class="cell-sub">Mã #${esc(item.entity_id)}</div></td>
        <td>${status(item.action)}</td>
        <td>${esc(item.reviewer_email||'—')}</td>
        <td>${formatDateTime(item.created_at)}</td>
      </tr>`;
    }).join('');
  }
  async function dashboard(){
    const errorBox=$('#dashboardError');
    const refresh=$('#refreshDashboard');
    if(errorBox){errorBox.classList.add('hidden');errorBox.textContent='';}
    if(refresh){refresh.disabled=true;refresh.classList.add('is-loading');}
    try{
      const data=await api('/api/admin/dashboard/summary');
      const s=data.stats||{};
      const set=(selector,value)=>{const el=$(selector);if(el)el.textContent=Number(value??0).toLocaleString('vi-VN');};
      set('#statActiveUsers',s.active_users);
      set('#statActiveStudents',s.active_students);
      set('#statApprovedCompanies',s.companies_approved);
      set('#statTotalCompanies',s.companies_total);
      set('#statApprovedJobs',s.jobs_approved);
      set('#statTotalJobs',s.jobs_total);
      set('#statApplications',s.applications_total);
      set('#statPendingApplications',s.applications_pending);
      set('#statPendingCompanies',s.companies_pending);
      set('#statPendingJobs',s.jobs_pending);
      set('#queueCompanies',s.companies_pending);
      set('#queueJobs',s.jobs_pending);
      set('#reviewsToday',s.reviews_today);
      set('#statCategories',s.categories_active);
      set('#statPublishedContents',s.contents_published);
      set('#statDraftContents',s.contents_draft);
      set('#statTotalContents',s.contents_total);
      const totalContents=$('#statTotalContents');
      if(totalContents)totalContents.textContent=`${Number(s.contents_total||0).toLocaleString('vi-VN')} nội dung trong hệ thống`;
      renderRecentReviews(data.recent_reviews);
    }catch(e){
      if(errorBox){errorBox.textContent=`Không thể tải dữ liệu tổng quan: ${e.message}. Hãy kiểm tra phiên đăng nhập và kết nối máy chủ.`;errorBox.classList.remove('hidden');}
      if($('#recentReviews'))$('#recentReviews').innerHTML=`<tr><td colspan="5" class="empty-cell">${esc(e.message)}</td></tr>`;
      toast(e.message,true);
    }finally{
      if(refresh){refresh.disabled=false;refresh.classList.remove('is-loading');}
    }
  }
  document.addEventListener('click',async e=>{
    const b=e.target.closest('button');if(!b)return;
    if(b.dataset.companyApprove)return review('companies',b.dataset.companyApprove,'approved');if(b.dataset.companyReject)return review('companies',b.dataset.companyReject,'rejected');if(b.dataset.jobApprove)return review('jobs',b.dataset.jobApprove,'approved');if(b.dataset.jobReject)return review('jobs',b.dataset.jobReject,'rejected');
    if(b.dataset.userToggle){try{await api(`/api/admin/users/${b.dataset.userToggle}`,{method:'PUT',body:JSON.stringify({is_active:Number(b.dataset.active)})});toast('Đã cập nhật tài khoản.');loadUsers();}catch(e){toast(e.message,true);}}
    if(b.dataset.categoryDelete&&confirm('Xóa danh mục này?')){try{await api(`/api/admin/categories/${b.dataset.categoryDelete}`,{method:'DELETE'});toast('Đã xóa danh mục.');loadCategories();}catch(e){toast(e.message,true);}}
    if(b.dataset.categoryEdit){try{const x=await api(`/api/admin/categories/${b.dataset.categoryEdit}`);const f=$('#categoryForm');f.dataset.id=x.id;f.elements.name.value=x.name;f.elements.description.value=x.description||'';f.elements.is_active.checked=!!x.is_active;$('#categoryModalTitle').textContent='Cập nhật danh mục';$('#categoryModal').showModal();}catch(e){toast(e.message,true);}}
    if(b.dataset.contentDelete&&confirm('Xóa nội dung này?')){try{await api(`/api/admin/career-contents/${b.dataset.contentDelete}`,{method:'DELETE'});toast('Đã xóa nội dung.');loadContents();}catch(e){toast(e.message,true);}}
    if(b.dataset.contentEdit){try{const x=await api(`/api/admin/career-contents/${b.dataset.contentEdit}`);const f=$('#contentForm');f.dataset.id=x.id;['title','summary','body','category','status'].forEach(k=>f.elements[k].value=x[k]||'');$('#contentModalTitle').textContent='Cập nhật nội dung';$('#contentModal').showModal();}catch(e){toast(e.message,true);}}
  });
  $('#menuToggle')?.addEventListener('click',()=>$('#sidebar').classList.toggle('open'));
  $('#logoutBtn')?.addEventListener('click',async()=>{try{await api('/api/auth/logout',{method:'POST',body:'{}'});location.href='/admin/login';}catch(e){toast(e.message,true);}});
  api('/api/auth/me').then(me=>{const email=$('#staffEmail');if(email)email.textContent=me.email;const avatar=$('.avatar');if(avatar)avatar.textContent=(me.email||'S')[0].toUpperCase();const greeting=$('#dashboardGreeting');if(greeting)greeting.textContent=me.email||'Staff';}).catch(()=>{});
  if(page==='dashboard'){
    const dateEl=$('#dashboardDate');
    if(dateEl)dateEl.textContent=new Date().toLocaleDateString('vi-VN',{weekday:'long',day:'2-digit',month:'long',year:'numeric'});
    $('#refreshDashboard')?.addEventListener('click',dashboard);
    dashboard();
  }
  if(page==='companies'){loadCompanies();bindSearch('#companySearch',loadCompanies);$('#refreshCompanies').onclick=loadCompanies;}
  if(page==='jobs'){loadJobs();bindSearch('#jobSearch',loadJobs);$('#refreshJobs').onclick=loadJobs;}
  if(page==='users'){
    loadUsers();bindSearch('#userSearch',loadUsers);$('#userRole').onchange=loadUsers;$('#userActive').onchange=loadUsers;$('#refreshUsers').onclick=loadUsers;
    $('#createUserBtn').onclick=()=>$('#userModal').showModal();$('#userForm').role.onchange=e=>$('#companyNameWrap').classList.toggle('hidden',e.target.value!=='business');
    $('#userForm').addEventListener('submit',async e=>{if(e.submitter?.value==='cancel')return;e.preventDefault();const f=e.currentTarget;const data=Object.fromEntries(new FormData(f));try{await api('/api/admin/users',{method:'POST',body:JSON.stringify(data)});$('#userModal').close();f.reset();toast('Đã tạo tài khoản.');loadUsers();}catch(err){toast(err.message,true);}});
  }
  if(page==='categories'){
    loadCategories();bindSearch('#categorySearch',loadCategories);$('#refreshCategories').onclick=loadCategories;
    $('#createCategoryBtn')?.addEventListener('click',()=>{const f=$('#categoryForm');f.reset();delete f.dataset.id;f.elements.is_active.checked=true;$('#categoryModalTitle').textContent='Thêm danh mục';$('#categoryModal').showModal();});
    $('#categoryForm').addEventListener('submit',async e=>{if(e.submitter?.value==='cancel')return;e.preventDefault();const f=e.currentTarget;const data={name:f.elements.name.value,description:f.elements.description.value,is_active:f.elements.is_active.checked?1:0};try{if(f.dataset.id)await api(`/api/admin/categories/${f.dataset.id}`,{method:'PUT',body:JSON.stringify(data)});else await api('/api/admin/categories',{method:'POST',body:JSON.stringify(data)});$('#categoryModal').close();toast('Đã lưu danh mục.');loadCategories();}catch(err){toast(err.message,true);}});
  }
  if(page==='contents'){
    loadContents();bindSearch('#contentSearch',loadContents);$('#contentStatus').onchange=loadContents;$('#refreshContents').onclick=loadContents;
    $('#createContentBtn').onclick=()=>{const f=$('#contentForm');f.reset();delete f.dataset.id;$('#contentModalTitle').textContent='Tạo nội dung';$('#contentModal').showModal();};
    $('#contentForm').addEventListener('submit',async e=>{if(e.submitter?.value==='cancel')return;e.preventDefault();const f=e.currentTarget;const data=Object.fromEntries(new FormData(f));try{if(f.dataset.id)await api(`/api/admin/career-contents/${f.dataset.id}`,{method:'PUT',body:JSON.stringify(data)});else await api('/api/admin/career-contents',{method:'POST',body:JSON.stringify(data)});$('#contentModal').close();toast('Đã lưu nội dung.');loadContents();}catch(err){toast(err.message,true);}});
  }
  if(page==='history'){loadHistory();$('#historyType').onchange=loadHistory;$('#refreshHistory').onclick=loadHistory;}
})();