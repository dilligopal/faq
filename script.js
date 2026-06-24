/**
 * script.js — FAQ Chatbot (Python/Flask edition)
 * All UI logic. No API keys here — requests go to the Flask backend.
 */
"use strict";

// ── Config ────────────────────────────────────────────────────────────────────
const API_URL       = "http://localhost:5000/api/chat";
const LS_HISTORY    = "faq_py_history";
const LS_THEME      = "faq_py_theme";
const WELCOME       = "Hello! 👋 Ask me anything about our FAQs.";
const MAX_MSGS      = 80;

// ── DOM ───────────────────────────────────────────────────────────────────────
const chatFab      = document.getElementById("chatFab");
const chatWindow   = document.getElementById("chatWindow");
const closeBtn     = document.getElementById("closeBtn");
const clearBtn     = document.getElementById("clearBtn");
const darkToggle   = document.getElementById("darkToggle");
const messagesWrap = document.getElementById("messagesWrap");
const userInput    = document.getElementById("userInput");
const sendBtn      = document.getElementById("sendBtn");
const quickArea    = document.getElementById("quickArea");
const fabBadge     = document.getElementById("fabBadge");
const fabOpen      = chatFab.querySelector(".fab-open");
const fabClose     = chatFab.querySelector(".fab-close");
const iconSun      = darkToggle.querySelector(".icon-sun");
const iconMoon     = darkToggle.querySelector(".icon-moon");

// ── State ─────────────────────────────────────────────────────────────────────
let isOpen    = false;
let busy      = false;
let typingEl  = null;
let history   = [];   // [{role, text, source, time}]

// ── Helpers ───────────────────────────────────────────────────────────────────
const esc = (s) =>
  s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
   .replace(/"/g,"&quot;").replace(/'/g,"&#039;");

const ts = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

function scrollBottom() {
  requestAnimationFrame(() => { messagesWrap.scrollTop = messagesWrap.scrollHeight; });
}

// ── Render one message ────────────────────────────────────────────────────────
function renderMsg(msg) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${msg.role}`;

  const avatarHTML = msg.role === "bot"
    ? `<div class="msg-ava">
         <svg viewBox="0 0 24 24" fill="currentColor">
           <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7H3a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2zM7.5 14.5a1.5 1.5 0 1 0 3 0 1.5 1.5 0 0 0-3 0zm7 0a1.5 1.5 0 1 0 3 0 1.5 1.5 0 0 0-3 0z"/>
         </svg>
       </div>`
    : "";

  const srcHTML = (msg.role === "bot" && msg.source)
    ? `<span class="src-badge src-${msg.source}">${msg.source.toUpperCase()}</span>`
    : "";

  wrap.innerHTML = `
    <div class="msg-row">
      ${avatarHTML}
      <div class="bubble">${esc(msg.text)}</div>
    </div>
    ${srcHTML}
    <span class="msg-time">${msg.time}</span>
  `;

  messagesWrap.appendChild(wrap);
  scrollBottom();
}

// ── Restore all history ────────────────────────────────────────────────────────
function renderAll() {
  messagesWrap.innerHTML = "";
  history.forEach(renderMsg);
}

// ── Typing indicator ───────────────────────────────────────────────────────────
function showTyping() {
  typingEl = document.createElement("div");
  typingEl.className = "msg bot";
  typingEl.innerHTML = `
    <div class="msg-row">
      <div class="msg-ava">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7H3a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
        </svg>
      </div>
      <div class="bubble">
        <div class="typing-dots">
          <div class="t-dot"></div><div class="t-dot"></div><div class="t-dot"></div>
        </div>
      </div>
    </div>`;
  messagesWrap.appendChild(typingEl);
  scrollBottom();
}

function hideTyping() {
  typingEl?.remove();
  typingEl = null;
}

// ── Persist history ────────────────────────────────────────────────────────────
function saveHistory() {
  localStorage.setItem(LS_HISTORY, JSON.stringify(history.slice(-MAX_MSGS)));
}

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(LS_HISTORY) || "[]");
  } catch { return []; }
}

// ── Add message ────────────────────────────────────────────────────────────────
function addMsg(role, text, source = null) {
  const msg = { role, text, source, time: ts() };
  history.push(msg);
  saveHistory();
  renderMsg(msg);
}

// ── Send ───────────────────────────────────────────────────────────────────────
async function send(text) {
  text = text.trim();
  if (!text || busy) return;

  addMsg("user", text);
  quickArea.style.display = "none";

  userInput.value = "";
  userInput.disabled = true;
  sendBtn.disabled = true;
  busy = true;

  showTyping();

  try {
    const res  = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    hideTyping();

    if (data?.answer) {
      addMsg("bot", data.answer, data.source || "fallback");
    } else {
      addMsg("bot", "Sorry, I couldn't find a reliable answer for that question. Try rephrasing it.", "fallback");
    }
  } catch {
    hideTyping();
    addMsg("bot", "⚠️ Cannot reach the server. Make sure the Python backend is running on port 5000.", "error");
  } finally {
    userInput.disabled = false;
    sendBtn.disabled = false;
    busy = false;
    userInput.focus();
  }
}

// ── Open / Close ───────────────────────────────────────────────────────────────
function openChat() {
  isOpen = true;
  chatWindow.classList.add("open");
  chatWindow.setAttribute("aria-hidden", "false");
  fabOpen.style.display  = "none";
  fabClose.style.display = "block";
  fabBadge.style.display = "none";
  chatFab.setAttribute("aria-label", "Close FAQ Assistant");
  userInput.focus();
  scrollBottom();
}

function closeChat() {
  isOpen = false;
  chatWindow.classList.remove("open");
  chatWindow.setAttribute("aria-hidden", "true");
  fabOpen.style.display  = "block";
  fabClose.style.display = "none";
  chatFab.setAttribute("aria-label", "Open FAQ Assistant");
}

function clearChat() {
  if (!confirm("Clear all chat messages?")) return;
  history = [];
  localStorage.removeItem(LS_HISTORY);
  messagesWrap.innerHTML = "";
  addMsg("bot", WELCOME, null);
  quickArea.style.display = "flex";
}

// ── Dark mode ──────────────────────────────────────────────────────────────────
function applyTheme(dark) {
  document.body.classList.toggle("dark", dark);
  if (dark) {
    iconSun.style.display  = "none";
    iconMoon.style.display = "block";
  } else {
    iconSun.style.display  = "block";
    iconMoon.style.display = "none";
  }
}

function toggleTheme() {
  const dark = !document.body.classList.contains("dark");
  applyTheme(dark);
  localStorage.setItem(LS_THEME, dark ? "dark" : "light");
}

// ── Events ─────────────────────────────────────────────────────────────────────
chatFab.addEventListener("click", () => isOpen ? closeChat() : openChat());
closeBtn.addEventListener("click", closeChat);
clearBtn.addEventListener("click", clearChat);
darkToggle.addEventListener("click", toggleTheme);

sendBtn.addEventListener("click", () => send(userInput.value));
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(userInput.value); }
});

quickArea.addEventListener("click", (e) => {
  const chip = e.target.closest(".qchip");
  if (chip?.dataset.msg) { userInput.value = chip.dataset.msg; send(chip.dataset.msg); }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && isOpen) closeChat();
});

// ── Init ───────────────────────────────────────────────────────────────────────
(function init() {
  // Theme
  applyTheme(localStorage.getItem(LS_THEME) === "dark");

  // History
  history = loadHistory();

  if (history.length) {
    renderAll();
    quickArea.style.display = "none";
    fabBadge.style.display = "flex";
  } else {
    addMsg("bot", WELCOME, null);
  }

  chatFab.classList.add("pulse");
})();
