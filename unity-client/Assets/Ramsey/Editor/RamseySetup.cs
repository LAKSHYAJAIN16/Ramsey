using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEditor.XR.OpenXR.Features;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using UnityEngine.XR.Management;
using UnityEngine.XR.OpenXR;

namespace Ramsey.Editor
{
    public static class RamseySetup
    {
        const string ScenePath = "Assets/Ramsey/Scenes/RamseyKitchen.unity";
        static readonly Color Ink = new Color32(60, 60, 60, 255);
        static readonly Color Green = new Color32(88, 204, 2, 255);
        static readonly Color Blue = new Color32(221, 244, 255, 255);
        static Font font;

        [MenuItem("Ramsey/Validate Kitchen Scene")]
        public static void ValidateScene()
        {
            var app = Object.FindFirstObjectByType<RamseyApp>();
            if (!app || !app.rig || !app.panel || !app.next || !app.voice || !app.cameraCheck || !app.connect) throw new System.Exception("Missing Ramsey scene references.");
            if (!Resources.Load<TextAsset>("sandwich")) throw new System.Exception("Missing offline recipe.");
            var recipe = JsonUtility.FromJson<Recipe>(Resources.Load<TextAsset>("sandwich").text);
            if (recipe.steps.Length != 4) throw new System.Exception("Unexpected bundled recipe.");
            Directory.CreateDirectory("Assets/Ramsey/Materials");
            var material = AssetDatabase.LoadAssetAtPath<Material>("Assets/Ramsey/Materials/Pointer.mat");
            if (!material) { material = new Material(Shader.Find("Universal Render Pipeline/Unlit")); material.color = new Color(.11f, .69f, .96f); AssetDatabase.CreateAsset(material, "Assets/Ramsey/Materials/Pointer.mat"); }
            var pointer = app.GetComponent<RamseyPointer>(); pointer.pointerMaterial = material; EditorUtility.SetDirty(pointer);
            var hand = pointer.rightHand;
            if (hand)
            {
                var skeleton = hand.GetComponent<OVRSkeleton>();
                if (skeleton) { var serialized = new SerializedObject(skeleton); var type = serialized.FindProperty("_skeletonType"); if (type != null) { type.intValue = 1; serialized.ApplyModifiedPropertiesWithoutUndo(); } }
            }
            EditorSceneManager.SaveScene(SceneManager.GetActiveScene()); AssetDatabase.SaveAssets();
            Debug.Log("RAMSEY_VALIDATED: offline recipe, scene references, pointer material, hand skeleton");
        }

        [MenuItem("Ramsey/Configure Quest")]
        public static void Configure()
        {
            PlayerSettings.companyName = "Ramsey"; PlayerSettings.productName = "Ramsey";
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, "com.ramsey.kitchen");
            PlayerSettings.bundleVersion = "0.1.0"; PlayerSettings.Android.bundleVersionCode = 1;
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel32;
            PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevelAuto;
            PlayerSettings.Android.forceInternetPermission = true;
            PlayerSettings.insecureHttpOption = InsecureHttpOption.DevelopmentOnly;
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.Vulkan });
            var config = OVRProjectConfig.CachedProjectConfig;
            config.targetDeviceTypes = new System.Collections.Generic.List<OVRProjectConfig.DeviceType> { OVRProjectConfig.DeviceType.Quest3, OVRProjectConfig.DeviceType.Quest3S };
            config.handTrackingSupport = OVRProjectConfig.HandTrackingSupport.ControllersAndHands;
            config.anchorSupport = OVRProjectConfig.AnchorSupport.Enabled;
            config.insightPassthroughSupport = OVRProjectConfig.FeatureSupport.Required;
            config.isPassthroughCameraAccessEnabled = true;
            config.requiresSystemKeyboard = true;
            OVRProjectConfig.CommitProjectConfig(config);

            Directory.CreateDirectory("Assets/XR");
            if (!EditorBuildSettings.TryGetConfigObject<XRGeneralSettingsPerBuildTarget>(XRGeneralSettings.k_SettingsKey, out var perTarget))
            {
                perTarget = ScriptableObject.CreateInstance<XRGeneralSettingsPerBuildTarget>();
                AssetDatabase.CreateAsset(perTarget, "Assets/XR/XRGeneralSettingsPerBuildTarget.asset");
                EditorBuildSettings.AddConfigObject(XRGeneralSettings.k_SettingsKey, perTarget, true);
            }
            if (!perTarget.HasManagerSettingsForBuildTarget(BuildTargetGroup.Android)) perTarget.CreateDefaultManagerSettingsForBuildTarget(BuildTargetGroup.Android);
            var settings = perTarget.SettingsForBuildTarget(BuildTargetGroup.Android);
            settings.InitManagerOnStart = true;
            XRPackageMetadataStore.AssignLoader(settings.Manager, "UnityEngine.XR.OpenXR.OpenXRLoader", BuildTargetGroup.Android);
            OpenXRFeatureSetManager.InitializeFeatureSets();
            foreach (var set in OpenXRFeatureSetManager.FeatureSetsForBuildTarget(BuildTargetGroup.Android))
                if (set.name.Contains("Meta")) set.isEnabled = true;
            OpenXRFeatureSetManager.SetFeaturesFromEnabledFeatureSets(BuildTargetGroup.Android);
            var xr = OpenXRSettings.GetSettingsForBuildTargetGroup(BuildTargetGroup.Android);
            foreach (var feature in xr.GetFeatures<UnityEngine.XR.OpenXR.Features.OpenXRFeature>())
                if (feature.GetType().Name.Contains("OculusTouchControllerProfile") || feature.GetType().Name == "MetaQuestFeature") feature.enabled = true;
            EditorUtility.SetDirty(perTarget); EditorUtility.SetDirty(settings); EditorUtility.SetDirty(settings.Manager); EditorUtility.SetDirty(xr);
            AssetDatabase.SaveAssets();
            // Do not run FixAllAsync: it also installs optional desktop tools.
            PlayerSettings.insecureHttpOption = InsecureHttpOption.DevelopmentOnly;
            AssetDatabase.SaveAssets(); Debug.Log("RAMSEY_CONFIGURED");
        }

        [MenuItem("Ramsey/Create Kitchen Scene")]
        public static void CreateScene()
        {
            Directory.CreateDirectory("Assets/Ramsey/Scenes");
            if (File.Exists(ScenePath)) { EditorSceneManager.OpenScene(ScenePath); Debug.Log("Existing Ramsey scene opened."); return; }
            if (SceneManager.GetActiveScene().isDirty) EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Packages/com.meta.xr.sdk.core/Prefabs/OVRCameraRig.prefab");
            var rigObject = (GameObject)PrefabUtility.InstantiatePrefab(prefab); rigObject.name = "Ramsey XR Rig";
            var rig = rigObject.GetComponent<OVRCameraRig>();
            var manager = rigObject.GetComponent<OVRManager>(); manager.isInsightPassthroughEnabled = true; manager.trackingOriginType = OVRManager.TrackingOrigin.Stage;
            var eye = rig.centerEyeAnchor.GetComponent<Camera>(); eye.tag = "MainCamera"; eye.clearFlags = CameraClearFlags.SolidColor; eye.backgroundColor = Color.clear; eye.nearClipPlane = .05f;
            var layer = new GameObject("Kitchen passthrough").AddComponent<OVRPassthroughLayer>(); layer.overlayType = OVROverlay.OverlayType.Underlay;
            RenderSettings.skybox = null;
            var light = new GameObject("Directional Light").AddComponent<Light>(); light.type = LightType.Directional; light.intensity = .7f;
            var handPrefab = AssetDatabase.LoadAssetAtPath<GameObject>("Packages/com.meta.xr.sdk.core/Prefabs/OVRHandPrefab.prefab");
            var handObject = (GameObject)PrefabUtility.InstantiatePrefab(handPrefab);
            handObject.name = "Right hand pointer"; handObject.transform.SetParent(rig.rightHandAnchor, false);
            var hand = handObject.GetComponent<OVRHand>();
            var handSerialized = new SerializedObject(hand); var handType = handSerialized.FindProperty("HandType"); if (handType != null) { handType.enumValueIndex = 1; handSerialized.ApplyModifiedPropertiesWithoutUndo(); }
            var appObject = new GameObject("Ramsey");
            appObject.AddComponent<RamseyApi>(); appObject.AddComponent<RamseyVoice>(); appObject.AddComponent<RamseyVision>(); appObject.AddComponent<RamseyAnchor>(); appObject.AddComponent<AudioSource>();
            var app = appObject.AddComponent<RamseyApp>(); app.rig = rig;
            var pointer = appObject.AddComponent<RamseyPointer>(); pointer.rig = rig; pointer.rightHand = hand;
            font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var canvasObject = new GameObject("Recipe panel", typeof(RectTransform), typeof(Canvas));
            var canvas = canvasObject.GetComponent<Canvas>(); canvas.renderMode = RenderMode.WorldSpace; canvas.worldCamera = eye;
            var panel = canvasObject.GetComponent<RectTransform>(); panel.sizeDelta = new Vector2(1000, 850); panel.localScale = Vector3.one * .001f; panel.position = new Vector3(0, 1.4f, 1.3f); app.panel = panel;
            var background = canvasObject.AddComponent<Image>(); background.color = Color.white;
            Label(panel, "Ramsey", 40, 22, 650, 55, 46, Ink, FontStyle.Bold);
            Label(panel, "Your kitchen companion", 40, 79, 700, 35, 24, Ink);
            app.titleText = Label(panel, "Garden sandwich", 40, 138, 920, 52, 38, Ink, FontStyle.Bold);
            app.progressText = Label(panel, "Step 1 of 4", 40, 197, 600, 38, 27, Ink);
            var rule = new GameObject("Progress accent", typeof(RectTransform), typeof(Image)); rule.transform.SetParent(panel, false); Rect(rule.GetComponent<RectTransform>(), 40, 245, 920, 5); rule.GetComponent<Image>().color = Green;
            app.stepText = Label(panel, "Set out your bread, cheese, lettuce, sliced tomato and spread on a clean board.", 40, 270, 920, 165, 36, Ink);
            app.stepText.resizeTextForBestFit = true; app.stepText.resizeTextMinSize = 24; app.stepText.resizeTextMaxSize = 36;
            app.back = Button(panel, "Back", 40, 458, 200, 64, new Color32(239, 239, 239, 255), out _);
            app.timer = Button(panel, "5-min timer", 258, 458, 250, 64, new Color32(239, 239, 239, 255), out _);
            app.next = Button(panel, "Next step", 526, 458, 434, 64, Green, out app.nextText);
            app.ingredients = Button(panel, "Ingredients", 40, 542, 285, 64, Blue, out _);
            app.voice = Button(panel, "Talk to Ramsey", 343, 542, 307, 64, Blue, out app.voiceText);
            app.cameraCheck = Button(panel, "Check cooking", 668, 542, 292, 64, Blue, out _);
            app.statusText = Label(panel, "Offline recipe • no connection needed", 40, 626, 920, 92, 24, Ink);
            app.statusText.resizeTextForBestFit = true; app.statusText.resizeTextMinSize = 18; app.statusText.resizeTextMaxSize = 24;
            app.connect = Button(panel, "Connect", 40, 745, 215, 57, new Color32(239, 239, 239, 255), out _);
            app.recenter = Button(panel, "Recenter", 273, 745, 215, 57, new Color32(239, 239, 239, 255), out _);
            app.pin = Button(panel, "Pin / unpin", 506, 745, 230, 57, new Color32(239, 239, 239, 255), out _);
            app.timerText = Label(panel, "", 750, 752, 210, 40, 23, Ink);
            var mobilePipeline = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>("Assets/Settings/Mobile_RPAsset.asset");
            if (mobilePipeline) { QualitySettings.renderPipeline = mobilePipeline; GraphicsSettings.defaultRenderPipeline = mobilePipeline; }
            EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets(); Selection.activeGameObject = canvasObject; Debug.Log("RAMSEY_SCENE_CREATED");
        }
        static void Rect(RectTransform rect, float x, float y, float w, float h) { rect.anchorMin = rect.anchorMax = new Vector2(0, 1); rect.pivot = new Vector2(0, 1); rect.anchoredPosition = new Vector2(x, -y); rect.sizeDelta = new Vector2(w, h); }
        static Text Label(Transform parent, string text, float x, float y, float w, float h, int size, Color color, FontStyle style = FontStyle.Normal)
        {
            var go = new GameObject(text.Length > 24 ? text.Substring(0, 24) : text, typeof(RectTransform), typeof(Text)); go.transform.SetParent(parent, false);
            Rect(go.GetComponent<RectTransform>(), x, y, w, h); var label = go.GetComponent<Text>(); label.font = font; label.text = text; label.fontSize = size; label.color = color; label.fontStyle = style; label.supportRichText = false; label.raycastTarget = false; return label;
        }
        static RamseyButton Button(Transform parent, string text, float x, float y, float w, float h, Color color, out Text label)
        {
            var go = new GameObject(text, typeof(RectTransform), typeof(Image), typeof(BoxCollider), typeof(RamseyButton)); go.transform.SetParent(parent, false);
            Rect(go.GetComponent<RectTransform>(), x, y, w, h); go.GetComponent<Image>().color = color;
            var collider = go.GetComponent<BoxCollider>(); collider.size = new Vector3(w, h, 10); collider.center = new Vector3(w / 2, -h / 2, 0);
            label = Label(go.transform, text, 8, 0, w - 16, h, 25, Ink, FontStyle.Bold); label.alignment = TextAnchor.MiddleCenter;
            return go.GetComponent<RamseyButton>();
        }
    }
}
