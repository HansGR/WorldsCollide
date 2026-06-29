"use strict";

const fighters = {
  a: document.querySelector('.fighter[data-side="a"]'),
  b: document.querySelector('.fighter[data-side="b"]'),
};
let current = null;     // {a, b} enemy records currently shown
let nextPair = null;    // promise for the prefetched next match-up
let busy = false;       // lock during the brief result animation
let localVotes = 0;     // optimistic vote counter (server reconciles it)
let votesSinceSync = 0; // refresh full stats every few votes
let voteError = false;  // a background vote POST failed
const voteQueue = [];   // pending votes, sent one at a time
let sending = false;    // queue worker running?

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

async function fetchPair() {
  const res = await fetch("/api/pair");
  if (!res.ok) throw new Error("pair fetch failed");
  return res.json();
}

function prefetch() {
  // Grab the next match-up while the user looks at the current one, so the
  // swap after a vote is instant.
  nextPair = fetchPair().catch(() => null);
}

async function loadPair() {
  busy = true;
  try {
    const pending = nextPair;
    nextPair = null;
    current = (pending && (await pending)) || (await fetchPair());
    render("a", current.a);
    render("b", current.b);
    fighters.a.classList.remove("chosen", "faded");
    fighters.b.classList.remove("chosen", "faded");
    prefetch();
  } catch (e) {
    console.error(e);
  } finally {
    busy = false;
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

function vote(winnerSide) {
  if (busy || !current) return;
  busy = true;
  const winner = current[winnerSide];
  const loser = current[winnerSide === "a" ? "b" : "a"];

  fighters[winnerSide].classList.add("chosen");
  fighters[winnerSide === "a" ? "b" : "a"].classList.add("faded");

  sendVote(winner.slug, loser.slug);   // background, don't block the UI
  bumpVoteCount();                     // optimistic counter

  // Swap to the prefetched next pair almost immediately.
  setTimeout(loadPair, 150);
}

// Queue votes and POST them one at a time (with retry) so concurrent writes
// can't race or get dropped on the Sheets side. The UI never waits on this.
function sendVote(winner, loser) {
  voteQueue.push({ winner, loser });
  flushVotes();
}

async function flushVotes() {
  if (sending) return;
  sending = true;
  while (voteQueue.length) {
    const v = voteQueue[0];
    let ok = false;
    for (let attempt = 0; attempt < 3 && !ok; attempt++) {
      try {
        const res = await fetch("/api/vote", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...v, voter: voterId(), name: voterName() }),
        });
        ok = res.ok;
        if (!ok) console.error("vote rejected:", await res.json().catch(() => ({})));
      } catch (e) {
        console.error(e);
      }
      if (!ok) await new Promise((r) => setTimeout(r, 400 * (attempt + 1)));
    }
    voteQueue.shift();
    if (!ok) {
      voteError = true;
      const cov = document.getElementById("coverage");
      if (cov) cov.textContent = "⚠ a vote didn't save — see /api/health";
    }
  }
  sending = false;
}

function bumpVoteCount() {
  localVotes += 1;
  document.getElementById("vote-count").textContent = localVotes;
  if (++votesSinceSync >= 8) {
    votesSinceSync = 0;
    refreshStats();      // reconcile count + coverage in the background
  }
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

// --- stats + leaderboard ---------------------------------------------------
// (The tier list is deliberately NOT shown here -- seeing the live ranking
// would let someone game the calibration leaderboard. The owner reads it from
// the private "TierList" tab in the Google Sheet.)
async function refreshStats() {
  try {
    const s = await (await fetch("/api/stats")).json();
    // The Sheets vote log is cached server-side, so the server count can lag
    // the optimistic one -- take the larger so it never ticks backwards.
    localVotes = Math.max(localVotes, s.total_votes);
    document.getElementById("vote-count").textContent = localVotes;
    if (!voteError) {
      document.getElementById("coverage").textContent =
        s.unrated > 0 ? `${s.unrated} enemies still unrated` : `avg uncertainty ±${s.avg_rd}`;
    }
  } catch (e) { /* ignore */ }
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

loadPair();
refreshStats();
