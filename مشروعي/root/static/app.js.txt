const chatBox = document.getElementById("chat");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("chat-send");

function addBubble(text, who = "bot") {
  const div = document.createElement("div");
  div.className = `bubble ${who}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn.addEventListener("click", async () => {
  const msg = (inputEl.value || "").trim();
  if (!msg) return;
  addBubble(msg, "user");
  inputEl.value = "";
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    addBubble(data.reply, "bot");
  } catch {
    addBubble("عذرًا، حدث خطأ بسيط. حاول مرة أخرى.", "bot");
  }
});

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendBtn.click();
});
