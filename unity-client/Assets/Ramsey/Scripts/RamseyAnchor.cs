using System;
using System.Collections.Generic;
using UnityEngine;

namespace Ramsey
{
    public class RamseyAnchor : MonoBehaviour
    {
        OVRSpatialAnchor anchor;
        bool working;
        public bool IsPinned => anchor != null;
        const string Key = "ramsey.panelAnchor";
        public async void TogglePin(Transform panel, Action<string> notice)
        {
            if (working) return;
            if (Application.isEditor) { notice("Persistent pinning is available on Quest. Recenter works in the Editor."); return; }
            working = true;
            try
            {
                if (anchor)
                {
                    var erased = await anchor.EraseAnchorAsync();
                    if (!erased.Success) { notice("Could not remove the saved pin. Try again."); return; }
                    panel.SetParent(null, true); Destroy(anchor.gameObject); anchor = null;
                    PlayerPrefs.DeleteKey(Key); PlayerPrefs.Save(); notice("Panel unpinned. You can recenter it now."); return;
                }
                notice("Saving this panel position…");
                var go = new GameObject("Ramsey saved panel anchor"); go.transform.SetPositionAndRotation(panel.position, panel.rotation);
                anchor = go.AddComponent<OVRSpatialAnchor>();
                if (!await anchor.WhenLocalizedAsync()) { Destroy(go); anchor = null; notice("Could not locate this position. Look around your room and try again."); return; }
                var saved = await anchor.SaveAnchorAsync();
                if (!saved.Success) { Destroy(go); anchor = null; notice("Could not save the panel. Check spatial-data permissions and try again."); return; }
                panel.SetParent(go.transform, true); PlayerPrefs.SetString(Key, anchor.Uuid.ToString()); PlayerPrefs.Save(); notice("Panel pinned here. Tap Pin / unpin to release it.");
            }
            catch (Exception exception) { notice("Pinning failed: " + exception.Message); }
            finally { working = false; }
        }
        public async void Restore(Transform panel, Action<string> notice)
        {
            if (Application.isEditor || !Guid.TryParse(PlayerPrefs.GetString(Key, ""), out var uuid)) return;
            working = true;
            try
            {
                var anchors = new List<OVRSpatialAnchor.UnboundAnchor>();
                var loaded = await OVRSpatialAnchor.LoadUnboundAnchorsAsync(new[] { uuid }, anchors);
                if (!loaded.Success || anchors.Count == 0) { notice("Saved position isn't available. Use Recenter or make a new pin."); return; }
                var unbound = anchors[0];
                if (!await unbound.LocalizeAsync(10)) { notice("Look around to recognize your room, or make a new pin."); return; }
                var go = new GameObject("Ramsey restored panel anchor"); anchor = go.AddComponent<OVRSpatialAnchor>(); unbound.BindTo(anchor);
                panel.SetParent(go.transform, false); panel.localPosition = Vector3.zero; panel.localRotation = Quaternion.identity;
                notice("Restored your saved panel position.");
            }
            catch (Exception exception) { notice("Could not restore pin: " + exception.Message); }
            finally { working = false; }
        }
    }
}
