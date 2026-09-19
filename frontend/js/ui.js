import { renderPixelAvatarSVG } from "./pixel-avatars.js";

export function showScreen(name) {
  document.getElementById("launcher").classList.toggle("hidden", name !== "launcher");
  document.getElementById("kitchen").classList.toggle("hidden", name !== "kitchen");
}

export function setCookingMode(mode) {
  ["campaign", "freestyle", "masterchef"].forEach((name) => {
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
  root.innerHTML = `<div class="tutorial-detail-head"><span class="tutorial-icon-badge" aria-hidden="true">${tutorial.icon}</span><div class="tutorial-detail-head-copy"><h3>${tutorial.title}</h3><span class="time-chip">${tutorial.time} drill</span></div></div><p class="tutorial-goal">${tutorial.goal}</p><ol>${tutorial.steps.map((step) => `<li>${step}</li>`).join("")}</ol><aside><strong>Safety cue</strong><p>${tutorial.safety}</p></aside><div class="tutorial-drill"><span>Practice now</span><strong>${tutorial.drill}</strong></div>`;
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
  document.getElementById("xp-fill").style.transform = `scaleX(${(progress.xp % 100) / 100})`;
  document.getElementById("campaign-streak").textContent = progress.streak;
  document.getElementById("campaign-xp").textContent = progress.xp;
  document.getElementById("daily-menu-note").textContent = progress.meals
    ? `${progress.meals} dish${progress.meals === 1 ? "" : "es"} cooked today. Keep building your skills.`
    : "Pick a dish and learn it step by step.";
}

export function renderAccount(account) {
  const label = document.getElementById("rank-label");
  const button = document.getElementById("auth-button");
  if (account.authenticated) {
    label.textContent = `${account.profile.display_name} · ${account.profile.rank}`;
    button.textContent = "Profile saved";
    button.disabled = true;
  } else {
    label.textContent = "Guest · Prep Cook";
    button.textContent = account.oauth_ready ? "Sign in to save" : "Google sign-in unavailable";
    button.disabled = !account.oauth_ready;
  }
}

export function renderDailyMenu(menus, onPick) {
  const root = document.getElementById("daily-menu");
  root.innerHTML = "";
  menus.forEach((menu, index) => {
    const status = menu.status || "current";
    const nodeIcon = status === "complete" ? "★" : status === "locked" ? "🔒" : menu.emoji;

    const item = document.createElement("div");
    item.className = `trail-item trail-item-${index % 2 === 0 ? "left" : "right"}`;

    const button = document.createElement("button");
    button.type = "button";
    button.className = `trail-node is-${status}`;
    button.disabled = status === "locked";
    button.setAttribute("aria-label", status === "locked" ? `${menu.dish}, locked until the lesson before it is finished` : `${menu.dish}, ${menu.calories} kcal`);
    button.innerHTML = `<span aria-hidden="true">${nodeIcon}</span>`;
    if (status === "current") {
      const bubble = document.createElement("span");
      bubble.className = "trail-bubble";
      bubble.textContent = "Start";
      button.appendChild(bubble);
    }
    if (status !== "locked") button.addEventListener("click", () => onPick(menu));

    const label = document.createElement("span");
    label.className = "trail-label";
    label.innerHTML = `<strong>${menu.dish}</strong><small>${menu.calories} kcal</small>`;

    item.appendChild(button);
    item.appendChild(label);
    root.appendChild(item);
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
    button.innerHTML = `<span class="chef-mark">${renderPixelAvatarSVG(pack.id)}</span><span><strong>${pack.name}</strong><small>${pack.focus}</small></span><i>${pack.id === selectedId ? "Active" : "Choose"}</i>`;
    button.addEventListener("click", () => onPick(pack));
    root.appendChild(button);
  });
}

export function setMealToLog(dish, calories) {
  document.getElementById("meal-calorie-label").textContent = `${dish} · about ${calories} kcal`;
  document.getElementById("btn-log-meal").disabled = false;
}

export function showSafety(command) {
  const dialog = document.getElementById("safety-dialog");
  const content = document.getElementById("safety-content");
  if (command === "code_red") {
    content.innerHTML = `<h2 id="safety-title" class="code-red">⚠ Code red — stop cooking</h2><p>Move away from smoke, flame, or a gas smell. If anyone is in danger, call emergency services now.</p><a class="emergency-call" href="tel:911">Call 911</a><p class="safety-note">This action is intentionally manual. Ramsey will not place emergency calls automatically.</p>`;
  } else {
    content.innerHTML = `<h2 id="safety-title" class="code-yellow">⚠ Code yellow — first aid</h2><section class="first-aid-card"><strong>Burn or scald</strong><p>Move away from heat. Cool under cool or lukewarm running water for 20 minutes. Do not use ice, butter, toothpaste, or creams; remove jewellery or loose clothing only if it is not stuck to skin.</p></section><section class="first-aid-card"><strong>Cut or chopped finger</strong><p>Use a clean cloth or dressing and apply firm, direct pressure. Once bleeding is controlled, rinse a small wound with clean water and cover it with a sterile dressing.</p></section><section class="first-aid-card"><strong>Get urgent help now</strong><p>Call 911 for uncontrolled or spurting bleeding, a deep/gaping wound, loss of feeling or movement, a serious/chemical burn, trouble breathing, choking, or loss of consciousness.</p></section><p class="safety-note">This is immediate guidance, not a substitute for professional medical care.</p>`;
  }
  if (!dialog.open) dialog.showModal();
}

export function renderKitchenState(state) {
  document.getElementById('session-connection').textContent = state.completed ? 'Cooking complete in Quest.' : 'Recipe ready. Your headset will use this desktop session.';
  document.getElementById('session-points').textContent = state.completed ? `+${state.points} points${state.profile_saved ? ' saved to your profile.' : ' — profile sync pending.'}` : '';
  document.getElementById('step-progress').textContent = `${state.title} · Step ${state.step_index + 1} of ${state.total_steps}`;
  document.getElementById('step-text').textContent = state.current_step;
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
