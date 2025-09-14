async function loadScripts() {
  const res = await fetch('/admin/scripts');
  const rows = await res.json();
  const area = document.getElementById('scriptsArea');
  if (!rows.length) { area.innerHTML = '<p>No scripts found</p>'; return; }
  let html = '<table><tr><th>Student</th><th>Question</th><th>Answer</th><th>Actions</th></tr>';
  rows.forEach(r => {
    html += `<tr>
      <td>${r.name}</td>
      <td>${r.question_text}</td>
      <td>${r.answer_text.substring(0,300)}</td>
      <td>
        <button onclick="runPlag(${r.answer_id})">Plagiarism</button>
        <button onclick="openEval(${r.user_id},${r.exam_id})">Evaluate</button>
      </td>
    </tr>`;
  });
  html += '</table>';
  area.innerHTML = html;
}

async function runPlag(answerId) {
  const res = await fetch('/admin/plagiarism', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({answer_id:answerId})
  });
  const j = await res.json();
  alert('Highest similarity: ' + (j.max_score || j.max) );
}

function openEval(userId, examId){
  const marks = prompt('Enter total marks for this student (number):');
  if (!marks) return;
  fetch('/admin/evaluate', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({user_id:userId, exam_id:examId, marks:[{q_id:0, mark:parseFloat(marks)}]})
  }).then(r=>r.json()).then(j=>{
    if (j.success) alert('Marks uploaded. Total: ' + j.total);
    else alert('Error: ' + (j.message||'unknown'));
    loadScripts();
  });
}
