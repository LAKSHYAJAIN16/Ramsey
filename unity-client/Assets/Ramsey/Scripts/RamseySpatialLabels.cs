using System.Collections.Generic;
using UnityEngine;

namespace Ramsey
{
    public class RamseySpatialLabels : MonoBehaviour
    {
        sealed class Track
        {
            public string label;
            public Vector3 position;
            public float seen;
            public int observations;
            public TextMesh text;
        }
        readonly List<Track> tracks = new List<Track>();
        public Transform viewer;
        public string Status { get; private set; } = "Waiting for equipment";

        public void Observe(EquipmentDetection[] detections, RamseyDepthSnapshot frame)
        {
            if (frame == null || Time.unscaledTime - frame.capturedAt > 15)
            { Status = "Spatial result expired; waiting for a fresh view"; return; }
            if (frame.samples.Count == 0) { Clear(); Status = frame.status; return; }
            var used = new HashSet<Track>();
            int located = 0;
            foreach (var item in detections ?? new EquipmentDetection[0])
            {
                if (located >= 12 || item == null || string.IsNullOrWhiteSpace(item.label) ||
                    !frame.TryLocate(item, out var position)) continue;
                located++;
                Track nearest = null;
                float distance = .25f;
                foreach (var track in tracks)
                {
                    float candidate = Vector3.Distance(track.position, position);
                    if (!used.Contains(track) && track.label == item.label && candidate < distance)
                    { nearest = track; distance = candidate; }
                }
                if (nearest == null)
                {
                    if (tracks.Count >= 24) continue;
                    nearest = new Track { label = item.label, position = position };
                    tracks.Add(nearest);
                }
                used.Add(nearest);
                nearest.position = Vector3.Lerp(nearest.position, position, .6f);
                nearest.seen = Time.unscaledTime;
                nearest.observations++;
                if (nearest.observations < 2) continue;
                if (!nearest.text)
                {
                    var label = new GameObject("Detected equipment: " + item.label);
                    nearest.text = label.AddComponent<TextMesh>();
                    nearest.text.anchor = TextAnchor.LowerCenter;
                    nearest.text.alignment = TextAlignment.Center;
                    nearest.text.characterSize = .009f;
                    nearest.text.fontSize = 64;
                    nearest.text.richText = false;
                    nearest.text.color = new Color(1, .88f, .35f);
                }
                nearest.text.text = item.label.ToUpperInvariant();
                nearest.text.transform.position = nearest.position + Vector3.up * .10f;
                nearest.text.gameObject.SetActive(true);
            }
            // Labels unsupported by this latest view are hidden, not left pretending to track motion.
            foreach (var track in tracks)
                if (!used.Contains(track) && track.text) track.text.gameObject.SetActive(false);
            Status = located == 0 ? "No confidently located equipment" : "Equipment located; labels confirm after two views";
        }

        void Update()
        {
            for (int i = tracks.Count - 1; i >= 0; i--)
            {
                var track = tracks[i];
                if (Time.unscaledTime - track.seen > 30)
                { if (track.text) Destroy(track.text.gameObject); tracks.RemoveAt(i); continue; }
                if (track.text && Time.unscaledTime - track.seen > 15) track.text.gameObject.SetActive(false);
                if (track.text && viewer)
                    track.text.transform.rotation = Quaternion.LookRotation(track.text.transform.position - viewer.position, Vector3.up);
            }
        }
        public void Clear()
        {
            foreach (var track in tracks) if (track.text) Destroy(track.text.gameObject);
            tracks.Clear();
        }
        void OnDisable() { Clear(); }
    }
}
