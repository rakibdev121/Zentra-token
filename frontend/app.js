// ----- CONFIGURE THESE TWO LINES -----
const API_BASE = "https://YOUR-RENDER-BACKEND.onrender.com"; // your deployed FastAPI backend
const BOT_USERNAME = "YOUR_BOT_USERNAME";            // no @, from BotFather
// --------------------------------------

const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const initData = tg?.initData || "";

async function api(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}

let state = null;

function renderTop(s) {
  document.getElementById("coin-count").textContent = Math.floor(s.coins).toLocaleString();
  document.getElementById("miner-name").textContent = s.first_name || s.username || "Miner";
  document.getElementById("avatar").textContent = (s.first_name || s.username || "M")[0].toUpperCase();
  document.getElementById("streak-sub").textContent =
    s.daily_streak > 0 ? `${s.daily_streak}-day streak` : "No streak yet";

  const pct = Math.round((s.energy / s.max_energy) * 100);
  document.getElementById("energy-fill").style.width = pct + "%";
  document.getElementById("energy-label").textContent = `${Math.floor(s.energy)}/${s.max_energy}`;
}

function renderDaily(s) {
  const track = document.getElementById("streak-track");
  track.innerHTML = "";
  for (let i = 1; i <= 7; i++) {
    const d = document.createElement("div");
    d.className = "streak-day" + (i <= s.daily_streak ? " done" : "");
    d.textContent = "D" + i;
    track.appendChild(d);
  }
  const btn = document.getElementById("claim-btn");
  btn.disabled = !s.can_claim_daily;
  btn.textContent = s.can_claim_daily ? "Claim today's ore" : "Already claimed";
  document.getElementById("daily-hint").textContent = s.can_claim_daily
    ? "Reward grows with your streak, up to day 7."
    : "Come back after your 24-hour cooldown.";
}

function renderReferral(s) {
  document.getElementById("ref-count").textContent = s.referral_count;
  document.getElementById("ref-link").value =
    `https://t.me/${BOT_USERNAME}?startapp=${s.referral_code}`;
}

async function refresh() {
  state = await api("/api/me");
  renderTop(state);
  renderDaily(state);
  renderReferral(state);
}

function popCoin() {
  const layer = document.getElementById("pop-layer");
  const el = document.createElement("div");
  el.className = "pop";
  el.textContent = "+1";
  el.style.left = 40 + Math.random() * 120 + "px";
  el.style.top = 80 + Math.random() * 40 + "px";
  layer.appendChild(el);
  setTimeout(() => el.remove(), 700);
}

let pendingTaps = 0;
let flushTimer = null;

async function flushTaps() {
  if (pendingTaps === 0) return;
  const taps = pendingTaps;
  pendingTaps = 0;
  try {
    state = await api("/api/tap", { method: "POST", body: JSON.stringify({ taps }) });
    renderTop(state);
  } catch (e) {
    await refresh(); // resync on error (e.g. ran out of energy)
  }
}

document.getElementById("rock-btn").addEventListener("click", () => {
  if (!state || state.energy < 1) return;
  tg?.HapticFeedback?.impactOccurred("light");
  state.coins += 1;
  state.energy -= 1;
  renderTop(state);
  popCoin();
  pendingTaps += 1;
  clearTimeout(flushTimer);
  flushTimer = setTimeout(flushTaps, 400);
});

document.getElementById("claim-btn").addEventListener("click", async () => {
  try {
    const s = await api("/api/daily-bonus", { method: "POST" });
    state = s;
    renderTop(state);
    renderDaily(state);
  } catch (e) {
    alert(e.message);
  }
});

document.getElementById("copy-btn").addEventListener("click", () => {
  const input = document.getElementById("ref-link");
  input.select();
  navigator.clipboard?.writeText(input.value);
  tg?.HapticFeedback?.notificationOccurred("success");
});

async function loadLeaderboard() {
  const rows = await api("/api/leaderboard");
  const list = document.getElementById("board-list");
  list.innerHTML = "";
  rows.forEach((r) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="rank">#${r.rank}</span><span class="name">${r.name}</span><span class="amount">${r.coins.toLocaleString()}</span>`;
    list.appendChild(li);
  });
}

document.querySelectorAll(".tabbtn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tabbtn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    document.querySelectorAll(".tab, .shaft").forEach((t) => t.classList.add("hidden"));
    const target = btn.dataset.tab === "mine" ? "tab-mine" : "tab-" + btn.dataset.tab;
    document.getElementById(target).classList.remove("hidden");
    if (btn.dataset.tab === "leaderboard") loadLeaderboard();
  });
});

// Passive energy regen shown locally between server syncs
setInterval(() => {
  if (!state) return;
  state.energy = Math.min(state.max_energy, state.energy + 1 / 3);
  renderTop(state);
}, 1000);

refresh();
