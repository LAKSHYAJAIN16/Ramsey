export function showScreen(name) {
  document.getElementById("launcher").classList.toggle("hidden", name !== "launcher");
  document.getElementById("kitchen").classList.toggle("hidden", name !== "kitchen");
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
