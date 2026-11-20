(() => {
"use strict";
const token = localStorage.getItem("access_token");
const role = document.body.dataset.role || "student";
const $ = (id) => document.getElementById(id);
const state = { user:null, courses:[], assignments:[], submissions:[] };
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const list = (data, key) => Array.isArray(data) ? data : (Array.isArray(data?.[key]) ? data[key] : Array.isArray(data?.items) ? data.items : []);
const courseId = c => c.id ?? c.course_id;
const courseName = c => c.course_name || c.name || c.course_code || `Course ${courseId(c)}`;
function signOut(){localStorage.removeItem("access_token");localStorage.removeItem("current_user");location.replace("/login");}
function notify(message, type="success"){
 const n=$("notice"); if(!n)return; n.textContent=message; n.className=`notice ${type}`; n.hidden=false;
 window.scrollTo({top:0,behavior:"smooth"}); setTimeout(()=>{n.hidden=true;},6500);
}
async function api(path, options={}){
 const headers={...(options.headers||{}),Authorization:`Bearer ${token}`};
 if(options.body && !(options.body instanceof FormData)) headers["Content-Type"]="application/json";
 const response=await fetch(path,{...options,headers});
 let data={}; const ct=response.headers.get("content-type")||"";
 if(ct.includes("application/json")){try{data=await response.json()}catch{}}
 else if(!response.ok){data.detail=await response.text();}
 if(!response.ok){if(response.status===401||response.status===403)signOut();throw new Error(data.detail||`Request failed (${response.status})`);}
 return data;
}
function renderCourseCards(target,courses){
 const el=$(target); if(!el)return;
 el.innerHTML=courses.length?courses.map(c=>`<article class="course-item"><div class="course-code">${esc(c.course_code||c.code||"COURSE")}</div><h3>${esc(courseName(c))}</h3><p>${esc(c.description||"No description provided.")}</p><small>Course ID: ${esc(courseId(c))}</small></article>`).join(""):'<div class="empty-state">No courses found.</div>';
}
function fillCourseSelect(id){
 const el=$(id); if(!el)return;
 el.innerHTML=state.courses.map(c=>`<option value="${esc(courseId(c))}">${esc(c.course_code||"")} — ${esc(courseName(c))}</option>`).join("");
 if(!state.courses.length)el.innerHTML='<option value="">Create or enrol in a course first</option>';
}
function setSection(name){
 document.querySelectorAll(".workspace-section").forEach(s=>s.hidden=s.id!==`section-${name}`);
 document.querySelectorAll(".sidebar .nav-link[data-section]").forEach(b=>b.classList.toggle("active",b.dataset.section===name));
 const titles={overview:"Professor Dashboard",courses:"My Courses",materials:"Learning Materials",assignments:"Assignments",submissions:"Submissions & Reviews",grading:"Grading",projects:"Student Projects"};
 if($("page-title"))$("page-title").textContent=titles[name]||"Workspace";
 if($("breadcrumb"))$("breadcrumb").textContent=`Workspace / ${titles[name]||name}`;
 const overview=["overview"].includes(name);
 if($("welcome-panel"))$("welcome-panel").hidden=!overview;
 if($("stats-panel"))$("stats-panel").hidden=!overview;
 if(role==="professor") loadSection(name).catch(e=>notify(e.message,"error"));
}
async function loadCourses(){
 const data=await api("/courses/my"); state.courses=list(data,"courses");
 if($("course-count"))$("course-count").textContent=state.courses.length;
 renderCourseCards("course-list",state.courses); renderCourseCards("courses-panel",state.courses);
 ["note-course","assignment-course","project-course"].forEach(fillCourseSelect);
}
async function loadMaterials(){
 const panel=$("materials-panel"); if(!panel)return;
 if(!state.courses.length)await loadCourses();
 const results=await Promise.all(state.courses.map(async c=>{
   try{return {course:c,notes:list(await api(`/courses/${courseId(c)}/notes`),"notes")};}
   catch(e){return {course:c,error:e.message,notes:[]};}
 }));
 const rows=results.flatMap(r=>r.notes.map(n=>({...n,_course:courseName(r.course)})));
 panel.innerHTML=rows.length?rows.map(n=>`<article class="data-row"><div><strong>${esc(n.title||"Untitled note")}</strong><p>${esc(n._course)} · ${esc(n.description||"")}</p><small>Version ${esc(n.current_version||n.version||1)} · Note ID ${esc(n.id||n.note_id)}</small></div><button class="outline-button" data-download-note="${esc(n.id||n.note_id)}">Download</button></article>`).join(""):'<div class="empty-state">No learning materials found for your courses yet.</div>';
}
async function loadAssignments(){
 if(!state.courses.length)await loadCourses();
 const results=await Promise.all(state.courses.map(async c=>{
   try{return list(await api(`/courses/${courseId(c)}/assignments`),"assignments").map(a=>({...a,_course:courseName(c)}));}
   catch(e){return [];}
 }));
 state.assignments=results.flat();
 const panel=$("assignments-panel");
 if(panel)panel.innerHTML=state.assignments.length?state.assignments.map(a=>`<article class="data-row"><div><strong>${esc(a.title)}</strong><p>${esc(a._course)} · Due: ${esc(a.deadline||"Not specified")}</p><small>Assignment ID ${esc(a.id||a.assignment_id)} · ${esc(a.maximum_marks??a.max_marks??"—")} marks · ${esc(a.status||"")}</small></div><button class="outline-button" data-view-submissions="${esc(a.id||a.assignment_id)}">View submissions</button></article>`).join(""):'<div class="empty-state">No assignments found. Create your first assignment above.</div>';
 const select=$("submission-assignment");
 if(select)select.innerHTML=state.assignments.map(a=>`<option value="${esc(a.id||a.assignment_id)}">${esc(a.title)} (ID ${esc(a.id||a.assignment_id)})</option>`).join("")||'<option value="">No assignments available</option>';
}
async function loadSubmissions(assignment){
 const panel=$("submissions-panel"); if(!panel)return;
 const id=assignment||$("submission-assignment")?.value;
 if(!id){panel.innerHTML='<div class="empty-state">Select an assignment to view submissions.</div>';return;}
 const data=await api(`/assignments/${id}/submissions`); state.submissions=list(data,"submissions");
 panel.innerHTML=state.submissions.length?state.submissions.map(s=>{
 const sid=s.id||s.submission_id;
 return `<article class="data-row"><div><strong>Submission #${esc(sid)}</strong><p>Student: ${esc(s.student_name||s.student_email||s.student_id||"Student")} · Submitted: ${esc(s.submitted_at||s.created_at||"")}</p><small>Status: ${esc(s.status||"Submitted")}</small></div><div class="action-row"><button class="outline-button" data-similarity="${esc(sid)}">Similarity reports</button><button class="outline-button" data-grade="${esc(sid)}">Grade</button></div></article>`;
 }).join(""):'<div class="empty-state">No submissions received for this assignment yet.</div>';
}
async function loadProjects(){
 const panel=$("projects-panel"); if(!panel)return;
 const data=await api("/projects/my"); const projects=list(data,"projects");
 panel.innerHTML=projects.length?projects.map(p=>`<article class="data-row"><div><strong>${esc(p.title||"Student project")}</strong><p>${esc(p.description||"")} · Student ID ${esc(p.student_id??"—")} · Course ID ${esc(p.course_id??"—")}</p><small>Project ID ${esc(p.id||p.project_id)}</small><div id="milestones-${esc(p.id||p.project_id)}" class="nested-list">Loading milestones…</div></div><button class="outline-button" data-add-milestone="${esc(p.id||p.project_id)}">Add milestone</button></article>`).join(""):'<div class="empty-state">No student projects found.</div>';
 for(const p of projects){const id=p.id||p.project_id;try{const ms=list(await api(`/projects/${id}/milestones`),"milestones");const el=$(`milestones-${id}`);if(el)el.innerHTML=ms.length?ms.map(m=>`<div>• ${esc(m.title)} — ${esc(m.status||"pending")}</div>`).join(""):"No milestones yet.";}catch(e){const el=$(`milestones-${id}`);if(el)el.textContent=e.message;}}
}
async function loadSection(name){
 if(name==="overview"||name==="courses")await loadCourses();
 if(name==="materials")await loadMaterials();
 if(name==="assignments")await loadAssignments();
 if(name==="submissions"){if(!state.assignments.length)await loadAssignments();await loadSubmissions();}
 if(name==="projects")await loadProjects();
}
async function initialize(){
 if(!token){location.replace("/login");return;}
 $("logout-button")?.addEventListener("click",signOut);
 if($("today-date"))$("today-date").textContent=new Intl.DateTimeFormat(undefined,{weekday:"short",day:"numeric",month:"short",year:"numeric"}).format(new Date());
 try{
  const profile=await api("/auth/me"); const user=profile.user||profile; state.user=user;
  if(user.role!==role){location.replace(user.role==="professor"?"/professor":"/student");return;}
  const name=user.full_name||user.name||user.email||role;
  if($("user-name"))$("user-name").textContent=name;
  if($("welcome-name"))$("welcome-name").textContent=name.split(" ")[0];
  if($("user-avatar"))$("user-avatar").textContent=name.trim().charAt(0).toUpperCase();
  if($("account-status"))$("account-status").textContent="Active";
  await api(role==="professor"?"/professor/dashboard":"/student/dashboard");
  if(role==="professor"){
   document.querySelectorAll("[data-section]").forEach(b=>b.addEventListener("click",()=>setSection(b.dataset.section)));
   document.querySelectorAll("[data-go]").forEach(b=>b.addEventListener("click",()=>setSection(b.dataset.go)));
   $("refresh-button")?.addEventListener("click",()=>loadCourses().catch(e=>notify(e.message,"error")));
   document.querySelectorAll("[data-reload]").forEach(b=>b.addEventListener("click",()=>loadSection(b.dataset.reload).catch(e=>notify(e.message,"error"))));
   $("course-form")?.addEventListener("submit",createCourse);
   $("note-form")?.addEventListener("submit",uploadNote);
   $("assignment-form")?.addEventListener("submit",createAssignment);
   $("project-form")?.addEventListener("submit",createProject);
   $("submission-assignment")?.addEventListener("change",()=>loadSubmissions().catch(e=>notify(e.message,"error")));
   $("grade-form")?.addEventListener("submit",gradeSubmission);
   $("approve-grade")?.addEventListener("click",()=>gradeAction("approve"));
   $("publish-grade")?.addEventListener("click",()=>gradeAction("publish"));
   document.body.addEventListener("click",handleDynamicClick);
  }
  await loadCourses();
 }catch(e){notify(e.message||"Unable to load dashboard.","error");if($("account-status"))$("account-status").textContent="Check session";}
}
async function createCourse(e){
 e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f.entries());body.semester=Number(body.semester);
 try{await api("/courses",{method:"POST",body:JSON.stringify(body)});e.currentTarget.reset();notify("Course created successfully.");await loadCourses();}
 catch(err){notify(err.message,"error");}
}
async function uploadNote(e){
 e.preventDefault();const f=new FormData(e.currentTarget);const id=f.get("course_id");
 try{await api(`/courses/${id}/notes`,{method:"POST",body:f});e.currentTarget.reset();notify("Learning material uploaded.");await loadMaterials();}
 catch(err){notify(err.message,"error");}
}
async function createAssignment(e){
 e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f.entries());body.course_id=Number(body.course_id);body.maximum_marks=Number(body.maximum_marks);body.deadline=body.deadline?new Date(body.deadline).toISOString():body.deadline;
 try{await api("/assignments",{method:"POST",body:JSON.stringify(body)});e.currentTarget.reset();notify("Assignment created successfully.");await loadAssignments();}
 catch(err){notify(err.message,"error");}
}
async function createProject(e){
 e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f.entries());body.course_id=Number(body.course_id);body.student_id=Number(body.student_id);
 try{await api("/projects",{method:"POST",body:JSON.stringify(body)});e.currentTarget.reset();notify("Student project created.");await loadProjects();}
 catch(err){notify(err.message,"error");}
}
async function gradeSubmission(e){
 e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f.entries());const id=Number(body.submission_id);delete body.submission_id;body.final_marks=Number(body.final_marks);body.suggested_marks=body.suggested_marks?Number(body.suggested_marks):null;
 try{const result=await api(`/submissions/${id}/grade`,{method:"POST",body:JSON.stringify(body)});const grade=result.grade||result;const gid=grade.id||grade.grade_id||result.grade_id;if(gid&&$("grade-action-form"))$("grade-action-form").elements.grade_id.value=gid;$("grade-result").innerHTML=`<div class="success-panel">Grade saved. ${gid?`Grade ID: <strong>${esc(gid)}</strong>`:"Check the API response for the grade ID."}</div>`;notify("Grade saved. Approve and publish it when ready.");}
 catch(err){notify(err.message,"error");}
}
async function gradeAction(action){
 const id=Number($("grade-action-form").elements.grade_id.value);if(!id){notify("Enter a grade ID first.","error");return;}
 try{const result=await api(`/grades/${id}/${action}`,{method:"POST"});notify(action==="approve"?"Grade approved.":"Grade published.");$("grade-result").innerHTML=`<pre>${esc(JSON.stringify(result,null,2))}</pre>`;}
 catch(err){notify(err.message,"error");}
}
async function handleDynamicClick(e){
 const sub=e.target.closest("[data-view-submissions]");if(sub){setSection("submissions");if($("submission-assignment"))$("submission-assignment").value=sub.dataset.viewSubmissions;loadSubmissions(sub.dataset.viewSubmissions).catch(x=>notify(x.message,"error"));return;}
 const sim=e.target.closest("[data-similarity]");if(sim){try{const data=await api(`/submissions/${sim.dataset.similarity}/similarity-reports`);const reports=list(data,"reports");const panel=$("submissions-panel");const reportHtml=reports.length?reports.map(r=>`<div class="report-card"><strong>Report #${esc(r.id||r.report_id)} · ${esc(r.similarity_score??r.score??"—")}%</strong><p>${esc(r.review_decision||r.status||"Pending review")}</p><button class="outline-button" data-review="${esc(r.id||r.report_id)}" data-decision="confirmed">Confirm</button> <button class="outline-button" data-review="${esc(r.id||r.report_id)}" data-decision="not_confirmed">Not confirmed</button></div>`).join(""):"<p>No similarity reports for this submission.</p>";panel.insertAdjacentHTML("beforeend",`<div class="content-card"><h3>Similarity reports for submission ${esc(sim.dataset.similarity)}</h3>${reportHtml}</div>`);}catch(err){notify(err.message,"error");}return;}
 const grade=e.target.closest("[data-grade]");if(grade){setSection("grading");$("grade-form").elements.submission_id.value=grade.dataset.grade;return;}
 const download=e.target.closest("[data-download-note]");if(download){try{const response=await fetch(`/notes/${download.dataset.downloadNote}/download`,{headers:{Authorization:`Bearer ${token}`}});if(!response.ok)throw new Error("Download failed. Please check your access.");const blob=await response.blob();const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=`note-${download.dataset.downloadNote}`;a.click();URL.revokeObjectURL(url);}catch(err){notify(err.message,"error");}return;}
 const review=e.target.closest("[data-review]");if(review){const reason=prompt("Enter the reason for this review decision (at least 5 characters):");if(!reason||reason.trim().length<5){notify("A review reason of at least 5 characters is required.","error");return;}try{await api(`/similarity-reports/${review.dataset.review}/review`,{method:"POST",body:JSON.stringify({review_decision:review.dataset.decision,reason})});notify("Similarity report review saved.");}catch(err){notify(err.message,"error");}return;}
 const add=e.target.closest("[data-add-milestone]");if(add){const title=prompt("Milestone title:");if(!title)return;const description=prompt("Milestone description (optional):")||"";try{await api(`/projects/${add.dataset.addMilestone}/milestones`,{method:"POST",body:JSON.stringify({title,description})});notify("Milestone added.");await loadProjects();}catch(err){notify(err.message,"error");}}
}
if(role==="professor") initialize();
else initialize();
})();