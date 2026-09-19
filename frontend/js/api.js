const API_BASE = "";

export async function getRecipe(sessionId, dish, demo = false) {
  const params = new URLSearchParams({ session_id: sessionId, dish, demo: demo ? "1" : "0" });
  const res = await fetch(`${API_BASE}/api/recipe?${params}`);
  if (!res.ok) throw new Error(`recipe fetch failed: ${res.status}`);
  return res.json();
}

export async function getSessionState(sessionId) {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}`);
  return res.json();
}

export async function sendAction(sessionId, action, index = null) {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, index }),
  });
  return res.json();
}

export async function sendChat(sessionId, text) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, text }),
  });
  return res.json();
}

export async function sendVoice(sessionId, audioBlob) {
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("audio", audioBlob, "utterance.webm");
  const res = await fetch(`${API_BASE}/api/chat/voice`, { method: "POST", body: form });
  return res.json();
}
