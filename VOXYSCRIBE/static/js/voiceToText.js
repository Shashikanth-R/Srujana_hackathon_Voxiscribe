// Voice recording helpers using MediaRecorder and Web Speech API for realtime transcription
let _mediaRecorder = null;
let _recordedChunks = [];
let _speechRecognition = null;
let _isDictating = false;

exported = {};
// Record audio as a wav/webm blob
function startRecording() {
  _recordedChunks = [];
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('Microphone not supported in this browser');
    return;
  }
  navigator.mediaDevices.getUserMedia({audio:true}).then(stream=>{
    _mediaRecorder = new MediaRecorder(stream);
    _mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size) _recordedChunks.push(e.data); };
    _mediaRecorder.start();
  });
}

function stopRecording() {
  return new Promise((resolve) => {
    if (!_mediaRecorder) return resolve(null);
    _mediaRecorder.onstop = () => {
      const blob = new Blob(_recordedChunks, {type: 'audio/webm'});
      resolve(blob);
    };
    _mediaRecorder.stop();
    _mediaRecorder = null;
  });
}

// Simple dictation using Web Speech API (client-side) - used for real-time dictation and voice commands
function startDictation(onResultCallback) {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('Web Speech API not supported in this browser. Use Chrome/Edge for demo.');
    return;
  }
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  _speechRecognition = new SpeechRecognition();
  _speechRecognition.lang = 'en-IN';
  _speechRecognition.interimResults = true;
  _speechRecognition.continuous = true;
  _speechRecognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    if (onResultCallback) onResultCallback(transcript);
  };
  _speechRecognition.start();
  _isDictating = true;
}

function stopDictation() {
  if (_speechRecognition) {
    _speechRecognition.stop();
    _speechRecognition = null;
  }
  _isDictating = false;
}

function isDictating() { return _isDictating; }

// Expose
window.startRecording = startRecording;
window.stopRecording = stopRecording;
window.startDictation = startDictation;
window.stopDictation = stopDictation;
window.isDictating = isDictating;
