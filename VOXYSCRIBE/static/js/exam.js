// Controls exam UI: timer, autosave, navigation, dictation integration
let currentIndex = 0;
let questions = window.EXAM_DATA.questions || [];
let examId = window.EXAM_DATA.exam_id;
let autosaveTimer = null;
let tabStrikes = 0;

function formatTime(seconds) {
  const m = Math.floor(seconds/60).toString().padStart(2,'0');
  const s = (seconds%60).toString().padStart(2,'0');
  return `${m}:${s}`;
}

function startTimer(minutes) {
  let seconds = minutes*60;
  const timeEl = document.getElementById('time');
  timeEl.innerText = formatTime(seconds);
  const t = setInterval(()=> {
    seconds--;
    timeEl.innerText = formatTime(seconds);
    if (seconds <= 0) {
      clearInterval(t);
      alert('Time up! Submitting exam automatically.');
      submitExam();
    }
  }, 1000);
}

function showQuestion(index) {
  const panes = document.querySelectorAll('.question-pane');
  panes.forEach((p, i) => p.style.display = (i===index ? 'block' : 'none'));
  currentIndex = index;
}

function nextQuestion(e) {
  e && e.preventDefault();
  saveCurrentAnswer();
  if (currentIndex < questions.length-1) showQuestion(currentIndex+1);
}
function previousQuestion(e) {
  e && e.preventDefault();
  saveCurrentAnswer();
  if (currentIndex > 0) showQuestion(currentIndex-1);
}

async function saveCurrentAnswer() {
  const q = questions[currentIndex];
  const ta = document.querySelector(`.question-pane[data-index="${currentIndex}"] textarea`);
  const answer_text = ta.value;
  await fetch('/api/exam/save', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({q_id: q.q_id, exam_id: examId, answer_text})
  });
}

function saveAnswer(e) { e && e.preventDefault(); saveCurrentAnswer(); alert('Saved'); }

async function submitExam(e) {
  if (e) e.preventDefault();
  if (!confirm('Are you sure you want to submit? This cannot be undone.')) return;
  await fetch('/api/exam/submit', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({exam_id: examId})
  });
  alert('Submitted. Redirecting to dashboard.');
  window.location = '/student/dashboard';
}

// autosave every 5 seconds
function startAutosave() {
  autosaveTimer = setInterval(saveCurrentAnswer, 5000);
}

document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    tabStrikes++;
    document.getElementById('warn').innerText = `Warning: Tab switched ${tabStrikes}/3`;
    if (tabStrikes >= 3) {
      fetch('/logout', {method:'POST'}).then(()=> window.location='/');
    }
  }
});

// Dictation integration using global start/stop
let dictateActive = false;
function toggleDictation(e) {
  e && e.preventDefault();
  const btn = document.getElementById('dictateBtn');
  if (!dictateActive) {
    // start dictation -> append results to current textarea
    window.startDictation((partialText) => {
      const ta = document.querySelector(`.question-pane[data-index="${currentIndex}"] textarea`);
      ta.value = partialText;
      // also check if voice commands present
      // basic parsing:
      if (partialText.toLowerCase().includes('next') || partialText.toLowerCase().includes('previous') || partialText.toLowerCase().includes('submit') || partialText.toLowerCase().includes('save')) {
        // route to navigation handler
        processVoiceCommand(partialText);
      }
    });
    btn.innerText = 'Stop Dictation';
    dictateActive = true;
  } else {
    window.stopDictation();
    btn.innerText = 'Start Dictation';
    dictateActive = false;
  }
}

// init
window.addEventListener('load', () => {
  startTimer(window.EXAM_DATA.duration_minutes);
  startAutosave();
  showQuestion(0);
});
