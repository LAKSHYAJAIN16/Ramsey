using UnityEngine;
using UnityEngine.InputSystem;

namespace Ramsey
{
    public class RamseyPointer : MonoBehaviour
    {
        public OVRCameraRig rig;
        public OVRHand rightHand;
        public Material pointerMaterial;
        LineRenderer line;
        RamseyButton hovered;
        bool wasPinching;
        Material material;
        void Start()
        {
            line = gameObject.AddComponent<LineRenderer>(); line.positionCount = 2;
            line.startWidth = .002f; line.endWidth = .001f;
            material = pointerMaterial ? new Material(pointerMaterial) : new Material(Shader.Find("UI/Default"));
            material.color = new Color(.11f, .69f, .96f); line.sharedMaterial = material;
        }
        void Update()
        {
            if (!rig || !rig.centerEyeAnchor) return;
            var origin = rig.centerEyeAnchor;
            bool pressed = false;
            bool pinching = !Application.isEditor && rightHand && rightHand.IsTracked && rightHand.GetFingerIsPinching(OVRHand.HandFinger.Index);
            if (!Application.isEditor && rightHand && rightHand.IsTracked && rightHand.IsPointerPoseValid)
            {
                origin = rightHand.PointerPose; pressed = pinching && !wasPinching;
            }
            else if (!Application.isEditor && OVRInput.IsControllerConnected(OVRInput.Controller.RTouch))
            {
                origin = rig.rightControllerAnchor;
                pressed = OVRInput.GetDown(OVRInput.Button.PrimaryIndexTrigger, OVRInput.Controller.RTouch);
            }
            wasPinching = pinching;
            var ray = new Ray(origin.position, origin.forward);
            if (Application.isEditor && Mouse.current != null && Camera.main)
            {
                ray = Camera.main.ScreenPointToRay(Mouse.current.position.ReadValue());
                pressed = Mouse.current.leftButton.wasPressedThisFrame;
            }
            var end = ray.GetPoint(2f);
            RamseyButton hitButton = null;
            if (Physics.Raycast(ray, out var hit, 4f)) { end = hit.point; hitButton = hit.collider.GetComponent<RamseyButton>(); }
            if (hovered != hitButton) { if (hovered) hovered.Hover(false); hovered = hitButton; if (hovered) hovered.Hover(true); }
            if (pressed && hovered) hovered.Press();
            line.enabled = !Application.isEditor;
            line.SetPosition(0, ray.origin); line.SetPosition(1, end);
        }
        void OnDestroy() { if (material) Destroy(material); }
    }
}
