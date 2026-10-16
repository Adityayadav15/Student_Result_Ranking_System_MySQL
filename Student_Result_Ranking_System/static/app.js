const form = document.getElementById('studentForm');
let students = [];
let toastTimer;
function toast(message, error=false){
  const el=document.getElementById('toast');el.textContent=message;el.className='toast show'+(error?' error':'');
  clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.className='toast',3000);
}
function selectedAlgorithm(){return document.querySelector('input[name="sortAlgo"]:checked').value;}
function marksFromForm(){return [1,2,3,4,5].map(i=>Number(document.getElementById(`subject${i}`).value));}
function resultFor(marks){
  const total=marks.reduce((a,b)=>a+b,0), percentage=total/5, passed=marks.every(m=>m>=35);
  let grade='F',status='Fail';
  if(passed){status='Pass';grade=percentage>=90?'A+':percentage>=80?'A':percentage>=70?'B':percentage>=60?'C':percentage>=50?'D':'E';}
  return {total,percentage,grade,status};
}
function updatePreview(){
  const marks=marksFromForm(),r=resultFor(marks);
  document.getElementById('liveTotal').textContent=`Total: ${Number.isFinite(r.total)?r.total.toFixed(1).replace(/\.0$/,''):'0'} / 500`;
  document.getElementById('livePercentage').textContent=`${r.percentage.toFixed(2)}%`;
  document.getElementById('liveGrade').textContent=r.grade;
  document.getElementById('liveStatus').textContent=r.status;
}
[1,2,3,4,5].forEach(i=>document.getElementById(`subject${i}`).addEventListener('input',updatePreview));
document.querySelectorAll('input[name="sortAlgo"]').forEach(input=>input.addEventListener('change',()=>{
  document.querySelectorAll('.sort-option').forEach(el=>el.classList.toggle('selected',el.querySelector('input').checked));
}));
function formData(){
  const data={roll_no:document.getElementById('rollNo').value.trim(),name:document.getElementById('studentName').value.trim(),
    class_name:document.getElementById('className').value.trim(),department:document.getElementById('department').value.trim()||'CSE'};
  marksFromForm().forEach((mark,i)=>data[`subject${i+1}`]=mark);
  return data;
}
function resetEditor(){
  document.getElementById('studentId').value='';
  document.getElementById('formTitle').textContent='Add a student';
  document.getElementById('saveBtn').textContent='＋ Save student result';
  document.getElementById('cancelEditBtn').classList.add('hidden');
  form.reset();document.getElementById('department').value='CSE';
  [1,2,3,4,5].forEach(i=>document.getElementById(`subject${i}`).value=0);
  updatePreview();
}
document.getElementById('resetBtn').addEventListener('click',()=>setTimeout(resetEditor,0));
document.getElementById('cancelEditBtn').addEventListener('click',resetEditor);
form.addEventListener('submit',async e=>{
  e.preventDefault();
  const data=formData(),id=document.getElementById('studentId').value;
  if(marksFromForm().some(m=>!Number.isFinite(m)||m<0||m>100)){toast('Each subject mark must be between 0 and 100.',true);return;}
  const btn=document.getElementById('saveBtn');btn.disabled=true;btn.textContent='Saving…';
  try{
    const res=await fetch(id?`/api/students/${id}`:'/api/students',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const body=await res.json();if(!res.ok)throw new Error(body.error||'Could not save result.');
    toast(body.message);resetEditor();await refreshAll();
  }catch(err){toast(err.message,true);}
  finally{btn.disabled=false;btn.textContent=document.getElementById('studentId').value?'Update student result':'＋ Save student result';}
});
function escapeHtml(value){
  return String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function renderStudents(){
  const query=document.getElementById('searchInput').value.trim().toLowerCase();
  const filtered=students.filter(s=>s.name.toLowerCase().includes(query)||s.roll_no.toLowerCase().includes(query)||s.class_name.toLowerCase().includes(query));
  const body=document.getElementById('studentRows');
  document.getElementById('tableCount').textContent=`Showing ${filtered.length} of ${students.length} students`;
  if(!filtered.length){body.innerHTML=`<tr><td colspan="9" class="empty">${students.length?'No matching students.':'No student results yet. Add the first student using the form above.'}</td></tr>`;return;}
  body.innerHTML=filtered.map(s=>`<tr>
    <td><span class="rank-number ${s.rank<=3?'rank-medal':''}">${s.rank<=3?['🥇','🥈','🥉'][s.rank-1]:`#${s.rank}`}</span></td>
    <td><span class="student-name">${escapeHtml(s.name)}</span><span class="student-sub">${escapeHtml(s.department)}</span></td>
    <td>${escapeHtml(s.roll_no)}</td><td>${escapeHtml(s.class_name)}</td>
    <td>${Number(s.total).toFixed(1).replace(/\.0$/,'')}</td><td><span class="percentage">${Number(s.percentage).toFixed(2)}%</span></td>
    <td><span class="grade-pill ${s.grade.toLowerCase().replace('+','plus')}">${escapeHtml(s.grade)}</span></td>
    <td><span class="status-pill ${s.status}">${escapeHtml(s.status)}</span></td>
    <td><button class="action-btn" data-edit="${s.id}">Edit</button><button class="action-btn delete" data-delete="${s.id}">Delete</button></td>
  </tr>`).join('');
}
document.getElementById('studentRows').addEventListener('click',async e=>{
  const edit=e.target.closest('[data-edit]'),del=e.target.closest('[data-delete]');
  if(edit){
    const s=students.find(x=>x.id===Number(edit.dataset.edit));if(!s)return;
    document.getElementById('studentId').value=s.id;
    document.getElementById('rollNo').value=s.roll_no;document.getElementById('studentName').value=s.name;
    document.getElementById('className').value=s.class_name;document.getElementById('department').value=s.department;
    s.marks.forEach((mark,i)=>document.getElementById(`subject${i+1}`).value=mark);
    document.getElementById('formTitle').textContent='Edit student result';document.getElementById('saveBtn').textContent='Save changes';
    document.getElementById('cancelEditBtn').classList.remove('hidden');updatePreview();
    document.getElementById('formPanel').scrollIntoView({behavior:'smooth',block:'start'});
  }
  if(del){
    const s=students.find(x=>x.id===Number(del.dataset.delete));if(!s)return;
    if(!confirm(`Delete ${s.name} (${s.roll_no}) and their result?`))return;
    try{const res=await fetch(`/api/students/${s.id}`,{method:'DELETE'}),body=await res.json();if(!res.ok)throw new Error(body.error||'Delete failed.');toast(body.message);await refreshAll();}
    catch(err){toast(err.message,true);}
  }
});
document.getElementById('searchInput').addEventListener('input',renderStudents);
async function refreshStudents(){
  const res=await fetch('/api/students');if(!res.ok)throw new Error('Could not load student records.');
  students=await res.json();renderStudents();
}
async function refreshStats(){
  const res=await fetch('/api/stats'),d=await res.json();
  document.getElementById('totalStudents').textContent=d.student_count;
  document.getElementById('passRate').textContent=`${d.pass_rate}%`;
  document.getElementById('passCount').textContent=`${d.pass_count} students passed`;
  document.getElementById('classAverage').textContent=`${d.average_percentage}%`;
  document.getElementById('topStudent').textContent=d.top_student?d.top_student.name:'—';
  document.getElementById('topStudentMeta').textContent=d.top_student?`${d.top_student.roll_no} · ${Number(d.top_student.percentage).toFixed(2)}% · Grade ${d.top_student.grade}`:'Add results to see the topper';
}
async function refreshHistory(){
  const res=await fetch('/api/ranking-history'),rows=await res.json(),target=document.getElementById('rankingHistory');
  if(!rows.length){target.innerHTML='<p class="empty">Ranking runs will appear here.</p>';return;}
  target.innerHTML=rows.map(r=>`<div class="history-item"><div><b>${escapeHtml(r.algorithm)} sort</b><small>${r.student_count} students ranked</small></div><span class="history-time">${r.elapsed_ms} ms</span><span class="history-time">${escapeHtml(r.created_at)}</span></div>`).join('');
}
async function refreshAll(){await Promise.all([refreshStudents(),refreshStats(),refreshHistory()]);}
document.getElementById('refreshBtn').addEventListener('click',async()=>{try{await refreshAll();toast('Dashboard refreshed.');}catch(e){toast(e.message,true);}});
document.getElementById('historyRefresh').addEventListener('click',refreshHistory);
document.getElementById('rankBtn').addEventListener('click',async()=>{
  const btn=document.getElementById('rankBtn');btn.disabled=true;btn.textContent='Ranking…';
  try{
    const res=await fetch('/api/rank',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({algorithm:selectedAlgorithm()})});
    const data=await res.json();if(!res.ok)throw new Error(data.error||'Ranking failed.');
    students=data.students;renderStudents();await Promise.all([refreshStats(),refreshHistory()]);
    const labels={MERGE:'Merge Sort',QUICK:'Quick Sort',BUILTIN:'Python built-in sort'};
    document.getElementById('algorithmResult').textContent=`${labels[data.algorithm]||data.algorithm} ranked ${data.student_count} students in ${data.elapsed_ms} ms.`;
    toast('Ranking completed successfully.');
  }catch(e){toast(e.message,true);}
  finally{btn.disabled=false;btn.textContent='↕ Rank students';}
});
document.getElementById('exportBtn').addEventListener('click',async()=>{
  try{
    const res=await fetch('/api/export'),data=await res.json();
    const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download='student_rankings.json';document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
    toast('Ranked JSON file exported.');
  }catch(e){toast('Export failed.',true);}
});
updatePreview();
refreshAll().catch(e=>toast(e.message,true));
