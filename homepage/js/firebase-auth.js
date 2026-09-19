import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyABm1kKxntgEEvnIdeZU6JwwQrcP-S7XHU",
  authDomain: "ramsey-b9d3e.firebaseapp.com",
  projectId: "ramsey-b9d3e",
  storageBucket: "ramsey-b9d3e.firebasestorage.app",
  messagingSenderId: "536788896938",
  appId: "1:536788896938:web:4e52fff6e0f365db8114d3",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export async function signInWithGoogle() {
  const provider = new GoogleAuthProvider();
  const result = await signInWithPopup(auth, provider);
  const idToken = await result.user.getIdToken();
  const response = await fetch("/api/auth/firebase", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idToken }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Sign-in failed.");
  }
  return response.json();
}
