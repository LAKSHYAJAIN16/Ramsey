using System;
using UnityEditor;
using UnityEngine;

namespace Ramsey.Editor
{
    public static class RamseySpatialChecks
    {
        [MenuItem("Ramsey/Validate Spatial Geometry")]
        public static void MenuRun() { Debug.Log(Run()); }
        public static string Run()
        {
            var item = new EquipmentDetection { label = "bowl", confidence = .95f, x = .2f, y = .2f, width = .6f, height = .6f };
            var frame = new RamseyDepthSnapshot();
            Require(!frame.TryLocate(item, out _), "No depth must not invent a position");
            frame.samples.Add(new RamseyDepthSnapshot.Sample { image = new Vector2(.5f,.5f), world = new Vector3(1,1,2) });
            frame.samples.Add(new RamseyDepthSnapshot.Sample { image = new Vector2(.52f,.5f), world = new Vector3(1.02f,1,2) });
            Require(!frame.TryLocate(item, out _), "Two samples must remain unlocalized");
            frame.samples.Add(new RamseyDepthSnapshot.Sample { image = new Vector2(.5f,.52f), world = new Vector3(1,1.02f,2) });
            Require(frame.TryLocate(item, out var point) && Vector3.Distance(point,new Vector3(1,1,2)) < .02f, "Measured surface should locate");
            frame.samples[2] = new RamseyDepthSnapshot.Sample { image = new Vector2(.5f,.52f), world = new Vector3(1,1,3) };
            Require(!frame.TryLocate(item, out _), "Depth edge must reject background");
            item.x = .9f;
            Require(!frame.TryLocate(item, out _), "Out-of-bounds image box must reject");
            var texture = Resources.Load<Texture2D>("Art/ramsey-pixel");
            Require(texture && texture.filterMode == FilterMode.Point, "Pixel portrait must import with point filtering");
            var shader = Resources.Load<Shader>("Art/PixelPortrait");
            Require(shader && !ShaderUtil.ShaderHasError(shader), "Portrait shader must compile");
            return "7 spatial/portrait checks passed. Camera/depth hardware and live CV still require Quest validation.";
        }
        static void Require(bool condition, string message) { if (!condition) throw new Exception(message); }
    }
}
