"use strict";

const fighters = {
  a: document.querySelector('.fighter[data-side="a"]'),
  b: document.querySelector('.fighter[data-side="b"]'),
};
let current = null;     // {a, b} enemy records
let busy = false;       // lock during the result animation

// --- voter identity (anonymous, persisted in the browser) ------------------
function voterId() {
  let id = localStorage.getItem("coliseum_voter");
  if (!id) {
    id = (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2));
    localStorage.setItem("coliseum_voter", id);
  }
  return id;
}
function voterName() {
  return localStorage.getItem("coliseum_name") || "";
}
const nameInput = document.getElementById("voter-name");
if (nameInput) {
  nameInput.value = voterName();
  nameInput.addEventListener("change", () =>
    localStorage.setItem("coliseum_name", nameInput.value.trim().slice(0, 24)));
}

async function loadPair() {
  busy = true;
  try {
    const res = await fetch("/api/pair");
    current = await res.json();
    render("a", current.a);
    render("b", current.b);
    fighters.a.classList.remove("chosen", "faded");
    fighters.b.classList.remove("chosen", "faded");
    busy = false;
  } catch (e) {
    console.error(e);
  }
}

function render(side, enemy) {
  const el = fighters[side];
  const img = el.querySelector(".sprite");
  const wrap = el.querySelector(".sprite-wrap");
  wrap.classList.remove("noimg");
  img.classList.remove("missing");

  // Local sprite first, then the CoN CDN as a fallback, then a "?" placeholder.
  const sources = [enemy.sprite, enemy.sprite_cdn].filter(Boolean);
  let idx = 0;
  img.onerror = () => {
    idx += 1;
    if (idx < sources.length) {
      img.src = sources[idx];
    } else {
      img.classList.add("missing");
      wrap.classList.add("noimg");
    }
  };
  img.alt = enemy.name;
  if (sources.length) {
    img.src = sources[0];
  } else {
    img.classList.add("missing");
    wrap.classList.add("noimg");
  }

  el.querySelector(".name").textContent = enemy.name;

  // Location (with a Coliseum tag when relevant) instead of level/HP.
  let loc = enemy.location || "";
  if (enemy.coliseum && !/colosseum/i.test(loc)) {
    loc += (loc ? " &middot; " : "") + '<span class="tag">Coliseum</span>';
  }
  el.querySelector(".location").innerHTML = loc || "&mdash;";

  // Non-scaling stat block.
  for (const i of el.querySelectorAll(".stats i")) {
    const v = enemy[i.dataset.k];
    i.textContent = (v === null || v === undefined) ? "?" : v;
  }

  el.querySelector(".desc").textContent = enemy.description || "";
}

async function vote(winnerSide) {
  if (busy || !current) return;
  busy = true;
  const winner = current[winnerSide];
  const loser = current[winnerSide === "a" ? "b" : "a"];

  fighters[winnerSide].classList.add("chosen");
  fighters[winnerSide === "a" ? "b" : "a"].classList.add("faded");

  try {
    await fetch("/api/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        winner: winner.slug, loser: loser.slug,
        voter: voterId(), name: voterName(),
      }),
    });
  } catch (e) {
    console.error(e);
  }

  refreshStats();
  setTimeout(loadPair, 280);
}

fighters.a.addEventListener("click", () => vote("a"));
fighters.b.addEventListener("click", () => vote("b"));
document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") vote("a");
  else if (e.key === "ArrowRight") vote("b");
});
document.getElementById("skip").addEventListener("click", (e) => {
  e.preventDefault();
  if (!busy) loadPair();
});

// --- stats + live tier list ------------------------------------------------
async function refreshStats() {
  try {
    const s = await (await fetch("/api/stats")).json();
    document.getElementById("vote-count").textContent = s.total_votes;
    document.getElementById("coverage").textContent =
      s.unrated > 0 ? `${s.unrated} enemies still unrated` : `avg uncertainty ±${s.avg_rd}`;
  } catch (e) { /* ignore */ }
}

// Tier colours (tiers themselves are decided server-side, bottom-heavy).
const TIER_COLORS = {
  S: "#ff7676", A: "#ffb24a", B: "#ffe14a",
  C: "#9be15d", D: "#5dd6e1", E: "#9aa0d6",
};
const TIER_ORDER = ["S", "A", "B", "C", "D", "E"];

async function showStandings() {
  const data = await (await fetch("/api/standings")).json();
  const buckets = {};
  for (const e of data.standings) (buckets[e.tier] = buckets[e.tier] || []).push(e);
  const root = document.getElementById("tiers");
  root.innerHTML = "";
  for (const label of TIER_ORDER) {
    const items = buckets[label];
    if (!items || !items.length) continue;
    const chips = items.map((e) => {
      const img = e.sprite ? `<img src="${e.sprite}" alt="" onerror="this.remove()">` : "";
      return `<span class="chip">${img}${e.name} <span class="r">${e.rating}</span></span>`;
    }).join("");
    const row = document.createElement("div");
    row.className = "tier-row";
    row.innerHTML =
      `<div class="tier-label" style="background:${TIER_COLORS[label]}">${label}</div>` +
      `<div class="tier-items">${chips}</div>`;
    root.appendChild(row);
  }
}

async function showLeaderboard() {
  const data = await (await fetch("/api/leaderboard")).json();
  const root = document.getElementById("leaderboard-body");
  if (!data.leaderboard.length) {
    root.innerHTML =
      `<p class="empty">No one has cast ${data.min_votes}+ votes yet. Keep voting!</p>`;
    return;
  }
  const rows = data.leaderboard.map((v) =>
    `<tr><td>${v.rank}</td><td>${escapeHtml(v.name)}</td>` +
    `<td>${v.accuracy}%</td><td>${v.calibration}%</td><td>${v.votes}</td></tr>`).join("");
  root.innerHTML =
    `<p class="empty">Ranked by how often your picks match the crowd consensus ` +
    `(${data.total_voters} voters, ${data.min_votes}+ votes to qualify).</p>` +
    `<table class="board"><thead><tr><th>#</th><th>Player</th>` +
    `<th>Accuracy</th><th>Calibration</th><th>Votes</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function togglePanel(id, render) {
  const panel = document.getElementById(id);
  const hidden = panel.classList.toggle("hidden");
  if (!hidden) render();
}
document.getElementById("toggle-leaderboard").addEventListener("click", (e) => {
  e.preventDefault();
  togglePanel("leaderboard", showLeaderboard);
});

document.getElementById("toggle-standings").addEventListener("click", (e) => {
  e.preventDefault();
  const panel = document.getElementById("standings");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) showStandings();
});

loadPair();
refreshStats();
