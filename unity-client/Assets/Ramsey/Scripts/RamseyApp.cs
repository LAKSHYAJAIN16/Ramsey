using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using UnityEngine.InputSystem;

namespace Ramsey
{
    public class RamseyApp : MonoBehaviour
    {
        public OVRCameraRig rig;
        public RectTransform panel;
        public Text titleText, progressText, stepText, statusText, timerText, nextText, voiceText;
        public RamseyButton back, next, timer, ingredients, voice, cameraCheck, connect, recenter, pin;
        RamseyApi api;
        RamseyVoice microphone;
        RamseyVision vision;
        RamseyAnchor anchor;
        Recipe recipe;
        KitchenState state;
        bool busy, showIngredients;
        float timerEnd = -1, nextPoll;
        TouchScreenKeyboard keyboard;
        AudioSource speaker;
        RamseyAssistant assistant;
        bool enteringCode, monitoring, visionBusy, audioBusy, paused, hasPaired;
        float nextFrame;
        public string editorPairCode = "";

        void Awake()
        {
            api = GetComponent<RamseyApi>(); microphone = GetComponent<RamseyVoice>(); vision = GetComponent<RamseyVision>(); anchor = GetComponent<RamseyAnchor>();
            speaker = GetComponent<AudioSource>(); assistant = gameObject.AddComponent<RamseyAssistant>();
            recipe = JsonUtility.FromJson<Recipe>(Resources.Load<TextAsset>("sandwich").text);
            state = new KitchenState { title = recipe.title, total_steps = recipe.steps.Length, step_index = Mathf.Clamp(PlayerPrefs.GetInt("ramsey.offlineStep", 0), 0, recipe.steps.Length - 1), ingredients = recipe.ingredients };
            state.current_step = recipe.steps[state.step_index];
            api.Failed += Fail;
            back.Clicked = () => Navigate("back"); next.Clicked = () => Navigate("next"); timer.Clicked = StartTimer;
            ingredients.Clicked = () => { showIngredients = !showIngredients; Render(); };
            recenter.Clicked = () => { if (!anchor.IsPinned) Recenter(); else Status("Panel is pinned. Unpin it before moving it."); };
            connect.Clicked = ConfigureConnection;
            voice.Clicked = OpenAssistant;
            microphone.DoubleTapped += OpenAssistant;
            cameraCheck.Clicked = () => {
                if (!api.Connected) { Status("Pair with your desktop recipe first."); return; }
                monitoring = !monitoring; nextFrame = 0;
                Status(monitoring ? "Monitoring on: camera frames go to desktop for step checks and plating feedback." : "Monitoring paused.");
                UpdateMonitorLabel();
            };
            pin.Clicked = () => anchor.TogglePin(panel, Status);
            microphone.Notice += Status;
            microphone.Recorded += bytes => { voiceText.text = "Talk to Ramsey"; StartCoroutine(SendVoice(bytes)); };
            microphone.RecordingChanged += recording => { voiceText.text = recording ? "Stop recording" : "Talk to Ramsey"; assistant.SetState(recording ? "Listening" : "Ready"); };
        }
        IEnumerator Start()
        {
            Render(); UpdateMonitorLabel(); Status("Offline recipe • no connection needed");
            yield return new WaitForSeconds(.7f); Recenter();
            anchor.Restore(panel, Status);
        }
        void Update()
        {
            microphone.Suppressed = busy || audioBusy || speaker.isPlaying || !api.Connected || paused;
            if (keyboard != null && keyboard.status == TouchScreenKeyboard.Status.Done)
            {
                var value = keyboard.text; keyboard = null;
                if (enteringCode) { enteringCode = false; StartCoroutine(Pair(value)); }
                else if (api.SetEndpoint(value)) StartCoroutine(Connect()); else Status("Enter a full HTTPS backend address. Development builds also accept HTTP.");
            }
            if (keyboard != null && (keyboard.status == TouchScreenKeyboard.Status.Canceled || keyboard.status == TouchScreenKeyboard.Status.LostFocus)) keyboard = null;
            if (timerEnd > 0)
            {
                int remaining = Mathf.Max(0, Mathf.CeilToInt(timerEnd - Time.unscaledTime));
                timerText.text = remaining > 0 ? $"Timer {remaining / 60:00}:{remaining % 60:00}" : "Timer finished";
                if (remaining == 0) timerEnd = -1;
            }
            if (api.Connected && !busy && !microphone.IsRecording && Time.unscaledTime > nextPoll) { nextPoll = Time.unscaledTime + 5; StartCoroutine(Poll()); }
            if (monitoring && api.Connected && !paused && !visionBusy && !busy && !microphone.IsRecording && !audioBusy && !speaker.isPlaying && Time.unscaledTime >= nextFrame)
            { nextFrame = Time.unscaledTime + 8; StartCoroutine(Monitor()); }
            if (Application.isEditor && Keyboard.current != null)
            {
                if (Keyboard.current.spaceKey.wasPressedThisFrame) OpenAssistant();
                if (Keyboard.current.rightArrowKey.wasPressedThisFrame) Navigate("next");
                if (Keyboard.current.leftArrowKey.wasPressedThisFrame) Navigate("back");
                if (Keyboard.current.rKey.wasPressedThisFrame && !anchor.IsPinned) Recenter();
            }
            if (!Application.isEditor && OVRInput.GetDown(OVRInput.Button.Two) && !anchor.IsPinned) Recenter();
        }
        public void Recenter()
        {
            if (!rig || !panel) return;
            var eye = rig.centerEyeAnchor;
            var forward = Vector3.ProjectOnPlane(eye.forward, Vector3.up).normalized;
            if (forward.sqrMagnitude < .1f) forward = Vector3.forward;
            panel.position = eye.position + forward * 1.3f + Vector3.down * .1f;
            panel.rotation = Quaternion.LookRotation(forward, Vector3.up);
        }
        void ConfigureConnection()
        {
            if (busy) return;
            if (Application.isEditor)
            {
                if (string.IsNullOrEmpty(api.BaseUrl)) api.SetEndpoint("http://127.0.0.1:8000");
                StartCoroutine(Connect()); return;
            }
            keyboard = TouchScreenKeyboard.Open(api.BaseUrl, TouchScreenKeyboardType.URL, false, false, false, false, "https://your-ramsey-server");
            Status("Enter your hosted Ramsey backend address, then press Done.");
        }
        public IEnumerator Connect()
        {
            busy = true; api.Connected = false; Status("Connecting to desktop..."); bool healthy = false;
            yield return api.Get("/health", _ => healthy = true);
            if (healthy)
            {
                if (Application.isEditor)
                {
                    if (!string.IsNullOrWhiteSpace(editorPairCode)) yield return Pair(editorPairCode);
                    else Status("Set RamseyApp's Editor Pair Code to the desktop code, then Connect.");
                }
                else
                {
                    enteringCode = true;
                    keyboard = TouchScreenKeyboard.Open("", TouchScreenKeyboardType.Default, false, false, false, false, "Desktop pairing code");
                    Status("Choose a desktop recipe, click Pair Quest, then enter its code here.");
                }
            }
            busy = false;
        }
        IEnumerator Pair(string code)
        {
            busy = true;
            yield return api.Post("/api/pair", JsonUtility.ToJson(new PairRequest { code = code }), json => {
                var response = JsonUtility.FromJson<PairResponse>(json);
                api.Join(response.session_id, response.token); hasPaired = true; Apply(JsonUtility.ToJson(response.state));
                Status("Paired. Double tap the table to talk. Start monitoring for automatic steps.");
                microphone.Arm();
            });
            busy = false;
        }
        void OpenAssistant()
        {
            if (!api.Connected) { Status("Pair with your desktop recipe to talk with Ramsey."); return; }
            if (busy || audioBusy || speaker.isPlaying) return;
            assistant.Open(panel); microphone.Suppressed = false; microphone.Toggle();
        }
        IEnumerator Poll() { busy = true; yield return api.Get($"/api/session/{api.SessionId}", Apply); busy = false; }
        void Navigate(string action)
        {
            if (busy || microphone.IsRecording) return;
            if (action == "next" && state.step_index == state.total_steps - 1) action = "complete";
            showIngredients = false;
            if (api.Connected) StartCoroutine(Action(action));
            else
            {
                if (hasPaired) { Status("Desktop connection lost. Reconnect to continue your recipe."); return; }
                if (action == "complete") { Status("Pair with your signed-in desktop recipe to save completion points."); return; }
                state.step_index = Mathf.Clamp(state.step_index + (action == "next" ? 1 : -1), 0, recipe.steps.Length - 1);
                state.current_step = recipe.steps[state.step_index]; PlayerPrefs.SetInt("ramsey.offlineStep", state.step_index); PlayerPrefs.Save(); Render();
            }
        }
        IEnumerator Action(string action)
        {
            busy = true;
            yield return api.Post($"/api/session/{api.SessionId}/action", JsonUtility.ToJson(new SessionAction { action = action }), Apply);
            busy = false;
        }
        void StartTimer()
        {
            if (busy) return;
            if (api.Connected) StartCoroutine(Action("start_timer"));
            else { timerEnd = Time.unscaledTime + 300; Status("Five-minute timer started."); }
        }
        void Apply(string json)
        {
            var updated = JsonUtility.FromJson<KitchenState>(json);
            if (updated == null || updated.total_steps == 0) return;
            state = updated;
            if (state.timers != null && state.timers.Length > 0) timerEnd = Time.unscaledTime + state.timers[state.timers.Length - 1].remaining_seconds;
            else { timerEnd = -1; timerText.text = "No active timer"; }
            Render();
        }
        void Render()
        {
            titleText.text = state.title;
            progressText.text = $"Step {state.step_index + 1} of {state.total_steps}";
            stepText.text = showIngredients ? string.Join("\n", state.ingredients ?? Array.Empty<string>()) : state.current_step;
            back.Available = state.step_index > 0;
            next.Available = !state.completed;
            nextText.text = state.completed ? $"Complete! +{state.points} points" : state.step_index < state.total_steps - 1 ? "Next step" : "Finish recipe";
        }
        IEnumerator SendVoice(byte[] bytes)
        {
            assistant.SetState("Thinking");
            busy = true; Status("Ramsey is listening…");
            yield return api.Upload("/api/chat/voice", "audio", bytes, "voice.wav", "audio/wav", json =>
            {
                var response = JsonUtility.FromJson<ChatResponse>(json);
                Status((string.IsNullOrEmpty(response.transcript) ? "" : "You: " + response.transcript + "\n") + "Ramsey: " + response.reply);
                if (response.state != null) Apply(JsonUtility.ToJson(response.state));
                if (response.recipe != null) recipe = response.recipe;
                if (!string.IsNullOrEmpty(response.audio_url)) StartCoroutine(PlayAudio(response.audio_url));
                else assistant.SetState("Ready - reply shown");
            });
            busy = false;
        }
        void UpdateMonitorLabel()
        {
            var label = cameraCheck.GetComponentInChildren<Text>();
            if (label) label.text = monitoring ? "Pause monitoring" : "Start monitoring";
        }
        IEnumerator Monitor()
        {
            visionBusy = true; byte[] frame = null;
            yield return vision.Capture(bytes => frame = bytes, message => { if (!microphone.IsRecording && !busy) Status(message); });
            if (frame == null) { monitoring = false; UpdateMonitorLabel(); visionBusy = false; yield break; }
            if (!monitoring || paused) { visionBusy = false; yield break; }
            yield return api.Upload("/api/vision/assist", "photo", frame, "kitchen.jpg", "image/jpeg", json => {
                if (!monitoring || paused) return;
                var response = JsonUtility.FromJson<AssistResponse>(json);
                if (response.state != null) Apply(JsonUtility.ToJson(response.state));
                if (!string.IsNullOrEmpty(response.message) && !microphone.IsRecording && !busy) Status(response.message);
                if (response.observation != null && response.observation.hazard != "none")
                { assistant.Open(panel); assistant.SetState("Check your cooking"); AlertTone(); }
                if (state.completed) { monitoring = false; UpdateMonitorLabel(); }
            });
            visionBusy = false; nextFrame = Time.unscaledTime + 8;
        }
        void AlertTone()
        {
            if (speaker.isPlaying || microphone.IsRecording) return;
            var tone = AudioClip.Create("Cooking alert", 8000, 1, 16000, false);
            var samples = new float[8000];
            for (int i = 0; i < samples.Length; i++) samples[i] = Mathf.Sin(i * 2 * Mathf.PI * 660 / 16000) * .12f;
            tone.SetData(samples, 0); speaker.PlayOneShot(tone); Destroy(tone, 1);
        }
        IEnumerator PlayAudio(string url)
        {
            if (!Uri.TryCreate(new Uri(api.BaseUrl + "/"), url, out var uri) || (uri.Scheme != "https" && uri.Scheme != "http")) yield break;
            audioBusy = true;
            var path = uri.AbsolutePath.ToLowerInvariant();
            var type = path.EndsWith(".wav") ? AudioType.WAV : path.EndsWith(".ogg") ? AudioType.OGGVORBIS : AudioType.MPEG;
            using (var request = UnityWebRequestMultimedia.GetAudioClip(uri.ToString(), type))
            {
                request.timeout = 30; yield return request.SendWebRequest();
                if (request.result == UnityWebRequest.Result.Success)
                {
                    if (speaker.clip) Destroy(speaker.clip);
                    speaker.clip = DownloadHandlerAudioClip.GetContent(request); speaker.Play();
                    assistant.SetState("Speaking");
                    while (speaker.isPlaying) yield return null;
                }
                else Status("Reply received, but audio could not play. Read the reply above.");
            }
            audioBusy = false; assistant.SetState("Ready");
        }
        void OnApplicationPause(bool value) { paused = value; if (value) speaker.Stop(); }
        void Fail(string message) { Status(message); assistant.SetState("Try again"); }
        public void Status(string message) { statusText.text = message; }
    }
}
