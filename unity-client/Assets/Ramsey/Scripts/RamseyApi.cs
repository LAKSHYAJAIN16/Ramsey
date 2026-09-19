using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace Ramsey
{
    public class RamseyApi : MonoBehaviour
    {
        public string BaseUrl { get; private set; }
        public string SessionId { get; private set; }
        public bool Connected { get; set; }
        string token;
        public void Join(string sessionId, string accessToken)
        {
            token = accessToken;
            SessionId = sessionId; Connected = true;
            PlayerPrefs.SetString("ramsey.session", SessionId); PlayerPrefs.Save();
        }
        public event Action<string> Failed;

        void Awake()
        {
            var config = Resources.Load<TextAsset>("ramsey-config");
            var fallback = config ? JsonUtility.FromJson<ClientConfig>(config.text).backendUrl : "";
            BaseUrl = PlayerPrefs.GetString("ramsey.backend", fallback).TrimEnd('/');
            SessionId = PlayerPrefs.GetString("ramsey.session", "");
            if (string.IsNullOrEmpty(SessionId)) { SessionId = Guid.NewGuid().ToString("N"); PlayerPrefs.SetString("ramsey.session", SessionId); PlayerPrefs.Save(); }
        }

        public bool SetEndpoint(string value)
        {
            if (!Uri.TryCreate(value.Trim(), UriKind.Absolute, out var uri) || (uri.Scheme != "https" && uri.Scheme != "http")) return false;
            if (uri.Scheme == "http" && !Application.isEditor && !Debug.isDebugBuild) return false;
            BaseUrl = value.Trim().TrimEnd('/'); Connected = false; token = null;
            PlayerPrefs.SetString("ramsey.backend", BaseUrl); PlayerPrefs.Save(); return true;
        }

        public IEnumerator Get(string path, Action<string> done)
        {
            using (var request = UnityWebRequest.Get(BaseUrl + path)) yield return Send(request, done);
        }

        public IEnumerator Post(string path, string json, Action<string> done)
        {
            using (var request = new UnityWebRequest(BaseUrl + path, "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                yield return Send(request, done);
            }
        }

        public IEnumerator Upload(string path, string field, byte[] bytes, string filename, string mime, Action<string> done)
        {
            var form = new WWWForm(); form.AddField("session_id", SessionId); form.AddBinaryData(field, bytes, filename, mime);
            using (var request = UnityWebRequest.Post(BaseUrl + path, form)) yield return Send(request, done);
        }

        IEnumerator Send(UnityWebRequest request, Action<string> done)
        {
            if (!string.IsNullOrEmpty(token)) request.SetRequestHeader("Authorization", "Bearer " + token);
            request.timeout = 60;
            yield return request.SendWebRequest();
            if (request.result != UnityWebRequest.Result.Success)
            {
                if (request.result == UnityWebRequest.Result.ConnectionError) Connected = false;
                Failed?.Invoke($"Request failed ({request.responseCode}): {request.error}. Check your connection and try again."); yield break;
            }
            var body = request.downloadHandler.text;
            if (body.Contains("\"error\":")) { Failed?.Invoke("The server could not complete this action. Reconnect and try again."); yield break; }
            done?.Invoke(body);
        }
    }
}
