import * as api from "./api.js";
import * as ui from "./ui.js";
import { CHEF_PACKS, DAILY_MENUS, MASTERCHEF_CHALLENGES, TUTORIALS, getProgress, getQueryParams, getRecentDishes, getSessionId, logHealthyMeal, pushRecentDish, selectChefPack } from "./state.js";
import { VoiceRecorder } from "./voice.js";
import { XRHost, bindKeyboardFallback } from "./xr.js";

const sessionId = getSessionId();
const xrHost = new XRHost();
const localMemory = { allergies: [], dislikes: [] };
let mealToLog = null;
let selectedTutorial = TUTORIALS[0];

async function loadRecipe(dish, demo = false, dailyMenu = null) {
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
    mealToLog = dailyMenu || { dish: recipe.title, calories: 450 };
    ui.setMealToLog(mealToLog.dish, mealToLog.calories);
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
  ui.renderProgress(getProgress());
  api.getMe().then(ui.renderAccount).catch(() => ui.renderAccount({ authenticated: false, oauth_ready: false }));
  document.getElementById("auth-button").addEventListener("click", () => { window.location.href = "/api/auth/google/login"; });
  ui.renderDailyMenu(DAILY_MENUS, (menu) => loadRecipe(menu.dish, false, menu));
  document.getElementById("campaign-fridge-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    e.target.value = "";
    if (!file) return;
    const status = document.getElementById("campaign-plan-status");
    status.classList.remove("hidden");
    status.textContent = "Reading your fridge and building a lesson path...";
    try {
      const result = await api.analyzeFridgePhoto(file);
      const plan = result.suggestions.map((dish, index) => ({
        dish, calories: 350 + index * 60, emoji: ["🥕", "🍳", "🍲"][index] || "🍽️",
        tag: `Lesson ${index + 1}`, detail: `${index === 0 ? "Start here" : "Unlock after the lesson before"} · from your fridge`,
      }));
      if (!plan.length) throw new Error("No dishes found");
      ui.renderDailyMenu(plan, (menu) => loadRecipe(menu.dish, false, menu));
      status.textContent = `Your path is ready: ${result.ingredients.slice(0, 5).join(", ")}. Start Lesson 1.`;
    } catch (err) {
      status.textContent = "I couldn't build a plan from that image. Try a brighter, closer fridge photo.";
    }
  });
  ui.renderMasterChefChallenges(MASTERCHEF_CHALLENGES, (challenge) => loadRecipe(challenge.dish));
  const showTutorial = (tutorial) => {
    selectedTutorial = tutorial;
    ui.renderTutorials(TUTORIALS, selectedTutorial.id, showTutorial);
    ui.renderTutorialDetail(selectedTutorial);
  };
  showTutorial(selectedTutorial);
  const renderPacks = () => ui.renderChefPacks(CHEF_PACKS, getProgress().chefPack, (pack) => {
    selectChefPack(pack.id);
    renderPacks();
  });
  renderPacks();
  document.getElementById("mode-campaign").addEventListener("click", () => ui.setCookingMode("campaign"));
  document.getElementById("mode-freestyle").addEventListener("click", () => ui.setCookingMode("freestyle"));
  document.getElementById("mode-masterchef").addEventListener("click", () => ui.setCookingMode("masterchef"));

  document.getElementById("dish-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const dish = document.getElementById("dish-input").value.trim();
    if (dish) loadRecipe(dish);
  });

  document.getElementById("demo-button").addEventListener("click", () => loadRecipe(null, true));

  document.getElementById("fridge-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    e.target.value = ""; // allow picking the same file again later
    if (!file) return;

    const status = document.getElementById("fridge-status");
    const suggestions = document.getElementById("fridge-suggestions");
    suggestions.innerHTML = "";
    status.classList.remove("hidden");
    status.textContent = "Looking at your fridge...";

    try {
      const result = await api.analyzeFridgePhoto(file);
      status.classList.add("hidden");
      if (!result.suggestions.length) {
        status.classList.remove("hidden");
        status.textContent = "Couldn't make out enough to suggest anything - try a closer photo.";
        return;
      }
      result.suggestions.forEach((dish) => {
        const btn = document.createElement("button");
        btn.textContent = dish;
        btn.addEventListener("click", () => loadRecipe(dish));
        suggestions.appendChild(btn);
      });
    } catch (err) {
      status.textContent = `Couldn't read that photo: ${err.message}`;
    }
  });

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
  document.getElementById("btn-log-meal").addEventListener("click", () => {
    if (!mealToLog) return;
    const result = logHealthyMeal(mealToLog.dish, mealToLog.calories);
    ui.renderProgress(result.progress);
    if (result.duplicate) {
      ui.appendChatLine("ramsey", "That dish is already in today's log. Consistency beats double-counting.");
    } else {
      ui.appendChatLine("ramsey", `Lesson complete: ${mealToLog.calories} kcal and 20 XP. That's day ${result.progress.streak} of your streak.`);
      document.getElementById("btn-log-meal").disabled = true;
      api.saveCompletedMeal(mealToLog.calories).then((profile) => ui.renderAccount({ authenticated: true, profile })).catch(() => {});
    }
  });
  document.getElementById("btn-close-safety").addEventListener("click", () => document.getElementById("safety-dialog").close());

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

  const { dish, demo, mode } = getQueryParams();
  if (["campaign", "freestyle", "masterchef"].includes(mode)) ui.setCookingMode(mode);
  if (dish || demo) loadRecipe(dish, demo);
}

main();
