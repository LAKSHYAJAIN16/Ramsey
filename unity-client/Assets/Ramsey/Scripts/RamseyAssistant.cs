using UnityEngine;

namespace Ramsey
{
    public class RamseyAssistant : MonoBehaviour
    {
        Transform avatar;
        TextMesh caption;
        Material material;
        string mode = "Ready";
        public void Open(Transform panel)
        {
            if (!avatar)
            {
                avatar = GameObject.CreatePrimitive(PrimitiveType.Cube).transform;
                avatar.name = "Ramsey Voice Assistant";
                Destroy(avatar.GetComponent<Collider>());
                var face = avatar.GetComponent<Renderer>();
                var pointer = GetComponent<RamseyPointer>();
                material = new Material(pointer && pointer.pointerMaterial ? pointer.pointerMaterial : face.sharedMaterial); face.sharedMaterial = material;
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
            if (!avatar) return;
            caption.text = "RAMSEY | AI voice\n" + value;
            var color = value == "Listening" ? new Color(.25f,.8f,.4f) : value == "Speaking" ? new Color(.25f,.65f,1) : new Color(1,.65f,.2f);
            material.color = color;
            if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", color);
        }
        void Update() { if (avatar) avatar.localScale = Vector3.one * (.14f + (mode == "Listening" || mode == "Speaking" ? Mathf.Sin(Time.unscaledTime * 5) * .008f : 0)); }
        void OnDestroy() { if (avatar) Destroy(avatar.gameObject); if (material) Destroy(material); }
    }
}
