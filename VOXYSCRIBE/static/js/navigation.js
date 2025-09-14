// simple voice command handling for exam page
// receives transcript string and maps keywords to actions
function processVoiceCommand(transcript) {
  const text = transcript.toLowerCase();
  if (text.includes('next')) {
    document.getElementById('nextBtn').click();
    return;
  }
  if (text.includes('previous') || text.includes('prev')) {
    document.getElementById('prevBtn').click();
    return;
  }
  if (text.includes('save')) {
    document.getElementById('saveBtn').click();
    return;
  }
  if (text.includes('submit')) {
    if (confirm('Submit exam by voice?')) document.getElementById('submitBtn').click();
    return;
  }
}
