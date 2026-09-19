using System;
using UnityEngine;
using UnityEngine.UI;

namespace Ramsey
{
    public class RamseyButton : MonoBehaviour
    {
        public Action Clicked;
        public bool Available = true;
        Image image;
        Color original;
        void Awake() { image = GetComponent<Image>(); original = image.color; }
        public void Hover(bool on) { if (image) image.color = on ? Color.Lerp(original, Color.black, .14f) : original; }
        public void Press() { if (Available && isActiveAndEnabled) Clicked?.Invoke(); }
    }
}
