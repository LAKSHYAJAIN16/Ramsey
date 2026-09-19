using System.Collections.Generic;
using Meta.XR;
using UnityEngine;

namespace Ramsey
{
    // Sample measured geometry before upload, never against a later head pose/depth frame.
    public sealed class RamseyDepthSnapshot
    {
        public struct Sample { public Vector2 image; public Vector3 world; }
        public readonly List<Sample> samples = new List<Sample>();
        public float capturedAt;
        public string status;
        public static RamseyDepthSnapshot Capture(PassthroughCameraAccess camera, EnvironmentRaycastManager depth)
        {
            var snapshot = new RamseyDepthSnapshot { capturedAt = Time.unscaledTime, status = "Depth unavailable" };
            if (!depth) return snapshot;
            var pose = camera.GetCameraPose();
            for (int y = 0; y < 13; y++)
            for (int x = 0; x < 17; x++)
            {
                var uv = new Vector2((x + .5f) / 17, (y + .5f) / 13);
                var ray = camera.ViewportPointToRay(uv, pose);
                if (depth.Raycast(ray, out var hit, 4f) && Vector3.Distance(ray.origin, hit.point) >= .2f)
                    snapshot.samples.Add(new Sample { image = new Vector2(uv.x, 1 - uv.y), world = hit.point });
            }
            snapshot.status = snapshot.samples.Count == 0 ? "No measured depth; labels withheld" : "Depth sampled";
            return snapshot;
        }

        public bool TryLocate(EquipmentDetection item, out Vector3 point)
        {
            point = default;
            if (item == null || item.confidence < .8f || item.width <= 0 || item.height <= 0 ||
                item.x < 0 || item.y < 0 || item.x + item.width > 1.00001f || item.y + item.height > 1.00001f) return false;
            var centre = new Vector2(item.x + item.width / 2, item.y + item.height / 2);
            var candidates = new List<Sample>();
            foreach (var sample in samples)
                if (Mathf.Abs(sample.image.x - centre.x) <= item.width * .25f &&
                    Mathf.Abs(sample.image.y - centre.y) <= item.height * .25f) candidates.Add(sample);
            if (candidates.Count < 3) return false;
            candidates.Sort((a,b) => (a.image-centre).sqrMagnitude.CompareTo((b.image-centre).sqrMagnitude));
            // Reject depth discontinuities rather than putting a label on the wall behind an object.
            var first = candidates[0].world;
            for (int i = 0; i < 3; i++)
            {
                if (Vector3.Distance(first, candidates[i].world) > .15f) return false;
                point += candidates[i].world;
            }
            point /= 3;
            return true;
        }
    }
}
