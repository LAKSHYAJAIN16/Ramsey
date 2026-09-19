using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Ramsey
{
    public class RamseyVoice : MonoBehaviour
    {
        public event Action<string> Notice;
        public event Action<byte[]> Recorded;
        public event Action<bool> RecordingChanged;
        public event Action DoubleTapped;
        [Range(.02f, .9f)] public float tapThreshold = .16f;
        public float speechThreshold = .012f, silenceSeconds = 1.3f;
        public bool Suppressed { get; set; }
        public bool IsRecording { get; private set; }
        public bool Armed { get; private set; }
        const int Rate = 16000, Block = 320;
        readonly DoubleTapDetector detector = new DoubleTapDetector();
        readonly List<float> utterance = new List<float>(Rate * 20);
        AudioClip clip;
        float[] block;
        string device;
        int cursor;
        bool requesting, heardSpeech, suspended;
        float started, lastSpeech, noise = .005f;
        public void Arm() { Armed = true; if (!clip && !requesting && !suspended) StartCoroutine(Begin(false)); }
        public void Toggle()
        {
            if (IsRecording) Stop();
            else if (!Suppressed && !requesting)
            {
                Armed = true;
                if (clip) Listen(); else StartCoroutine(Begin(true));
            }
        }
        IEnumerator Begin(bool listen)
        {
            requesting = true;
            yield return Application.RequestUserAuthorization(UserAuthorization.Microphone);
            requesting = false;
            if (suspended || !isActiveAndEnabled) yield break;
            if (!Application.HasUserAuthorization(UserAuthorization.Microphone)) { Armed = false; Notice?.Invoke("Enable microphone permission to use voice and table taps."); yield break; }
            if (Microphone.devices.Length == 0) { Armed = false; Notice?.Invoke("No microphone is available."); yield break; }
            device = Microphone.devices[0]; clip = Microphone.Start(device, true, 2, Rate);
            if (!clip) { Armed = false; Notice?.Invoke("Could not start the microphone."); yield break; }
            block = new float[Block * clip.channels]; cursor = 0; detector.Reset(Time.unscaledTime);
            if (listen) Listen(); else Notice?.Invoke("Table taps enabled. Microphone listens locally until you open Ramsey.");
        }
        void Listen()
        {
            utterance.Clear(); heardSpeech = false; started = lastSpeech = Time.unscaledTime;
            IsRecording = true; RecordingChanged?.Invoke(true);
            Notice?.Invoke("Listening. Speak your question; pause to send, or tap Stop recording.");
        }
        void Update()
        {
            if (!clip || suspended) return;
            int position = Microphone.GetPosition(device);
            if (position < 0) { Release(); Notice?.Invoke("Microphone stopped. Tap Talk to retry."); return; }
            int available = (position - cursor + clip.samples) % clip.samples;
            while (available >= Block)
            {
                clip.GetData(block, cursor); cursor = (cursor + Block) % clip.samples; available -= Block;
                float peak = 0, sum = 0;
                foreach (float value in block) { peak = Mathf.Max(peak, Mathf.Abs(value)); sum += value * value; }
                float rms = Mathf.Sqrt(sum / block.Length);
                if (IsRecording)
                {
                    utterance.AddRange(block);
                    if (rms > Mathf.Max(speechThreshold, noise * 2.5f)) { heardSpeech = true; lastSpeech = Time.unscaledTime; }
                }
                else if (Armed && !Suppressed)
                {
                    float threshold = Mathf.Max(tapThreshold, noise * 8);
                    if (detector.Sample(peak > rms * 2.5f ? peak : 0, threshold, Time.unscaledTime)) DoubleTapped?.Invoke();
                    noise = Mathf.Lerp(noise, rms, .01f);
                }
                else detector.Reset(Time.unscaledTime);
            }
            if (IsRecording && (Time.unscaledTime - started >= 19 ||
                (heardSpeech && Time.unscaledTime - lastSpeech >= silenceSeconds) ||
                (!heardSpeech && Time.unscaledTime - started >= 7))) Stop();
        }
        void Stop()
        {
            IsRecording = false; RecordingChanged?.Invoke(false); detector.Reset(Time.unscaledTime);
            if (!heardSpeech || utterance.Count < Rate / 5) { Notice?.Invoke("No speech heard. Double tap or press Talk to try again."); return; }
            using (var stream = new MemoryStream()) using (var writer = new BinaryWriter(stream))
            {
                int bytes = utterance.Count * 2;
                writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); writer.Write(36 + bytes);
                writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt ")); writer.Write(16); writer.Write((short)1);
                writer.Write((short)clip.channels); writer.Write(clip.frequency); writer.Write(clip.frequency * clip.channels * 2);
                writer.Write((short)(clip.channels * 2)); writer.Write((short)16);
                writer.Write(System.Text.Encoding.ASCII.GetBytes("data")); writer.Write(bytes);
                foreach (float sample in utterance) writer.Write((short)(Mathf.Clamp(sample, -1, 1) * short.MaxValue));
                Recorded?.Invoke(stream.ToArray());
            }
            utterance.Clear();
        }
        void Release()
        {
            if (clip) { Microphone.End(device); Destroy(clip); clip = null; }
            utterance.Clear(); IsRecording = false; RecordingChanged?.Invoke(false);
        }
        void OnApplicationPause(bool paused) { suspended = paused; if (paused) Release(); else if (Armed) Arm(); }
        void OnDisable() { StopAllCoroutines(); requesting = false; Release(); }
        void OnEnable() { if (Armed) Arm(); }
    }
}
