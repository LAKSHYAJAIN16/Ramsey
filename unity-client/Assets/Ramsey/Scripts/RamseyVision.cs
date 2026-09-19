using System;
using System.Collections;
using Meta.XR;
using UnityEngine;

namespace Ramsey
{
    public class RamseyVision : MonoBehaviour
    {
        PassthroughCameraAccess cameraAccess;
        EnvironmentRaycastManager depth;
        bool ownsDepth;
        public RamseyDepthSnapshot LastDepth { get; private set; }
        const string Permission = "horizonos.permission.HEADSET_CAMERA";
        public IEnumerator Capture(Action<byte[]> completed, Action<string> notice)
        {
            LastDepth = null;
            if (Application.isEditor) { notice("Camera capture needs an installed Quest build. No image was uploaded."); yield break; }
#if UNITY_ANDROID
            if (!UnityEngine.Android.Permission.HasUserAuthorizedPermission(Permission))
            {
                UnityEngine.Android.Permission.RequestUserPermission(Permission);
                notice("Allow camera access inside the headset, then tap Check cooking again."); yield break;
            }
#endif
            if (!PassthroughCameraAccess.IsSupported) { notice("Headset camera access is not supported on this device or OS version."); yield break; }
            if (!cameraAccess)
            {
                var go = new GameObject("Ramsey camera capture"); go.SetActive(false); go.transform.SetParent(transform);
                cameraAccess = go.AddComponent<PassthroughCameraAccess>();
                cameraAccess.CameraPosition = PassthroughCameraAccess.CameraPositionType.Left;
                cameraAccess.RequestedResolution = new Vector2Int(1280, 960); go.SetActive(true);
            }
            cameraAccess.enabled = true; notice("Opening camera…");
            if (!depth && EnvironmentRaycastManager.IsSupported)
            {
                depth = FindAnyObjectByType<EnvironmentRaycastManager>();
                if (!depth) { depth = gameObject.AddComponent<EnvironmentRaycastManager>(); ownsDepth = true; }
            }
            if (depth && ownsDepth) depth.enabled = true;
            float deadline = Time.realtimeSinceStartup + 12;
            while ((!cameraAccess.IsPlaying || !cameraAccess.IsUpdatedThisFrame) && Time.realtimeSinceStartup < deadline) yield return null;
            if (!cameraAccess.IsPlaying || !cameraAccess.IsUpdatedThisFrame) { cameraAccess.enabled = false; notice("No fresh camera frame. Check app permissions and try again."); yield break; }
            yield return new WaitForEndOfFrame();
            var source = cameraAccess.GetTexture();
            if (!source) { cameraAccess.enabled = false; notice("Camera returned no image. Try again."); yield break; }
            LastDepth = RamseyDepthSnapshot.Capture(cameraAccess, depth);
            int width = 768, height = Mathf.RoundToInt(768f * source.height / source.width);
            var target = RenderTexture.GetTemporary(width, height, 0, RenderTextureFormat.ARGB32);
            var previous = RenderTexture.active;
            var readable = new Texture2D(width, height, TextureFormat.RGB24, false);
            byte[] bytes;
            try { Graphics.Blit(source, target); RenderTexture.active = target; readable.ReadPixels(new Rect(0, 0, width, height), 0, 0); readable.Apply(); bytes = readable.EncodeToJPG(75); }
            finally { RenderTexture.active = previous; RenderTexture.ReleaseTemporary(target); Destroy(readable); cameraAccess.enabled = false; }
            completed(bytes);
        }
        public void StopSpatialCapture() { if (ownsDepth && depth) depth.enabled = false; LastDepth = null; }
        void OnDisable() { StopSpatialCapture(); if (cameraAccess) cameraAccess.enabled = false; }
    }
}
