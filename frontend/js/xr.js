import * as THREE from "three";

/**
 * Minimal WebXR plumbing: passthrough AR on the Quest 3S with the DOM
 * overlay (#overlay) floating over the camera feed, a full VR fallback,
 * and a plain laptop fallback that never touches WebXR at all.
 *
 * The 3D scene itself is a placeholder (a soft light + nothing solid) -
 * the floating UI is carried entirely by the dom-overlay feature. A real
 * "Ramsey has a face" model or world-anchored timers (Tier 7) would hang
 * off this same renderer/scene.
 */
export class XRHost {
  constructor() {
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.session = null;
  }

  async checkSupport() {
    if (!("xr" in navigator)) return { ar: false, vr: false };
    const [ar, vr] = await Promise.all([
      navigator.xr.isSessionSupported("immersive-ar").catch(() => false),
      navigator.xr.isSessionSupported("immersive-vr").catch(() => false),
    ]);
    return { ar, vr };
  }

  _ensureRenderer() {
    if (this.renderer) return;
    const canvas = document.getElementById("scene-canvas");
    canvas.classList.remove("hidden");
    this.renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.xr.enabled = true;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.01, 50);
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.2));

    this.renderer.setAnimationLoop(() => this.renderer.render(this.scene, this.camera));
    window.addEventListener("resize", () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  async enterAR() {
    this._ensureRenderer();
    const overlayRoot = document.getElementById("overlay");
    this.session = await navigator.xr.requestSession("immersive-ar", {
      requiredFeatures: ["local-floor"],
      optionalFeatures: ["dom-overlay", "hit-test"],
      domOverlay: { root: overlayRoot },
    });
    await this.renderer.xr.setSession(this.session);
    this.session.addEventListener("end", () => this._onSessionEnd());
  }

  async enterVR() {
    this._ensureRenderer();
    const overlayRoot = document.getElementById("overlay");
    this.session = await navigator.xr.requestSession("immersive-vr", {
      requiredFeatures: ["local-floor"],
      optionalFeatures: ["dom-overlay"],
      domOverlay: { root: overlayRoot },
    });
    await this.renderer.xr.setSession(this.session);
    this.session.addEventListener("end", () => this._onSessionEnd());
  }

  _onSessionEnd() {
    this.session = null;
  }
}

export function bindKeyboardFallback({ onNext, onBack, onTimer }) {
  window.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") onNext();
    if (e.key === "ArrowLeft") onBack();
    if (e.key.toLowerCase() === "t") onTimer();
  });
}
