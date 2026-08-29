/* ── API Base ─────────────────────────────────────────────────── */
// Works whether opened via file://, localhost, or 127.0.0.1
const API = "http://127.0.0.1:8000";

/* ── State ───────────────────────────────────────────────────── */
const state = {
  documents: [],          // { doc_id, filename, word_count, content_preview }
  activeDocId: null,
  chatHistory: [],
  quizAnswered: new Set(),
};

/* ── Toast ───────────────────────────────────────────────────── */
function toast(msg, type = "info") {
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

/* ── Fetch helper ────────────────────────────────────────────── */
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

/* ── Navigation ──────────────────────────────────────────────── */
function navigate(tabId) {
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById(tabId).classList.add("active");
  document.querySelector(`[data-tab="${tabId}"]`).classList.add("active");
  document.querySelector(".topbar h2").textContent =
    document.querySelector(`[data-tab="${tabId}"] .nav-label`)?.textContent || "AI Study Buddy";
  // Close sidebar on mobile
  document.querySelector(".sidebar").classList.remove("open");
}

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => navigate(item.dataset.tab));
});

document.querySelector(".hamburger")?.addEventListener("click", () => {
  document.querySelector(".sidebar").classList.toggle("open");
});

/* ═══════════════════════════════════════════════════════════════
   1. DOCUMENTS
═══════════════════════════════════════════════════════════════ */

async function loadDocuments() {
  try {
    state.documents = await apiFetch("/api/documents/list");
    renderDocumentList();
    updateDocSelectors();
  } catch (e) {
    console.warn("Could not load documents:", e.message);
  }
}

function renderDocumentList() {
  const container = document.getElementById("doc-list");
  const countEl = document.getElementById("doc-count");

  if (countEl) countEl.textContent = state.documents.length;

  if (!state.documents.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📂</div>
        <p>No documents uploaded yet.<br>Upload a PDF, TXT, or Markdown file to get started.</p>
      </div>`;
    return;
  }

  container.innerHTML = state.documents.map(doc => `
    <div class="doc-item" data-id="${doc.doc_id}">
      <div class="doc-info">
        <div class="doc-name" title="${doc.filename}">${doc.filename}</div>
        <div class="doc-meta">ID: ${doc.doc_id} · ${doc.word_count.toLocaleString()} words</div>
        <div class="doc-meta" style="margin-top:2px; font-size:11px; opacity:0.7">${doc.content_preview.slice(0, 100)}…</div>
      </div>
      <div class="doc-actions">
        <button class="btn btn-ghost btn-sm" onclick="setActiveDoc('${doc.doc_id}', '${doc.filename}')">Use</button>
        <button class="btn btn-danger btn-sm" onclick="deleteDoc('${doc.doc_id}')">🗑</button>
      </div>
    </div>`).join("");
}

function updateDocSelectors() {
  const options = [`<option value="">— Paste text below —</option>`,
    ...state.documents.map(d => `<option value="${d.doc_id}">${d.filename} (${d.doc_id})</option>`)
  ].join("");
  document.querySelectorAll(".doc-selector").forEach(sel => sel.innerHTML = options);

  if (state.activeDocId) {
    document.querySelectorAll(".doc-selector").forEach(sel => sel.value = state.activeDocId);
  }
}

function setActiveDoc(docId, filename) {
  state.activeDocId = docId;
  document.querySelectorAll(".doc-selector").forEach(sel => sel.value = docId);
  document.getElementById("active-doc-badge").textContent = `📄 ${filename}`;
  document.getElementById("active-doc-badge").style.display = "inline-flex";
  toast(`Active document set to "${filename}"`, "success");
}

async function deleteDoc(docId) {
  if (!confirm("Delete this document?")) return;
  try {
    await apiFetch(`/api/documents/${docId}`, { method: "DELETE" });
    state.documents = state.documents.filter(d => d.doc_id !== docId);
    if (state.activeDocId === docId) {
      state.activeDocId = null;
      document.getElementById("active-doc-badge").style.display = "none";
    }
    renderDocumentList();
    updateDocSelectors();
    toast("Document deleted", "success");
  } catch (e) {
    toast(e.message, "error");
  }
}

/* ── File Upload ─────────────────────────────────────────────── */
const uploadInput = document.getElementById("file-input");
const uploadZone  = document.getElementById("upload-zone");

uploadZone?.addEventListener("dragover", e => { e.preventDefault(); uploadZone.classList.add("drag-over"); });
uploadZone?.addEventListener("dragleave", () => uploadZone.classList.remove("drag-over"));
uploadZone?.addEventListener("drop", e => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]);
});

uploadInput?.addEventListener("change", () => {
  if (uploadInput.files[0]) handleUpload(uploadInput.files[0]);
});

async function handleUpload(file) {
  const btn = document.getElementById("upload-btn");
  const statusEl = document.getElementById("upload-status");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Uploading…`;
  statusEl.textContent = "";

  const fd = new FormData();
  fd.append("file", file);
  try {
    const doc = await apiFetch("/api/documents/upload", { method: "POST", body: fd });
    state.documents.push(doc);
    renderDocumentList();
    updateDocSelectors();
    setActiveDoc(doc.doc_id, doc.filename);
    statusEl.innerHTML = `<span style="color:var(--green)">✅ Uploaded "${doc.filename}" · ${doc.word_count} words</span>`;
    toast(`"${doc.filename}" uploaded successfully!`, "success");
  } catch (e) {
    statusEl.innerHTML = `<span style="color:var(--red)">❌ ${e.message}</span>`;
    toast(e.message, "error");
  }
  btn.disabled = false;
  btn.innerHTML = `📤 Upload`;
  uploadInput.value = "";
}

/* ═══════════════════════════════════════════════════════════════
   2. ELI10 EXPLAIN
═══════════════════════════════════════════════════════════════ */

document.getElementById("eli10-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const docId  = document.getElementById("eli10-doc").value;
  const text   = document.getElementById("eli10-text").value.trim();
  const output = document.getElementById("eli10-result");
  const btn    = document.getElementById("eli10-btn");

  if (!docId && !text) { toast("Select a document or paste text.", "error"); return; }

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Simplifying…`;
  output.classList.add("hidden");

  const body = docId ? { doc_id: docId } : { text };
  try {
    const res = await apiFetch("/api/explain/eli10", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    output.textContent = res.simplified;
    output.classList.remove("hidden");
    document.getElementById("eli10-word-count").textContent =
      `Original: ${res.original_length} words`;
    toast("Explanation ready!", "success");
  } catch (e) {
    toast(e.message, "error");
  }

  btn.disabled = false;
  btn.innerHTML = `✨ Simplify`;
});

/* ═══════════════════════════════════════════════════════════════
   3. QUIZ GENERATOR
═══════════════════════════════════════════════════════════════ */

document.getElementById("quiz-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const docId   = document.getElementById("quiz-doc").value;
  const text    = document.getElementById("quiz-text").value.trim();
  const numQ    = parseInt(document.getElementById("quiz-num").value) || 5;
  const btn     = document.getElementById("quiz-btn");

  if (!docId && !text) { toast("Select a document or paste text.", "error"); return; }

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Generating…`;
  document.getElementById("quiz-results").innerHTML = "";
  document.getElementById("flashcard-results").innerHTML = "";
  state.quizAnswered.clear();

  const body = { num_questions: numQ, ...(docId ? { doc_id: docId } : { text }) };
  try {
    const res = await apiFetch("/api/quiz/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    renderQuiz(res.questions);
    renderFlashcards(res.flashcards);
    toast(`Generated ${res.questions.length} questions & ${res.flashcards.length} flashcards!`, "success");
  } catch (e) {
    toast(e.message, "error");
  }

  btn.disabled = false;
  btn.innerHTML = `🎯 Generate Quiz`;
});

function renderQuiz(questions) {
  const container = document.getElementById("quiz-results");
  if (!questions.length) { container.innerHTML = `<div class="empty-state"><p>No questions generated.</p></div>`; return; }

  document.getElementById("quiz-score-section").style.display = "block";
  document.getElementById("quiz-total").textContent = questions.length;
  document.getElementById("quiz-correct").textContent = "0";

  container.innerHTML = questions.map((q, i) => `
    <div class="quiz-question" id="qq-${i}">
      <h4>${i + 1}. ${escHtml(q.question)}</h4>
      <div class="quiz-options">
        ${q.options.map(opt => `
          <div class="quiz-option" onclick="checkAnswer(${i}, '${opt.label}', '${q.answer}', '${escAttr(q.explanation)}')" data-idx="${i}" data-label="${opt.label}">
            <span class="option-label">${opt.label}</span>
            <span>${escHtml(opt.text)}</span>
          </div>`).join("")}
      </div>
      <div class="quiz-explanation" id="qexp-${i}">${escHtml(q.explanation)}</div>
    </div>`).join("");
}

function checkAnswer(qIdx, chosen, correct, explanation) {
  if (state.quizAnswered.has(qIdx)) return;
  state.quizAnswered.add(qIdx);

  document.querySelectorAll(`[data-idx="${qIdx}"]`).forEach(opt => {
    if (opt.dataset.label === correct) opt.classList.add("correct");
    else if (opt.dataset.label === chosen) opt.classList.add("wrong");
    opt.style.cursor = "default";
  });
  document.getElementById(`qexp-${qIdx}`).style.display = "block";

  // Update score
  const correctCount = [...state.quizAnswered].filter(idx => {
    const el = document.querySelector(`[data-idx="${idx}"].correct`);
    return el && el.querySelector(`[data-label]`) === null
      ? document.querySelector(`[data-idx="${idx}"][data-label="${correct}"].correct`) !== null
      : el !== null;
  }).length;

  const scoreEl = document.getElementById("quiz-correct");
  if (chosen === correct) scoreEl.textContent = parseInt(scoreEl.textContent) + 1;
}

function renderFlashcards(cards) {
  const container = document.getElementById("flashcard-results");
  if (!cards.length) { container.innerHTML = ""; return; }

  container.innerHTML = `
    <h3 class="card-title" style="margin-top:24px">🃏 Flashcards <span class="badge">${cards.length}</span></h3>
    <div class="grid-2">
      ${cards.map((c, i) => `
        <div>
          <div class="flashcard" id="fc-${i}" onclick="this.classList.toggle('flipped')">
            <div class="flashcard-inner">
              <div class="flashcard-front"><span>${escHtml(c.front)}</span></div>
              <div class="flashcard-back"><span>${escHtml(c.back)}</span></div>
            </div>
          </div>
          <div class="flashcard-hint">Click to flip</div>
        </div>`).join("")}
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════
   4. REVISION PLANNER
═══════════════════════════════════════════════════════════════ */

document.getElementById("planner-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const examDate  = document.getElementById("exam-date").value;
  const topicsRaw = document.getElementById("topics-input").value.trim();
  const hours     = parseFloat(document.getElementById("daily-hours").value) || 2;
  const btn       = document.getElementById("planner-btn");

  if (!examDate) { toast("Please select an exam date.", "error"); return; }
  if (!topicsRaw) { toast("Please enter at least one topic.", "error"); return; }

  const topics = topicsRaw.split("\n").map(t => t.trim()).filter(Boolean);
  if (!topics.length) { toast("No valid topics found.", "error"); return; }

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Planning…`;
  document.getElementById("plan-output").innerHTML = "";

  try {
    const res = await apiFetch("/api/planner/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ exam_date: examDate, topics, daily_hours: hours }),
    });
    renderPlan(res);
    toast(`${res.total_days}-day plan created!`, "success");
  } catch (e) {
    toast(e.message, "error");
  }

  btn.disabled = false;
  btn.innerHTML = `📅 Generate Plan`;
});

function renderPlan(plan) {
  const container = document.getElementById("plan-output");
  container.innerHTML = `
    <div class="card" style="margin-bottom:0">
      <div style="padding:14px 16px; background:var(--bg3); border:1px solid var(--border); border-radius:8px; margin-bottom:20px; font-size:14px;">
        ${escHtml(plan.message)}
      </div>
      ${plan.daily_plan.map(day => {
        const d = new Date(day.date + "T00:00:00");
        const dayNum = d.getDate();
        const dayLabel = d.toLocaleDateString("en", { weekday: "short" });
        const month = d.toLocaleDateString("en", { month: "short" });
        const isRevision = day.topics.some(t => t.includes("Revision"));
        return `
          <div class="plan-day">
            <div class="plan-date">
              <div class="day-num">${dayNum}</div>
              <div class="day-label">${dayLabel} ${month}</div>
              <div style="font-size:11px;color:var(--muted);margin-top:2px">${day.hours}h</div>
            </div>
            <div class="plan-topics">
              ${day.topics.map(t => `<span class="plan-topic-tag ${isRevision ? 'revision' : ''}">${escHtml(t)}</span>`).join("")}
            </div>
          </div>`;
      }).join("")}
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════
   5. CHATBOT
═══════════════════════════════════════════════════════════════ */

function appendMessage(role, content, time) {
  const msgs = document.getElementById("chat-messages");
  const t = time || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="msg-avatar">${role === "user" ? "🧑‍🎓" : "🤖"}</div>
    <div>
      <div class="msg-bubble">${escHtml(content)}</div>
      <div class="msg-time">${t}</div>
    </div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

document.getElementById("chat-send-btn")?.addEventListener("click", sendChat);
document.getElementById("chat-input")?.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); }
});

async function sendChat() {
  const inputEl = document.getElementById("chat-input");
  const docId   = document.getElementById("chat-doc").value;
  const question = inputEl.value.trim();
  if (!question) return;

  appendMessage("user", question);
  state.chatHistory.push({ role: "user", content: question });
  inputEl.value = "";

  const sendBtn = document.getElementById("chat-send-btn");
  sendBtn.disabled = true;

  // Typing indicator
  const typing = document.createElement("div");
  typing.className = "msg assistant";
  typing.id = "typing-indicator";
  typing.innerHTML = `<div class="msg-avatar">🤖</div><div class="msg-bubble"><span class="spinner"></span></div>`;
  document.getElementById("chat-messages").appendChild(typing);
  document.getElementById("chat-messages").scrollTop = 99999;

  try {
    const res = await apiFetch("/api/chat/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doc_id: docId || undefined,
        history: state.chatHistory.slice(-10),
        question,
      }),
    });
    document.getElementById("typing-indicator")?.remove();
    appendMessage("assistant", res.answer);
    state.chatHistory.push({ role: "assistant", content: res.answer });
  } catch (e) {
    document.getElementById("typing-indicator")?.remove();
    appendMessage("assistant", `❌ Error: ${e.message}`);
  }

  sendBtn.disabled = false;
  inputEl.focus();
}

document.getElementById("chat-clear-btn")?.addEventListener("click", () => {
  state.chatHistory = [];
  document.getElementById("chat-messages").innerHTML = `
    <div class="msg assistant">
      <div class="msg-avatar">🤖</div>
      <div>
        <div class="msg-bubble">Hi! I'm your AI Study Buddy 🎓 Upload a document and ask me anything about it. I'm here to help you understand tough concepts!</div>
        <div class="msg-time">Now</div>
      </div>
    </div>`;
});

/* ── Utility ─────────────────────────────────────────────────── */
function escHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function escAttr(s) {
  return String(s).replace(/'/g, "\\'").replace(/"/g, '\\"');
}

/* ── Init ─────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  // Set min date for exam date picker to tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const examDateInput = document.getElementById("exam-date");
  if (examDateInput) examDateInput.min = tomorrow.toISOString().split("T")[0];

  loadDocuments();
  navigate("tab-documents");
});
