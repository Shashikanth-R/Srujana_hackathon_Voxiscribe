// Simple webcam helpers for capture
let _stream = null;
async function startPreview(videoId) {
  const video = document.getElementById(videoId);
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Camera not supported");
    return;
  }
  _stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  video.srcObject = _stream;
  await video.play();
}

function captureImageBlob(videoId) {
  return new Promise((resolve) => {
    const video = document.getElementById(videoId);
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => resolve(blob || null), 'image/jpeg', 0.9);
  });
}
