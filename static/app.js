const STORAGE_KEY = "rag-customer-service-conversations-v1";
const WELCOME_MESSAGE = "您好，我是智能客服小助手，请问有什么可以帮您？";

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
const conversationListEl = document.getElementById("conversationList");
const conversationCountEl = document.getElementById("conversationCount");
const conversationTitleEl = document.getElementById("conversationTitle");
const newConversationBtn = document.getElementById("newConversation");
const renameConversationBtn = document.getElementById("renameConversation");
const exportTxtBtn = document.getElementById("exportTxt");
const exportJsonBtn = document.getElementById("exportJson");
const adminDialog = document.getElementById("adminDialog");
const adminTokenEl = document.getElementById("adminToken");
const knowledgeContentEl = document.getElementById("knowledgeContent");
const adminMessageEl = document.getElementById("adminMessage");

let state = loadState();
let searchTerm = "";

function createId() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function createConversation() {
  const now = Date.now();
  return { id: createId(), title: "新对话", createdAt: now, updatedAt: now, messages: [] };
}
function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved && Array.isArray(saved.conversations) && saved.conversations.length) return { conversations: saved.conversations, activeId: saved.activeId || saved.conversations[0].id };
  } catch (error) { console.warn("读取本地会话记录失败：", error); }
  const first = createConversation();
  return { conversations: [first], activeId: first.id };
}
function saveState() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
function activeConversation() { return state.conversations.find((item) => item.id === state.activeId) || null; }
function formatTime(timestamp) {
  const date = new Date(timestamp); const today = new Date();
  if (date.toDateString() === today.toDateString()) return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  return date.toLocaleDateString("zh-CN", { month: "numeric", day: "numeric" });
}
function titleFromQuestion(question) { const compact = question.replace(/\s+/g, " ").trim(); return compact.length > 18 ? `${compact.slice(0, 18)}…` : compact; }

function renderConversationList() {
  conversationListEl.replaceChildren(); conversationCountEl.textContent = state.conversations.length;
  [...state.conversations].filter((conversation) => !searchTerm || conversation.title.toLowerCase().includes(searchTerm.toLowerCase())).sort((a, b) => b.updatedAt - a.updatedAt).forEach((conversation) => {
    const item = document.createElement("div"); item.className = `conversation-item ${conversation.id === state.activeId ? "active" : ""}`;
    const button = document.createElement("button"); button.className = "conversation-main"; button.type = "button"; button.dataset.action = "select"; button.dataset.id = conversation.id;
    const title = document.createElement("strong"); title.textContent = conversation.title;
    const time = document.createElement("span"); time.textContent = formatTime(conversation.updatedAt); button.append(title, time);
    const actions = document.createElement("div"); actions.className = "conversation-actions";
    actions.innerHTML = `<button type="button" title="重命名" aria-label="重命名" data-action="rename" data-id="${conversation.id}">✎</button><button type="button" title="删除" aria-label="删除" data-action="delete" data-id="${conversation.id}">×</button>`;
    item.append(button, actions); conversationListEl.appendChild(item);
  });
}

function renderMessages() {
  const conversation = activeConversation(); if (!conversation) return;
  conversationTitleEl.textContent = conversation.title; messagesEl.replaceChildren();
  if (!conversation.messages.length) {
    messagesEl.innerHTML = `<div class="empty-state"><div class="empty-mark">R</div><h2>今天想了解什么？</h2><p>从知识库中检索信息，获得更准确的客服回答。</p><div class="quick-prompts"><button class="quick-prompt" type="button" data-prompt="怎么申请退款？">怎么申请退款？</button><button class="quick-prompt" type="button" data-prompt="配送通常需要多久？">配送通常需要多久？</button><button class="quick-prompt" type="button" data-prompt="如何保护账户安全？">如何保护账户安全？</button><button class="quick-prompt" type="button" data-prompt="有哪些支付方式？">有哪些支付方式？</button></div></div>`;
    return;
  }
  conversation.messages.forEach((message) => {
    const wrapper = document.createElement("div"); wrapper.className = `message-group ${message.role}`;
    const bubble = document.createElement("div"); bubble.className = `msg ${message.role}`; bubble.textContent = message.text; wrapper.appendChild(bubble);
    if (message.role === "bot" && message.sources && message.sources.length) {
      const details = document.createElement("details"); details.className = "sources";
      const summary = document.createElement("summary"); summary.textContent = `参考来源（${message.sources.length}）`; details.appendChild(summary);
      const list = document.createElement("ol"); message.sources.forEach((source) => { const li = document.createElement("li"); li.textContent = source; list.appendChild(li); });
      details.appendChild(list); wrapper.appendChild(details);
    }
    messagesEl.appendChild(wrapper);
  });
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
function render() { renderConversationList(); renderMessages(); }
function sendPrompt(prompt) { inputEl.value = prompt; send(); }

function touchConversation(conversation) { conversation.updatedAt = Date.now(); saveState(); renderConversationList(); }
function selectConversation(id) { if (!state.conversations.some((item) => item.id === id)) return; state.activeId = id; saveState(); render(); inputEl.focus(); }
function newConversation() { const conversation = createConversation(); state.conversations.push(conversation); state.activeId = conversation.id; saveState(); render(); inputEl.focus(); }
function renameConversation(id = state.activeId) {
  const conversation = state.conversations.find((item) => item.id === id); if (!conversation) return;
  const title = window.prompt("请输入新的对话名称：", conversation.title); if (title === null || !title.trim()) return;
  conversation.title = title.trim().slice(0, 40); touchConversation(conversation); render();
}
function deleteConversation(id) {
  const conversation = state.conversations.find((item) => item.id === id); if (!conversation) return;
  if (state.conversations.length === 1) return window.alert("至少保留一个对话。可以新建对话后再删除当前对话。");
  if (!window.confirm(`确定删除“${conversation.title}”吗？`)) return;
  state.conversations = state.conversations.filter((item) => item.id !== id);
  if (state.activeId === id) state.activeId = [...state.conversations].sort((a, b) => b.updatedAt - a.updatedAt)[0].id;
  saveState(); render();
}

function addBotMessage(conversation, text, sources = []) {
  const existing = conversation.messages[conversation.messages.length - 1];
  if (existing && existing.role === "bot" && existing.streaming) { existing.text += text; existing.sources = sources; }
  else conversation.messages.push({ role: "bot", text, sources, streaming: false });
}

async function send() {
  const question = inputEl.value.trim(); const conversation = activeConversation();
  if (!question || !conversation || sendBtn.disabled) return;
  const isFirstQuestion = conversation.messages.every((message) => message.role === "bot");
  conversation.messages.push({ role: "user", text: question, sources: [] });
  if (isFirstQuestion || conversation.title === "新对话") conversation.title = titleFromQuestion(question);
  touchConversation(conversation); renderMessages(); inputEl.value = ""; sendBtn.disabled = true;
  const botMessage = { role: "bot", text: "", sources: [], streaming: true }; conversation.messages.push(botMessage); renderMessages();
  try {
    const response = await fetch("/chat/stream", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: question }) });
    if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);
    const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
    while (true) {
      const { value, done } = await reader.read(); if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n"); buffer = events.pop();
      for (const raw of events) {
        const lines = raw.split("\n"); const eventName = lines.find((line) => line.startsWith("event:"))?.slice(6).trim(); const dataLine = lines.find((line) => line.startsWith("data:"));
        if (!dataLine) continue;
        const data = JSON.parse(dataLine.slice(5).trim());
        if (eventName === "sources") botMessage.sources = data.sources || [];
        if (eventName === "token") { botMessage.text += data.text || ""; renderMessages(); }
        if (eventName === "error") throw new Error(data.message || "流式请求失败");
      }
    }
    botMessage.streaming = false;
  } catch (error) {
    botMessage.text = botMessage.text || `请求失败：${error.message}`; botMessage.streaming = false;
  } finally {
    touchConversation(conversation); render(); sendBtn.disabled = false; inputEl.focus();
  }
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const link = document.createElement("a");
  link.href = url; link.download = filename; link.click(); URL.revokeObjectURL(url);
}
function exportConversation(format) {
  const conversation = activeConversation(); if (!conversation) return;
  const safeTitle = conversation.title.replace(/[\\/:*?"<>|]/g, "_").slice(0, 40) || "对话记录";
  if (format === "json") downloadFile(`${safeTitle}.json`, JSON.stringify(conversation, null, 2), "application/json;charset=utf-8");
  else {
    const text = [`# ${conversation.title}`, "", ...conversation.messages.map((message) => `${message.role === "user" ? "用户" : "客服"}：\n${message.text}${message.sources?.length ? `\n\n参考来源：\n${message.sources.map((source, i) => `${i + 1}. ${source}`).join("\n")}` : ""}\n`)].join("\n");
    downloadFile(`${safeTitle}.txt`, text, "text/plain;charset=utf-8");
  }
}

function adminMessage(text, isError = false) { adminMessageEl.textContent = text; adminMessageEl.className = `admin-message ${isError ? "error" : "success"}`; }
async function loadKnowledge() {
  adminMessage("正在读取…");
  try { const response = await fetch("/admin/knowledge-base", { headers: { "X-Admin-Token": adminTokenEl.value } }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "读取失败"); knowledgeContentEl.value = data.content; adminMessage("读取成功"); }
  catch (error) { adminMessage(error.message, true); }
}
async function saveKnowledge() {
  if (!knowledgeContentEl.value.trim()) return adminMessage("知识库内容不能为空", true);
  adminMessage("正在保存并重建索引…");
  try { const response = await fetch("/admin/knowledge-base", { method: "PUT", headers: { "Content-Type": "application/json", "X-Admin-Token": adminTokenEl.value }, body: JSON.stringify({ content: knowledgeContentEl.value }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "保存失败"); adminMessage(`${data.message}（${data.chunks} 个片段）`); }
  catch (error) { adminMessage(error.message, true); }
}

conversationListEl.addEventListener("click", (event) => { const target = event.target.closest("button[data-action]"); if (!target) return; const { action, id } = target.dataset; if (action === "select") selectConversation(id); if (action === "rename") renameConversation(id); if (action === "delete") deleteConversation(id); });
messagesEl.addEventListener("click", (event) => { const target = event.target.closest("button[data-prompt]"); if (target) sendPrompt(target.dataset.prompt); });
document.getElementById("conversationSearch").addEventListener("input", (event) => { searchTerm = event.target.value.trim(); renderConversationList(); });
document.getElementById("clearSearch").addEventListener("click", () => { searchTerm = ""; document.getElementById("conversationSearch").value = ""; renderConversationList(); });
document.addEventListener("keydown", (event) => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); newConversation(); } });
document.getElementById("railKnowledge").addEventListener("click", () => document.getElementById("openAdmin").click());
document.getElementById("railSettings").addEventListener("click", () => document.getElementById("openAdmin").click());
newConversationBtn.addEventListener("click", newConversation);
renameConversationBtn.addEventListener("click", () => renameConversation());
exportTxtBtn.addEventListener("click", () => exportConversation("txt"));
exportJsonBtn.addEventListener("click", () => exportConversation("json"));
document.getElementById("openAdmin").addEventListener("click", () => { adminDialog.showModal(); adminMessage(""); });
document.getElementById("closeAdmin").addEventListener("click", () => adminDialog.close());
document.getElementById("loadKnowledge").addEventListener("click", loadKnowledge);
document.getElementById("saveKnowledge").addEventListener("click", saveKnowledge);
sendBtn.addEventListener("click", send);
inputEl.addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); } });
inputEl.addEventListener("input", () => { inputEl.style.height = "auto"; inputEl.style.height = `${Math.min(inputEl.scrollHeight, 120)}px`; });
render(); inputEl.focus();
