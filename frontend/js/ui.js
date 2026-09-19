export function showScreen(name) {
  document.getElementById("launcher").classList.toggle("hidden", name !== "launcher");
  document.getElementById("kitchen").classList.toggle("hidden", name !== "kitchen");
}

export function setCookingMode(mode) {
  ["campaign", "freestyle", "masterchef", "tutorial"].forEach((name) => {
    const active = mode === name;
    document.getElementById(`${name}-mode`).classList.toggle("hidden", !active);
    document.getElementById(`mode-${name}`).classList.toggle("active", active);
    document.getElementById(`mode-${name}`).setAttribute("aria-selected", String(active));
  });
}

export function renderTutorials(tutorials, selectedId, onPick) {
  const root = document.getElementById("tutorial-list");
  root.innerHTML = "";
  tutorials.forEach((tutorial) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `tutorial-card${tutorial.id === selectedId ? " selected" : ""}`;
    button.setAttribute("aria-pressed", String(tutorial.id === selectedId));
    button.innerHTML = `<span aria-hidden="true">${tutorial.icon}</span><span><strong>${tutorial.title}</strong><small>${tutorial.time}</small></span>`;
    button.addEventListener("click", () => onPick(tutorial));
    root.appendChild(button);
  });
}

export function renderTutorialDetail(tutorial) {
  const root = document.getElementById("tutorial-detail");
  root.innerHTML = `<div class="tutorial-detail-head"><span aria-hidden="true">${tutorial.icon}</span><div><p class="eyebrow">${tutorial.time} KITCHEN DRILL</p><h3>${tutorial.title}</h3></div></div><p class="tutorial-goal">${tutorial.goal}</p><ol>${tutorial.steps.map((step) => `<li>${step}</li>`).join("")}</ol><aside><strong>Safety cue</strong><p>${tutorial.safety}</p></aside><div class="tutorial-drill"><span>Practice now</span><strong>${tutorial.drill}</strong></div>`;
}

export function renderMasterChefChallenges(challenges, onPick) {
  const root = document.getElementById("masterchef-challenges");
  root.innerHTML = "";
  challenges.forEach((challenge, index) => {
    const button = document.createElement("button");
    button.className = "challenge-card";
    button.type = "button";
    button.innerHTML = `<span class="challenge-number">${String(index + 1).padStart(2, "0")}</span><span class="challenge-emoji" aria-hidden="true">${challenge.emoji}</span><span class="challenge-main"><strong>${challenge.dish}</strong><small>${challenge.skill}</small></span><span class="challenge-time">${challenge.time}</span>`;
    button.addEventListener("click", () => onPick(challenge));
    root.appendChild(button);
  });
}

export function renderRecentDishes(dishes, onPick) {
  const row = document.getElementById("recent-dishes");
  row.innerHTML = "";
  dishes.forEach((dish) => {
    const btn = document.createElement("button");
    btn.textContent = dish;
    btn.addEventListener("click", () => onPick(dish));
    row.appendChild(btn);
  });
}

export function renderProgress(progress) {
  document.getElementById("streak-count").textContent = progress.streak;
  document.getElementById("calorie-count").textContent = progress.calories.toLocaleString();
  document.getElementById("meal-count").textContent = `${progress.meals} meal${progress.meals === 1 ? "" : "s"} cooked`;
  document.getElementById("level-number").textContent = Math.floor(progress.xp / 100) + 1;
  document.getElementById("xp-fill").style.width = `${progress.xp % 100}%`;
  document.getElementById("daily-menu-note").textContent = progress.meals
    ? `${progress.meals} dish${progress.meals === 1 ? "" : "es"} cooked today. Keep building your skills.`
    : "Pick a dish and learn it step by step.";
}

export function renderDailyMenu(menus, onPick) {
  const root = document.getElementById("daily-menu");
  root.innerHTML = "";
  menus.forEach((menu) => {
    const button = document.createElement("button");
    button.className = "menu-card";
    button.type = "button";
    button.innerHTML = `<span class="menu-emoji" aria-hidden="true">${menu.emoji}</span><span class="menu-main"><strong>${menu.dish}</strong><small>${menu.detail}</small></span><span class="menu-meta"><b>${menu.calories}</b><small>kcal</small><em>${menu.tag}</em></span>`;
    button.addEventListener("click", () => onPick(menu));
    root.appendChild(button);
  });
}

export function renderChefPacks(packs, selectedId, onPick) {
  const root = document.getElementById("chef-pack-list");
  root.innerHTML = "";
  packs.forEach((pack) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `chef-pack ${pack.accent}${pack.id === selectedId ? " selected" : ""}`;
    button.setAttribute("aria-pressed", String(pack.id === selectedId));
    button.innerHTML = `<span class="chef-mark">${pack.mark}</span><span><strong>${pack.name}</strong><small>${pack.focus}</small></span><i>${pack.id === selectedId ? "Active" : "Choose"}</i>`;
    button.addEventListener("click", () => onPick(pack));
    root.appendChild(button);
  });
}

export function setMealToLog(dish, calories) {
  document.getElementById("meal-calorie-label").textContent = `${dish} · about ${calories} kcal`;
  document.getElementById("btn-log-meal").disabled = false;
}

export function renderKitchenState(state) {
  document.getElementById("step-progress").textContent = `Step ${state.step_index + 1} / ${state.total_steps}`;
  document.getElementById("step-text").textContent = state.current_step;

  const list = document.getElementById("ingredient-list");
  list.innerHTML = "";
  state.ingredients.forEach((ingredient, i) => {
    const li = document.createElement("li");
    li.textContent = ingredient;
    if (state.checked_ingredients.includes(i)) li.classList.add("checked");
    li.dataset.index = String(i);
    list.appendChild(li);
  });

  const note = document.getElementById("servings-note");
  note.textContent = state.servings_multiplier !== 1 ? `(x${state.servings_multiplier} servings)` : "";

  const timersPanel = document.getElementById("timers-panel");
  timersPanel.innerHTML = "";
  state.timers.forEach((timer) => {
    const chip = document.createElement("div");
    chip.className = "timer-chip";
    chip.textContent = `${timer.label}: ${formatSeconds(timer.remaining_seconds)}`;
    timersPanel.appendChild(chip);
  });
}

export function formatSeconds(total) {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function appendChatLine(who, text) {
  const log = document.getElementById("chat-log");
  const p = document.createElement("p");
  p.className = who === "you" ? "you" : "ramsey";
  p.textContent = `${who === "you" ? "You" : "Ramsey"}: ${text}`;
  log.appendChild(p);
  log.scrollTop = log.scrollHeight;
}

export function renderMemory(memory) {
  const panel = document.getElementById("memory-panel");
  const content = document.getElementById("memory-content");
  if (!memory || (!memory.allergies?.length && !memory.dislikes?.length)) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");
  content.innerHTML = "";
  if (memory.allergies?.length) {
    const p = document.createElement("p");
    p.textContent = `Allergic to: ${memory.allergies.join(", ")}`;
    content.appendChild(p);
  }
  if (memory.dislikes?.length) {
    const p = document.createElement("p");
    p.textContent = `Dislikes: ${memory.dislikes.join(", ")}`;
    content.appendChild(p);
  }
}

export function setSearchStatus(visible, sources = []) {
  const el = document.getElementById("search-status");
  el.classList.toggle("hidden", !visible);
  const list = document.getElementById("source-list");
  list.innerHTML = "";
  sources.forEach((s) => {
    const div = document.createElement("div");
    div.textContent = s;
    list.appendChild(div);
  });
}
