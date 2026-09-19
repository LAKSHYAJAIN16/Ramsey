using UnityEngine;

namespace Ramsey
{
    public class RamseyAssistant : MonoBehaviour
    {
        Transform avatar;
        TextMesh caption;
        Material material;
        string mode = "Ready";
        float dismissAt;
        public bool IsVisible => avatar && avatar.gameObject.activeSelf;
        public void Dismiss() { if (avatar) avatar.gameObject.SetActive(false); }
        public void Open(Transform panel)
        {
            if (!avatar)
            {
                avatar = GameObject.CreatePrimitive(PrimitiveType.Cube).transform;
                avatar.name = "Ramsey Voice Assistant";
                Destroy(avatar.GetComponent<Collider>());
                var face = avatar.GetComponent<Renderer>();
                var shader = Resources.Load<Shader>("Art/PixelPortrait");
                material = new Material(shader ? shader : face.sharedMaterial.shader);
                var portrait = Resources.Load<Texture2D>("Art/ramsey-pixel");
                if (portrait) { portrait.filterMode = FilterMode.Point; portrait.wrapMode = TextureWrapMode.Clamp; }
                material.mainTexture = portrait; face.sharedMaterial = material;
                var label = new GameObject("Assistant captions"); label.transform.SetParent(avatar, false);
                label.transform.localPosition = new Vector3(0, -.9f, -.55f);
                caption = label.AddComponent<TextMesh>(); caption.anchor = TextAnchor.UpperCenter;
                caption.alignment = TextAlignment.Center; caption.characterSize = .09f; caption.fontSize = 48;
                caption.color = Color.white;
            }
            avatar.position = panel.position + panel.right * .67f + panel.up * .2f;
            avatar.rotation = panel.rotation;
            avatar.gameObject.SetActive(true); SetState("Listening");
        }
        public void SetState(string value)
        {
            mode = value;
            dismissAt = Time.unscaledTime + 20;
            if (!avatar) return;
            caption.text = "RAMSEY | AI voice\n" + value;
            var color = value == "Listening" ? new Color(.25f,.8f,.4f) : value == "Speaking" ? new Color(.25f,.65f,1) : new Color(1,.65f,.2f);
            caption.color = color;
        }
        void Update()
        {
            if (!IsVisible) return;
            avatar.localScale = Vector3.one * (.22f + (mode == "Listening" || mode == "Speaking" ? Mathf.Sin(Time.unscaledTime * 5) * .006f : 0));
            if (mode != "Listening" && mode != "Speaking" && mode != "Thinking" && Time.unscaledTime > dismissAt) Dismiss();
        }
        void OnDestroy() { if (avatar) Destroy(avatar.gameObject); if (material) Destroy(material); }
    }
}
