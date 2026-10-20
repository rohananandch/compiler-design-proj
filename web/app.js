/**
 * Frontend Application Logic for Regex to Minimized DFA Studio.
 * Handles API communication, SVG graph rendering, table generation,
 * interactive simulation, and pan/zoom interactions.
 */

let currentPipelineData = null;
let currentSimulationData = null;

// SVG Viewport Pan/Zoom state map
const svgStates = {};

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupPresets();
  setupEvents();
  setupThemeToggle();
  // Initial load with default expression
  transformRegex("(a|b)*abb");
});

function setupTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const pane = document.getElementById(btn.getAttribute("data-tab"));
      if (pane) pane.classList.add("active");
    });
  });
}

function setupPresets() {
  document.querySelectorAll("#presetChips .chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const regex = chip.getAttribute("data-regex");
      document.getElementById("regexInput").value = regex;
      transformRegex(regex);
    });
  });

  document.querySelectorAll(".quick-sim-strings .chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const s = chip.getAttribute("data-sim");
      document.getElementById("simStringInput").value = s;
      simulateString(s);
    });
  });
}

function setupEvents() {
  const convertBtn = document.getElementById("convertBtn");
  const regexInput = document.getElementById("regexInput");

  convertBtn.addEventListener("click", () => {
    const val = regexInput.value.trim();
    if (val) transformRegex(val);
  });

  regexInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const val = regexInput.value.trim();
      if (val) transformRegex(val);
    }
  });

  document.getElementById("simBtn").addEventListener("click", () => {
    simulateString(document.getElementById("simStringInput").value);
  });

  document.getElementById("simStringInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") simulateString(e.target.value);
  });
}

function setupThemeToggle() {
  document.getElementById("themeToggleBtn").addEventListener("click", () => {
    const isLight = document.body.getAttribute("data-theme") === "light";
    if (isLight) {
      document.body.removeAttribute("data-theme");
    } else {
      document.body.setAttribute("data-theme", "light");
    }
    if (currentPipelineData) renderAllGraphs(currentPipelineData);
  });
}

/* ========================================================
   PIPELINE TRANSFORMATION
======================================================== */

async function transformRegex(regexStr) {
  const errorAlert = document.getElementById("errorAlert");
  errorAlert.classList.add("hidden");
  errorAlert.innerText = "";

  try {
    const response = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ regex: regexStr })
    });

    const data = await response.json();
    if (!data.success) {
      showError(data.error || "Failed to process regular expression.");
      return;
    }

    currentPipelineData = data.data;
    populateUI(currentPipelineData);
  } catch (err) {
    showError("Could not connect to server: " + err.message);
  }
}

function showError(msg) {
  const errorAlert = document.getElementById("errorAlert");
  errorAlert.innerText = msg;
  errorAlert.classList.remove("hidden");
}

/* ========================================================
   UI POPULATION
======================================================== */

function insertExplicitDots(str) {
  // Shows explicit concatenation operator insertion (preview only)
  let result = "";
  for (let i = 0; i < str.length; i++) {
    result += str[i];
    if (i + 1 < str.length) {
      const a = str[i];
      const b = str[i + 1];
      const aCanPrecede = /[a-zA-Z0-9ε*+?)]/. test(a);
      const bCanFollow  = /[a-zA-Z0-9ε(]/.test(b);
      if (aCanPrecede && bCanFollow) result += ".";
    }
  }
  return result;
}

function populateUI(data) {
  // Tab 1: Overview
  document.getElementById("overviewRegex").innerText    = data.regex;
  document.getElementById("overviewExplicit").innerText = insertExplicitDots(data.regex);
  document.getElementById("overviewPostfix").innerText  = data.postfix;
  document.getElementById("overviewAlphabet").innerText = "{ " + data.alphabet.join(", ") + " }";

  // Tab 2: NFA stats
  document.getElementById("nfaStateCount").innerText = data.nfa.total_states;
  document.getElementById("nfaTransCount").innerText = data.nfa.total_transitions;
  document.getElementById("nfaEpsCount").innerText   = data.nfa.epsilon_transitions;
  renderNFATable(data.nfa);

  // Tab 3: DFA stats
  document.getElementById("dfaStateCount").innerText = data.dfa.total_states;
  document.getElementById("dfaTransCount").innerText = data.dfa.total_transitions;
  renderDFATable(data.dfa);

  // Tab 4: Min DFA stats
  document.getElementById("minStateCount").innerText    = data.min_dfa.total_states;
  document.getElementById("minTransCount").innerText    = data.min_dfa.total_transitions;
  document.getElementById("minReductionPill").innerText = data.metrics.reductions.nfa_to_min_dfa_state_pct + "%";
  renderMinDFATable(data.min_dfa);

  // Tab 5: Metrics
  populateMetrics(data.metrics);

  // Render all SVG graphs
  renderAllGraphs(data);

  // Step-by-step Thompson gallery (Tab 2 bottom)
  if (data.nfa.construction_steps && data.nfa.construction_steps.length > 0) {
    renderStepByStepGallery(data.nfa.construction_steps);
  }
}

function populateMetrics(metrics) {
  const nfaStates = metrics.counts.nfa.states;
  const dfaStates = metrics.counts.dfa.states;
  const minStates = metrics.counts.min_dfa.states;

  document.getElementById("kpiNfaStates").innerText   = nfaStates;
  document.getElementById("kpiNfaTrans").innerText     = `${metrics.counts.nfa.transitions} transitions (${metrics.counts.nfa.epsilon_transitions} eps)`;
  document.getElementById("kpiDfaStates").innerText   = dfaStates;
  document.getElementById("kpiDfaTrans").innerText     = `${metrics.counts.dfa.transitions} transitions`;
  document.getElementById("kpiMinStates").innerText   = minStates;
  document.getElementById("kpiMinTrans").innerText     = `${metrics.counts.min_dfa.transitions} transitions`;
  document.getElementById("kpiNfaToMinPct").innerText = `${metrics.reductions.nfa_to_min_dfa_state_pct}%`;

  // Bar chart
  document.getElementById("barNfaVal").innerText = nfaStates;
  document.getElementById("barDfaVal").innerText = dfaStates;
  document.getElementById("barMinVal").innerText = minStates;
  const maxVal = Math.max(nfaStates, 1);
  document.getElementById("barNfa").style.width = "100%";
  document.getElementById("barDfa").style.width = `${Math.max((dfaStates / maxVal) * 100, 8)}%`;
  document.getElementById("barMin").style.width = `${Math.max((minStates / maxVal) * 100, 8)}%`;

  // Timings
  document.getElementById("timeParse").innerText = `${metrics.timings_us.parse.toFixed(1)} us`;
  document.getElementById("timeNfa").innerText   = `${metrics.timings_us.nfa.toFixed(1)} us`;
  document.getElementById("timeDfa").innerText   = `${metrics.timings_us.dfa.toFixed(1)} us`;
  document.getElementById("timeMin").innerText   = `${metrics.timings_us.minimization.toFixed(1)} us`;
  document.getElementById("timeTotal").innerText = `${metrics.timings_us.total.toFixed(1)} us (${(metrics.timings_us.total / 1000).toFixed(3)} ms)`;
}

/* ========================================================
   TABLE RENDERING
======================================================== */

function renderNFATable(nfa) {
  const container = document.getElementById("nfaTableContainer");
  const symbols = [...nfa.alphabet, "eps"];

  let html = `<table class="transition-table"><thead><tr><th>State</th>`;
  symbols.forEach(s => { html += `<th>${s}</th>`; });
  html += `</tr></thead><tbody>`;

  nfa.states.forEach(sid => {
    const isStart  = (sid === nfa.start_state);
    const isAccept = nfa.accept_states.includes(sid);
    const badge    = isStart ? "state-start" : (isAccept ? "state-accept" : "");
    const prefix   = isStart ? "&#x27A4; " : (isAccept ? "&#9733; " : "");

    html += `<tr><td><span class="state-badge ${badge}">${prefix}s${sid}</span></td>`;
    symbols.forEach(sym => {
      // Translate "eps" back to the epsilon character for matching
      const lookupSym = sym === "eps" ? "\u03b5" : sym;
      const matches = nfa.transitions.filter(t => t.from === sid && t.symbol === lookupSym);
      if (matches.length > 0) {
        html += `<td><code>{ ${matches.map(t => "s" + t.to).join(", ")} }</code></td>`;
      } else {
        html += `<td style="color:var(--text-muted);">-</td>`;
      }
    });
    html += `</tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

function renderDFATable(dfa) {
  const container = document.getElementById("dfaTableContainer");
  const alphabet  = dfa.alphabet;

  let html = `<table class="transition-table"><thead><tr><th>State</th><th>NFA Subset</th>`;
  alphabet.forEach(a => { html += `<th>${a}</th>`; });
  html += `</tr></thead><tbody>`;

  dfa.states.forEach(state => {
    const isStart  = state.is_start;
    const isAccept = state.is_accept;
    const badge    = isStart ? "state-start" : (isAccept ? "state-accept" : "");
    const prefix   = isStart ? "&#x27A4; " : (isAccept ? "&#9733; " : "");
    const subset   = `{ ${state.nfa_subset.join(", ")} }`;

    html += `<tr>
      <td><span class="state-badge ${badge}">${prefix}${state.name}</span></td>
      <td><code>${subset}</code></td>`;
    alphabet.forEach(sym => {
      const tr = dfa.transitions.find(t => t.from === state.id && t.symbol === sym);
      html += tr
        ? `<td><code>D${tr.to}</code></td>`
        : `<td style="color:var(--text-muted);">-</td>`;
    });
    html += `</tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

function renderMinDFATable(minDfa) {
  const container = document.getElementById("minTableContainer");
  const alphabet  = minDfa.alphabet;

  let html = `<table class="transition-table"><thead><tr><th>State</th><th>Merged States</th>`;
  alphabet.forEach(a => { html += `<th>${a}</th>`; });
  html += `</tr></thead><tbody>`;

  minDfa.states.forEach(state => {
    const isStart  = state.is_start;
    const isAccept = state.is_accept;
    const badge    = isStart ? "state-start" : (isAccept ? "state-accept" : "");
    const prefix   = isStart ? "&#x27A4; " : (isAccept ? "&#9733; " : "");
    const merged   = (minDfa.partition_mapping[state.name] || []).join(", ");

    html += `<tr>
      <td><span class="state-badge ${badge}">${prefix}${state.name}</span></td>
      <td><code>{ ${merged} }</code></td>`;
    alphabet.forEach(sym => {
      const tr = minDfa.transitions.find(t => t.from === state.id && t.symbol === sym);
      html += tr
        ? `<td><code>M${tr.to}</code></td>`
        : `<td style="color:var(--text-muted);">-</td>`;
    });
    html += `</tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

/* ========================================================
   SVG GRAPH RENDERING ENGINE
   Uses canonical geometric positions from Thompson Layout Engine.
   - Union → Diamond / parallel tracks (diagonal eps arrows)
   - Kleene Star → top loopback arc + bottom bypass arc
   - Concat → horizontal sequential merge
======================================================== */

function renderAllGraphs(data) {
  renderAutomatonGraph("nfaSvg", data.nfa,     "s");
  renderAutomatonGraph("dfaSvg", data.dfa,     "D");
  renderAutomatonGraph("minSvg", data.min_dfa, "M");
}

function renderStepByStepGallery(steps) {
  const container = document.getElementById("nfaStepGallery");
  if (!container) return;
  container.innerHTML = "";

  steps.forEach(step => {
    const item  = document.createElement("div");
    item.className = "step-nfa-item";
    const svgId = `step-svg-${step.step_number}`;

    item.innerHTML = `
      <div class="step-item-header">
        <h4>${step.title}</h4>
        <span class="badge badge-accent">${step.sub_regex}</span>
      </div>
      <div class="step-svg-box">
        <svg id="${svgId}"></svg>
      </div>`;
    container.appendChild(item);

    renderAutomatonGraph(svgId, step.nfa, "s", true);
  });
}

function renderAutomatonGraph(svgId, automaton, statePrefix, isMini = false) {
  const svg = document.getElementById(svgId);
  if (!svg) return;
  svg.innerHTML = "";

  const stateIds  = automaton.states.map(s => typeof s === "object" ? s.id : s);
  const numStates = stateIds.length;
  if (numStates === 0) return;

  const positions      = {};
  let   defaultViewBox = [0, 0, 800, 480];

  // ── 1. Prefer canonical geometric positions from Thompson Layout Engine ──
  if (automaton.positions && Object.keys(automaton.positions).length > 0) {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

    stateIds.forEach(sid => {
      const p = automaton.positions[sid] || automaton.positions[String(sid)] || { x: 0, y: 0 };
      positions[sid] = { x: p.x, y: p.y };
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    });

    const padX = isMini ? 70 : 110;
    const padY = isMini ? 75 : 120;
    const vbW  = Math.max(maxX - minX + padX * 2, 400);
    const vbH  = Math.max(maxY - minY + padY * 2, isMini ? 190 : 360);

    defaultViewBox = [minX - padX, minY - padY, vbW, vbH];

  } else {
    // ── 2. Rank-based layered layout for DFA / Min DFA (no positions) ──
    const ranks    = computeStateRanks(automaton, stateIds);
    const layerMap = {};
    stateIds.forEach(sid => {
      const r = ranks[sid] || 0;
      if (!layerMap[r]) layerMap[r] = [];
      layerMap[r].push(sid);
    });

    const maxRank  = Math.max(...Object.keys(layerMap).map(Number), 0);
    const startX   = 140;
    const stepX    = 170;
    const vbWidth  = Math.max(startX + (maxRank + 1) * stepX + 80, 750);
    const vbHeight = 400;

    Object.entries(layerMap).forEach(([rStr, sids]) => {
      const r      = parseInt(rStr, 10);
      const x      = startX + r * stepX;
      const stepY  = sids.length > 1 ? 120 : 0;
      const startY = vbHeight / 2 - ((sids.length - 1) * stepY) / 2;
      sids.forEach((sid, idx) => {
        positions[sid] = { x, y: startY + idx * stepY };
      });
    });

    defaultViewBox = [0, 0, vbWidth, vbHeight];
  }

  // ── Arrow marker defs ──
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <marker id="arr-${svgId}" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#94a3b8"/>
    </marker>
    <marker id="arr-start-${svgId}" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#3b82f6"/>
    </marker>
    <marker id="arr-eps-${svgId}" viewBox="0 0 10 10" refX="27" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 10 5 L 0 8.5 z" fill="#8b5cf6"/>
    </marker>`;
  svg.appendChild(defs);

  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
  svg.appendChild(g);

  // ── Build edge map (group multi-symbol edges) ──
  const edgeMap = {};
  automaton.transitions.forEach(t => {
    const key = `${t.from}→${t.to}`;
    if (!edgeMap[key]) edgeMap[key] = { from: t.from, to: t.to, symbols: [], route: t.route || "straight" };
    edgeMap[key].symbols.push(t.symbol);
    if (t.route && t.route !== "straight") edgeMap[key].route = t.route;
  });

  // ── Draw edges ──
  Object.values(edgeMap).forEach(edge => {
    const p1  = positions[edge.from];
    const p2  = positions[edge.to];
    if (!p1 || !p2) return;

    const label = edge.symbols.map(s => s === "\u03b5" ? "eps" : s).join(",");
    const isEps = edge.symbols.some(s => s === "\u03b5");

    if (edge.from === edge.to) {
      drawSelfLoop(g, p1, label, svgId, isEps);
    } else if (edge.route === "loopback_top") {
      drawArcTop(g, p1, p2, label, svgId);
    } else if (edge.route === "bypass_bottom") {
      drawArcBottom(g, p1, p2, label, svgId);
    } else {
      const reverseExists = Boolean(edgeMap[`${edge.to}→${edge.from}`]);
      drawEdge(g, p1, p2, label, isEps, reverseExists, svgId);
    }
  });

  // ── Draw start arrow ──
  const sp = positions[automaton.start_state];
  if (sp) drawStartArrow(g, sp, svgId);

  // ── Draw state nodes ──
  stateIds.forEach(sid => {
    const pos      = positions[sid];
    if (!pos) return;
    const isStart  = (sid === automaton.start_state);
    const isAccept = automaton.accept_states.includes(sid);
    const label    = `${statePrefix}${sid}`;

    let subLabel = "";
    if (statePrefix === "D") {
      const sObj = automaton.states.find(s => typeof s === "object" && s.id === sid);
      if (sObj) {
        const sub = sObj.nfa_subset || [];
        subLabel = `{${sub.slice(0, 4).join(",")}${sub.length > 4 ? "..." : ""}}`;
      }
    } else if (statePrefix === "M") {
      const sObj = automaton.states.find(s => typeof s === "object" && s.id === sid);
      if (sObj && automaton.partition_mapping) {
        subLabel = `{${(automaton.partition_mapping[sObj.name] || []).join(",")}}`;
      }
    }

    drawNode(g, pos.x, pos.y, label, subLabel, isStart, isAccept, isMini);
  });

  // ── Viewbox / pan-zoom init ──
  initPanZoom(svg, defaultViewBox);
}

/* ──────── Individual drawing helpers ──────── */

function drawEdge(container, p1, p2, label, isEps, curved, svgId) {
  const g   = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const dx  = p2.x - p1.x, dy = p2.y - p1.y;
  const len = Math.sqrt(dx*dx + dy*dy) || 1;

  let pathD, tx, ty;

  if (curved) {
    const k  = 28;
    const nx = -dy / len, ny = dx / len;
    const cx = (p1.x + p2.x) / 2 + nx * k;
    const cy = (p1.y + p2.y) / 2 + ny * k;
    pathD = `M ${p1.x} ${p1.y} Q ${cx} ${cy} ${p2.x} ${p2.y}`;
    tx = cx; ty = cy - 4;
  } else {
    pathD = `M ${p1.x} ${p1.y} L ${p2.x} ${p2.y}`;
    tx = (p1.x + p2.x) / 2;
    ty = (p1.y + p2.y) / 2 - 9;
  }

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", pathD);
  path.setAttribute("stroke", isEps ? "#8b5cf6" : "#64748b");
  path.setAttribute("stroke-width", "2");
  path.setAttribute("fill", "none");
  path.setAttribute("marker-end", `url(#${isEps ? "arr-eps" : "arr"}-${svgId})`);
  g.appendChild(path);

  drawEdgeLabel(g, tx, ty, label, isEps);
  container.appendChild(g);
}

function drawArcTop(container, p1, p2, label, svgId) {
  // High arc curving over the top — for star loopback (accept → start)
  const g     = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const apexY = Math.min(p1.y, p2.y) - 80;
  const mid   = (p1.x + p2.x) / 2;

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", `M ${p1.x} ${p1.y} C ${p1.x - 15} ${apexY}, ${p2.x + 15} ${apexY}, ${p2.x} ${p2.y}`);
  path.setAttribute("stroke", "#8b5cf6");
  path.setAttribute("stroke-width", "2.2");
  path.setAttribute("fill", "none");
  path.setAttribute("marker-end", `url(#arr-eps-${svgId})`);
  g.appendChild(path);

  drawEdgeLabel(g, mid, apexY - 8, label, true);
  container.appendChild(g);
}

function drawArcBottom(container, p1, p2, label, svgId) {
  // Low arc curving under the bottom — for star bypass (start → accept skip)
  const g       = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const troughY = Math.max(p1.y, p2.y) + 80;
  const mid     = (p1.x + p2.x) / 2;

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", `M ${p1.x} ${p1.y} C ${p1.x + 15} ${troughY}, ${p2.x - 15} ${troughY}, ${p2.x} ${p2.y}`);
  path.setAttribute("stroke", "#8b5cf6");
  path.setAttribute("stroke-width", "2.2");
  path.setAttribute("fill", "none");
  path.setAttribute("marker-end", `url(#arr-eps-${svgId})`);
  g.appendChild(path);

  drawEdgeLabel(g, mid, troughY + 12, label, true);
  container.appendChild(g);
}

function drawSelfLoop(container, p, label, svgId, isEps) {
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", `M ${p.x - 12} ${p.y - 18} C ${p.x - 32} ${p.y - 68}, ${p.x + 32} ${p.y - 68}, ${p.x + 12} ${p.y - 18}`);
  path.setAttribute("stroke", isEps ? "#8b5cf6" : "#64748b");
  path.setAttribute("stroke-width", "2");
  path.setAttribute("fill", "none");
  path.setAttribute("marker-end", `url(#${isEps ? "arr-eps" : "arr"}-${svgId})`);
  g.appendChild(path);

  drawEdgeLabel(g, p.x, p.y - 72, label, isEps);
  container.appendChild(g);
}

function drawEdgeLabel(container, x, y, label, isEps) {
  const w   = Math.max(label.length * 8 + 10, 22);
  const bg  = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x",      x - w / 2);
  bg.setAttribute("y",      y - 10);
  bg.setAttribute("width",  w);
  bg.setAttribute("height", 16);
  bg.setAttribute("rx",     "4");
  bg.setAttribute("fill",   "var(--bg-primary)");
  bg.setAttribute("stroke", isEps ? "#8b5cf6" : "var(--border-color)");
  bg.setAttribute("stroke-width", "1");
  container.appendChild(bg);

  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x",           x);
  text.setAttribute("y",           y + 2);
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("font-family", "Fira Code, monospace");
  text.setAttribute("font-size",   "11px");
  text.setAttribute("font-weight", "600");
  text.setAttribute("fill",        isEps ? "#a78bfa" : "#38bdf8");
  text.textContent = label;
  container.appendChild(text);
}

function drawStartArrow(container, p, svgId) {
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", `M ${p.x - 60} ${p.y} L ${p.x} ${p.y}`);
  path.setAttribute("stroke", "#3b82f6");
  path.setAttribute("stroke-width", "3");
  path.setAttribute("fill", "none");
  path.setAttribute("marker-end", `url(#arr-start-${svgId})`);
  g.appendChild(path);

  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x",           p.x - 45);
  text.setAttribute("y",           p.y - 8);
  text.setAttribute("font-family", "Inter, sans-serif");
  text.setAttribute("font-size",   "10px");
  text.setAttribute("font-weight", "700");
  text.setAttribute("fill",        "#3b82f6");
  text.textContent = "START";
  g.appendChild(text);

  container.appendChild(g);
}

function drawNode(container, x, y, label, subLabel, isStart, isAccept, isMini) {
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

  const rInner = isMini ? 16 : (isAccept ? 20 : 22);
  const rOuter = isMini ? 20 : 25;

  // Double-circle outer ring for accept state
  if (isAccept) {
    const outer = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    outer.setAttribute("cx", x); outer.setAttribute("cy", y); outer.setAttribute("r", rOuter);
    outer.setAttribute("fill", "none");
    outer.setAttribute("stroke", "#10b981");
    outer.setAttribute("stroke-width", "2.5");
    g.appendChild(outer);
  }

  // Main circle
  const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  circle.setAttribute("cx", x); circle.setAttribute("cy", y); circle.setAttribute("r", rInner);
  circle.setAttribute("fill",   isStart ? "#1e3a8a" : (isAccept ? "#064e3b" : "var(--bg-secondary)"));
  circle.setAttribute("stroke", isStart ? "#3b82f6" : (isAccept ? "#10b981" : "var(--border-color)"));
  circle.setAttribute("stroke-width", "2");
  g.appendChild(circle);

  // State label
  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x", x); text.setAttribute("y", y + 5);
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("font-family", "Fira Code, monospace");
  text.setAttribute("font-size",   isMini ? "11px" : "13px");
  text.setAttribute("font-weight", "700");
  text.setAttribute("fill", "var(--text-main)");
  text.textContent = label;
  g.appendChild(text);

  // Sub-label (NFA subset or merged states) — only in full-size view
  if (subLabel && !isMini) {
    const sub = document.createElementNS("http://www.w3.org/2000/svg", "text");
    sub.setAttribute("x", x); sub.setAttribute("y", y + 36);
    sub.setAttribute("text-anchor", "middle");
    sub.setAttribute("font-family", "Fira Code, monospace");
    sub.setAttribute("font-size",   "9px");
    sub.setAttribute("fill", "var(--text-muted)");
    sub.textContent = subLabel;
    g.appendChild(sub);
  }

  container.appendChild(g);
}

/* ──────── Pan & Zoom ──────── */

function computeStateRanks(automaton, stateIds) {
  const ranks = {};
  const start = automaton.start_state;
  ranks[start] = 0;
  const queue = [start];
  while (queue.length > 0) {
    const curr = queue.shift();
    automaton.transitions.forEach(t => {
      if (t.from === curr && t.to !== curr && ranks[t.to] === undefined) {
        ranks[t.to] = ranks[curr] + 1;
        queue.push(t.to);
      }
    });
  }
  stateIds.forEach(sid => { if (ranks[sid] === undefined) ranks[sid] = 1; });
  return ranks;
}

function initPanZoom(svg, bounds) {
  const id = svg.getAttribute("id");
  svgStates[id] = {
    viewBox:        [...bounds],
    defaultViewBox: [...bounds],
    isPanning: false,
    startX: 0,
    startY: 0
  };
  svg.setAttribute("viewBox", bounds.join(" "));

  svg.onmousedown = e => { svgStates[id].isPanning = true; svgStates[id].startX = e.clientX; svgStates[id].startY = e.clientY; };
  svg.onmouseup   = () => { svgStates[id].isPanning = false; };
  svg.onmouseleave = () => { svgStates[id].isPanning = false; };

  svg.onmousemove = e => {
    if (!svgStates[id].isPanning) return;
    const vb = svgStates[id].viewBox;
    const dx = (e.clientX - svgStates[id].startX) * (vb[2] / (svg.clientWidth  || 1));
    const dy = (e.clientY - svgStates[id].startY) * (vb[3] / (svg.clientHeight || 1));
    vb[0] -= dx; vb[1] -= dy;
    svgStates[id].startX = e.clientX; svgStates[id].startY = e.clientY;
    svg.setAttribute("viewBox", vb.join(" "));
  };

  svg.onwheel = e => {
    e.preventDefault();
    const f = e.deltaY > 0 ? 1.1 : 0.9;
    const vb = svgStates[id].viewBox;
    vb[2] *= f; vb[3] *= f;
    svg.setAttribute("viewBox", vb.join(" "));
  };
}

function resetGraphView(svgId) {
  const st  = svgStates[svgId];
  const svg = document.getElementById(svgId);
  if (st && svg) {
    st.viewBox = [...st.defaultViewBox];
    svg.setAttribute("viewBox", st.viewBox.join(" "));
  }
}

/* ========================================================
   STRING SIMULATOR
======================================================== */

async function simulateString(inputStr) {
  const regex = document.getElementById("regexInput").value.trim();
  if (!regex) return;

  try {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ regex, string: inputStr })
    });

    const data = await response.json();
    if (!data.success) { alert("Simulation error: " + data.error); return; }
    renderSimulationResults(data.simulation);
  } catch (err) {
    alert("Network error: " + err.message);
  }
}

function renderSimulationResults(sim) {
  const section = document.getElementById("simResultsSection");
  section.classList.remove("hidden");

  const banner = document.getElementById("simVerdictBanner");
  banner.className = "sim-verdict-banner " + (sim.accepted ? "verdict-accepted" : "verdict-rejected");
  document.getElementById("simVerdictIcon").innerText    = sim.accepted ? "✅" : "❌";
  document.getElementById("simVerdictTitle").innerText   = sim.accepted ? `"${sim.input_string}" is ACCEPTED` : `"${sim.input_string}" is REJECTED`;
  document.getElementById("simVerdictSubtitle").innerText = sim.equivalent_across_all
    ? "NFA, DFA, and Minimized DFA all produced matching verdicts."
    : "Warning: Decision mismatch across automata!";

  // Min DFA trace
  const minTrace = document.getElementById("minTraceList");
  minTrace.innerHTML = "";
  (sim.min_dfa.trace || []).forEach(item => {
    const div = document.createElement("div");
    div.className = "trace-item";
    div.innerHTML = `
      <span class="trace-step">Step ${item.step}</span>
      <span class="trace-char">${item.symbol}</span>
      <span class="trace-state"><strong>${item.state_name}</strong></span>`;
    minTrace.appendChild(div);
  });

  // NFA trace
  const nfaTrace = document.getElementById("nfaTraceList");
  nfaTrace.innerHTML = "";
  (sim.nfa.trace || []).forEach(item => {
    const div = document.createElement("div");
    div.className = "trace-item";
    div.innerHTML = `
      <span class="trace-step">Step ${item.step}</span>
      <span class="trace-char">${item.symbol}</span>
      <span class="trace-state"><code>{ ${item.active_states.map(s => "s" + s).join(", ")} }</code></span>`;
    nfaTrace.appendChild(div);
  });
}

/* ========================================================
   DOT EXPORT MODAL & REPORT
======================================================== */

function exportDotModal(type) {
  if (!currentPipelineData) return;
  const modal    = document.getElementById("dotModal");
  const title    = document.getElementById("dotModalTitle");
  const textarea = document.getElementById("dotTextarea");

  const labels = { nfa: "Thompson NFA", dfa: "Subset DFA", min_dfa: "Hopcroft Minimized DFA" };
  title.innerText    = labels[type] + " (Graphviz DOT Code)";
  textarea.value     = currentPipelineData.dot[type];
  modal.classList.remove("hidden");
}

function closeDotModal() {
  document.getElementById("dotModal").classList.add("hidden");
}

function copyDotCode() {
  const textarea = document.getElementById("dotTextarea");
  textarea.select();
  navigator.clipboard.writeText(textarea.value);
  alert("DOT code copied to clipboard!");
}

function copyReportMarkdown() {
  if (!currentPipelineData) return;
  const m  = currentPipelineData.metrics;
  const md = `# State Reduction & Efficiency Report
**Input Regex**: \`${currentPipelineData.regex}\`
**Postfix Notation**: \`${currentPipelineData.postfix}\`
**Alphabet**: \`${currentPipelineData.alphabet.join(", ")}\`

## Machine State Comparison
| Stage | States | Transitions | Notes |
|-------|--------|-------------|-------|
| Thompson NFA | ${m.counts.nfa.states} | ${m.counts.nfa.transitions} | ${m.counts.nfa.epsilon_transitions} eps-moves |
| Subset DFA | ${m.counts.dfa.states} | ${m.counts.dfa.transitions} | Deterministic |
| Hopcroft Min DFA | ${m.counts.min_dfa.states} | ${m.counts.min_dfa.transitions} | Minimal |

## Optimizations Achieved
- **NFA to Min DFA State Reduction**: ${m.reductions.nfa_to_min_dfa_state_pct}%
- **DFA to Min DFA State Reduction**: ${m.reductions.dfa_to_min_dfa_state_pct}%
- **Total Pipeline Execution Latency**: ${m.timings_us.total.toFixed(1)} us
`;
  navigator.clipboard.writeText(md);
  alert("Markdown Report copied to clipboard!");
}
