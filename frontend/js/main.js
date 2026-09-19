import * as api from "./api.js";
import * as ui from "./ui.js";
import { getSessionId, getQueryParams, getRecentDishes, pushRecentDish } from "./state.js";
import { VoiceRecorder } from "./voice.js";
import { XRHost, bindKeyboardFallback } from "./xr.js";

const sessionId = getSessionId();
const xrHost = new XRHost();
const localMemory = { allergies: [], dislikes: [] };

async function loadRecipe(dish, demo = false) {
  ui.setSearchStatus(true, demo ? ["Loading offline demo recipe..."] : [
    "Racing: fast fetch + parse",
    "Racing: live browser fallback",
    "First valid recipe wins, the rest get cancelled",
  ]);
  try {
    const recipe = await api.getRecipe(sessionId, dish || "demo", demo);
    if (dish) pushRecentDish(dish);
    ui.setSearchStatus(false);
    ui.showScreen("kitchen");
    const state = await api.getSessionState(sessionId);
    ui.renderKitchenState(state);
    ui.appendChatLine("ramsey", `Right, ${recipe.title}. Let's get moving.`);
  } catch (err) {
    ui.setSearchStatus(false);
    ui.appendChatLine("ramsey", `Couldn't reach the kitchen: ${err.message}. Loading the demo recipe instead.`);
    await loadRecipe(null, true);
  }
}

async function applyAction(action, index = null) {
  const state = await api.sendAction(sessionId, action, index);
  if (!state.error) ui.renderKitchenState(state);
}

function trackMemoryFromToolCalls(toolCalls) {
  let changed = false;
  for (const call of toolCalls || []) {
    if (call.name === "remember_allergy" && call.arguments?.item) {
      if (!localMemory.allergies.includes(call.arguments.item)) {
        localMemory.allergies.push(call.arguments.item);
        changed = true;
      }
    }
    if (call.name === "remember_dislike" && call.arguments?.item) {
      if (!localMemory.dislikes.includes(call.arguments.item)) {
        localMemory.dislikes.push(call.arguments.item);
        changed = true;
      }
    }
  }
  if (changed) ui.renderMemory(localMemory);
}

function setupLauncher() {
  ui.renderRecentDishes(getRecentDishes(), (dish) => loadRecipe(dish));

  document.getElementById("dish-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const dish = document.getElementById("dish-input").value.trim();
    if (dish) loadRecipe(dish);
  });

  document.getElementById("demo-button").addEventListener("click", () => loadRecipe(null, true));

  xrHost.checkSupport().then(({ ar, vr }) => {
    document.getElementById("enter-ar").classList.toggle("hidden", !ar);
    document.getElementById("enter-vr").classList.toggle("hidden", !vr);
  });
  document.getElementById("enter-ar").addEventListener("click", () => xrHost.enterAR());
  document.getElementById("enter-vr").addEventListener("click", () => xrHost.enterVR());
}

function setupKitchenControls() {
  document.getElementById("btn-back").addEventListener("click", () => applyAction("back"));
  document.getElementById("btn-next").addEventListener("click", () => applyAction("next"));
  document.getElementById("btn-timer").addEventListener("click", () => applyAction("start_timer"));
  document.getElementById("btn-exit").addEventListener("click", () => ui.showScreen("launcher"));

  document.getElementById("ingredient-list").addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (li) applyAction("toggle_ingredient", Number(li.dataset.index));
  });

  bindKeyboardFallback({
    onNext: () => applyAction("next"),
    onBack: () => applyAction("back"),
    onTimer: () => applyAction("start_timer"),
  });

  setInterval(() => {
    if (!document.getElementById("kitchen").classList.contains("hidden")) {
      api.getSessionState(sessionId).then((state) => {
        if (!state.error) ui.renderKitchenState(state);
      });
    }
  }, 1000);
}

function setupVoice() {
  const talkButton = document.getElementById("btn-talk");
  const recorder = new VoiceRecorder({
    onResult: (result) => {
      ui.appendChatLine("ramsey", result.reply || "...");
      if (result.state) ui.renderKitchenState(result.state);
      trackMemoryFromToolCalls(result.tool_calls);
    },
    onError: (message) => ui.appendChatLine("ramsey", `(mic issue: ${message})`),
    onSpeakingChange: (speaking) => talkButton.classList.toggle("recording", speaking),
  });

  const start = async (e) => {
    e.preventDefault();
    const ok = await recorder.start();
    if (ok) talkButton.classList.add("recording");
  };
  const stop = (e) => {
    e.preventDefault();
    talkButton.classList.remove("recording");
    recorder.stop((blob) => api.sendVoice(sessionId, blob));
  };

  talkButton.addEventListener("mousedown", start);
  talkButton.addEventListener("touchstart", start);
  talkButton.addEventListener("mouseup", stop);
  talkButton.addEventListener("touchend", stop);
}

function main() {
  setupLauncher();
  setupKitchenControls();
  setupVoice();

  const { dish, demo } = getQueryParams();
  if (dish || demo) loadRecipe(dish, demo);
}

main();
