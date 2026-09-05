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

let state = loadState();

function createId() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createConversation() {
  const now = Date.now();
  return {
    id: createId(),
    title: "新对话",
    createdAt: now,
    updatedAt: now,
    messages: [{ role: "bot", text: WELCOME_MESSAGE, sources: [] }],
  };
}

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved && Array.isArray(saved.conversations) && saved.conversations.length) {
      const activeId = saved.activeId || saved.conversations[0].id;
      return { conversations: saved.conversations, activeId };
    }
  } catch (error) {
    console.warn("读取本地会话记录失败：", error);
  }
  const first = createConversation();
  return { conversations: [first], activeId: first.id };
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function activeConversation() {
  return state.conversations.find((item) => item.id === state.activeId) || null;
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  const today = new Date();
  if (date.toDateString() === today.toDateString()) {
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  }
  return date.toLocaleDateString("zh-CN", { month: "numeric", day: "numeric" });
}

function titleFromQuestion(question) {
  const compact = question.replace(/\s+/g, " ").trim();
  return compact.length > 18 ? `${compact.slice(0, 18)}…` : compact;
}

function renderConversationList() {
  conversationListEl.replaceChildren();
  conversationCountEl.textContent = state.conversations.length;

  [...state.conversations]
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .forEach((conversation) => {
      const item = document.createElement("div");
      item.className = `conversation-item ${conversation.id === state.activeId ? "active" : ""}`;
      item.dataset.id = conversation.id;

      const button = document.createElement("button");
      button.className = "conversation-main";
      button.type = "button";
      button.dataset.action = "select";
      button.dataset.id = conversation.id;

      const title = document.createElement("strong");
      title.textContent = conversation.title;
      const time = document.createElement("span");
      time.textContent = formatTime(conversation.updatedAt);
      button.append(title, time);

      const actions = document.createElement("div");
      actions.className = "conversation-actions";
      actions.innerHTML = `
        <button type="button" title="重命名" aria-label="重命名" data-action="rename" data-id="${conversation.id}">✎</button>
        <button type="button" title="删除" aria-label="删除" data-action="delete" data-id="${conversation.id}">×</button>
      `;
      item.append(button, actions);
      conversationListEl.appendChild(item);
    });
}

function renderMessages() {
  const conversation = activeConversation();
  if (!conversation) return;
  conversationTitleEl.textContent = conversation.title;
  messagesEl.replaceChildren();

  conversation.messages.forEach((message) => {
    const wrapper = document.createElement("div");
    wrapper.className = `message-group ${message.role}`;

    const bubble = document.createElement("div");
    bubble.className = `msg ${message.role}`;
    bubble.textContent = message.text;
    wrapper.appendChild(bubble);

    if (message.role === "bot" && message.sources && message.sources.length) {
      const details = document.createElement("details");
      details.className = "sources";
      const summary = document.createElement("summary");
      summary.textContent = `参考来源（${message.sources.length}）`;
      details.appendChild(summary);
      const list = document.createElement("ol");
      message.sources.forEach((source) => {
        const li = document.createElement("li");
        li.textContent = source;
        list.appendChild(li);
      });
      details.appendChild(list);
      wrapper.appendChild(details);
    }
    messagesEl.appendChild(wrapper);
  });
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function render() {
  renderConversationList();
  renderMessages();
}

function touchConversation(conversation) {
  conversation.updatedAt = Date.now();
  saveState();
  renderConversationList();
}

function selectConversation(id) {
  if (!state.conversations.some((item) => item.id === id)) return;
  state.activeId = id;
  saveState();
  render();
  inputEl.focus();
}

function newConversation() {
  const conversation = createConversation();
  state.conversations.push(conversation);
  state.activeId = conversation.id;
  saveState();
  render();
  inputEl.focus();
}

function renameConversation(id = state.activeId) {
  const conversation = state.conversations.find((item) => item.id === id);
  if (!conversation) return;
  const title = window.prompt("请输入新的对话名称：", conversation.title);
  if (title === null) return;
  const trimmed = title.trim();
  if (!trimmed) return;
  conversation.title = trimmed.slice(0, 40);
  touchConversation(conversation);
  if (conversation.id === state.activeId) conversationTitleEl.textContent = conversation.title;
  renderConversationList();
}

function deleteConversation(id) {
  const conversation = state.conversations.find((item) => item.id === id);
  if (!conversation) return;
  if (state.conversations.length === 1) {
    window.alert("至少保留一个对话。可以新建对话后再删除当前对话。");
    return;
  }
  if (!window.confirm(`确定删除“${conversation.title}”吗？`)) return;
  state.conversations = state.conversations.filter((item) => item.id !== id);
  if (state.activeId === id) {
    state.activeId = [...state.conversations].sort((a, b) => b.updatedAt - a.updatedAt)[0].id;
  }
  saveState();
  render();
}

async function send() {
  const question = inputEl.value.trim();
  const conversation = activeConversation();
  if (!question || !conversation || sendBtn.disabled) return;

  const isFirstQuestion = conversation.messages.every((message) => message.role === "bot");
  conversation.messages.push({ role: "user", text: question, sources: [] });
  if (isFirstQuestion || conversation.title === "新对话") {
    conversation.title = titleFromQuestion(question);
  }
  touchConversation(conversation);
  renderMessages();
  inputEl.value = "";
  sendBtn.disabled = true;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: question }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    conversation.messages.push({
      role: "bot",
      text: data.answer || "（无回复）",
      sources: Array.isArray(data.sources) ? data.sources : [],
    });
  } catch (error) {
    conversation.messages.push({ role: "bot", text: `请求失败：${error.message}`, sources: [] });
  } finally {
    touchConversation(conversation);
    render();
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

conversationListEl.addEventListener("click", (event) => {
  const target = event.target.closest("button[data-action]");
  if (!target) return;
  const { action, id } = target.dataset;
  if (action === "select") selectConversation(id);
  if (action === "rename") renameConversation(id);
  if (action === "delete") deleteConversation(id);
});

newConversationBtn.addEventListener("click", newConversation);
renameConversationBtn.addEventListener("click", () => renameConversation());
sendBtn.addEventListener("click", send);
inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter") send();
});

render();
inputEl.focus();
