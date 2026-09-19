using System;
using UnityEditor;
using UnityEngine;

namespace Ramsey.Editor
{
    public static class RamseyVoiceChecks
    {
        [MenuItem("Ramsey/Check Double Tap Detector")]
        public static void Run()
        {
            var d = new DoubleTapDetector();
            void Check(bool pass, string name) { if (!pass) throw new Exception(name); }
            Check(!d.Sample(.3f, .15f, 1), "Single tap must not trigger");
            d.Sample(0, .15f, 1.1f);
            Check(d.Sample(.3f, .15f, 1.3f), "Two taps should trigger");
            d.Sample(0, .15f, 1.4f);
            Check(!d.Sample(.3f, .15f, 1.5f), "Cooldown must suppress triple tap");
            d.Reset(3);
            Check(!d.Sample(.3f, .15f, 4), "First isolated tap");
            Check(!d.Sample(.3f, .15f, 4.3f), "Sustained noise must not double tap");
            d.Sample(0, .15f, 4.4f);
            Check(!d.Sample(.3f, .15f, 5), "Widely spaced taps must not trigger");
            Debug.Log("Ramsey: six double-tap detector checks passed.");
        }
    }
}
