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
    this.interrupt(); // pressing talk always stops Ramsey mid-sentence first
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      this.onError(`Mic access denied or unavailable: ${err.message}`);
      return false;
    }
    this.chunks = [];
    this.mediaRecorder = new MediaRecorder(this.stream);
    this.mediaRecorder.ondataavailable = (e) => this.chunks.push(e.data);
    this.mediaRecorder.start();
    return true;
  }

  stop(sendFn) {
    if (!this.mediaRecorder) return;
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
    if (!result.audio_base64) return; // no TTS audio (e.g. Backboard not wired yet)
    const audio = new Audio(`data:audio/mp3;base64,${result.audio_base64}`);
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
