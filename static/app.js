const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
const sourcesEl = document.getElementById("sources");

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + (role === "user" ? "user" : "bot");
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

async function send() {
  const q = inputEl.value.trim();
  if (!q) return;
  addMessage("user", q);
  inputEl.value = "";
  sendBtn.disabled = true;
  sourcesEl.classList.add("hidden");
  sourcesEl.innerHTML = "";
  try {
    const resp = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q }),
    });
    const data = await resp.json();
    addMessage("bot", data.answer || "（无回复）");
    if (data.sources && data.sources.length) {
      sourcesEl.classList.remove("hidden");
      sourcesEl.innerHTML =
        "<strong>参考来源：</strong><ol>" +
        data.sources.map((s) => "<li>" + escapeHtml(s) + "</li>").join("") +
        "</ol>";
    }
  } catch (e) {
    addMessage("bot", "请求失败：" + e);
  } finally {
    sendBtn.disabled = false;
  }
}

sendBtn.addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") send();
});

addMessage("bot", "您好，我是智能客服小助手，请问有什么可以帮您？");
