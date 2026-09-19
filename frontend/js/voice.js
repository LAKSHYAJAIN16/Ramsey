export class VoiceRecorder {
  constructor({ onResult, onError, onSpeakingChange }) {
    this.onResult = onResult;
    this.onError = onError;
    this.onSpeakingChange = onSpeakingChange || (() => {});
    this.mediaRecorder = null;
    this.chunks = [];
    this.stream = null;
    this.currentAudio = null;
  }

  async start() {
    if (this.starting || this.mediaRecorder?.state === 'recording') return false;
    this.starting = true;
    this.interrupt(); // pressing talk always stops Ramsey mid-sentence first
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      this.starting = false;
      this.onError(`Mic access denied or unavailable: ${err.message}`);
      return false;
    }
    this.chunks = [];
    this.mediaRecorder = new MediaRecorder(this.stream);
    this.mediaRecorder.ondataavailable = (e) => this.chunks.push(e.data);
    this.mediaRecorder.start();
    this.starting = false;
    return true;
  }

  stop(sendFn) {
    if (!this.mediaRecorder || this.mediaRecorder.state !== 'recording') return;
    this.mediaRecorder.onstop = async () => {
      const blob = new Blob(this.chunks, { type: "audio/webm" });
      this.stream.getTracks().forEach((t) => t.stop());
      try {
        const result = await sendFn(blob);
        this.onResult(result);
        this.playReply(result);
      } catch (err) {
        this.onError(err.message);
      }
    };
    this.mediaRecorder.stop();
  }

  playReply(result) {
    if (!result.audio_url) return; // no TTS audio (e.g. Backboard not wired yet)
    const audio = new Audio(result.audio_url); // Backboard returns a temporary audio URL, not inline audio
    this.currentAudio = audio;
    this.onSpeakingChange(true);
    audio.addEventListener("ended", () => this.onSpeakingChange(false));
    audio.play().catch(() => this.onSpeakingChange(false));
  }

  interrupt() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
      this.onSpeakingChange(false);
    }
  }
}
