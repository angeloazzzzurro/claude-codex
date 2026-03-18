const dialogoEl = document.getElementById("dialogo");
const ragEl = document.getElementById("ragionamento");
const opzioniEl = document.getElementById("opzioni");
const statusDialogo = document.getElementById("statusDialogo");
const statusRag = document.getElementById("statusRag");
const statusOpzioni = document.getElementById("statusOpzioni");
const btnReset = document.getElementById("btnReset");
const userPrompt = document.getElementById("userPrompt");
const btnInvia = document.getElementById("btnInvia");
const apiKeyInput = document.getElementById("apiKey");

// Carica API key salvata
if (apiKeyInput && localStorage.getItem("anthropic_key")) {
  apiKeyInput.value = localStorage.getItem("anthropic_key");
}

let abortController = null;

function resetUI() {
  if (abortController) {
    abortController.abort();
    abortController = null;
  }
  dialogoEl.innerHTML = "";
  ragEl.innerHTML = "";
  opzioniEl.innerHTML = "";
  setStatus("dialogo", "Pronto");
  setStatus("ragionamento", "In attesa");
  setStatus("opzioni", "In attesa");
}

function setStatus(panel, text) {
  if (panel === "dialogo") statusDialogo.textContent = text;
  else if (panel === "ragionamento") statusRag.textContent = text;
  else if (panel === "opzioni") statusOpzioni.textContent = text;
}

// Ogni bubble ha un div.text che viene aggiornato token per token
const activeBubbles = {};

function startBubble(container, who) {
  const wrap = document.createElement("div");
  wrap.className = `bubble ${who.toLowerCase()}`;

  const nameEl = document.createElement("div");
  nameEl.className = "who";
  nameEl.textContent = who;

  const textEl = document.createElement("div");
  textEl.className = "text";
  textEl.innerHTML = '<span class="cursor">▍</span>';

  wrap.appendChild(nameEl);
  wrap.appendChild(textEl);
  container.appendChild(wrap);
  container.scrollTop = container.scrollHeight;

  activeBubbles[who] = { wrap, textEl, text: "" };
}

function appendToken(who, token) {
  const b = activeBubbles[who];
  if (!b) return;
  b.text += token;
  b.textEl.textContent = b.text;
  b.textEl.innerHTML += '<span class="cursor">▍</span>';
  // scroll
  b.wrap.parentElement.scrollTop = b.wrap.parentElement.scrollHeight;
}

function endBubble(who) {
  const b = activeBubbles[who];
  if (!b) return;
  b.textEl.textContent = b.text;
  delete activeBubbles[who];
}

function addUserBubble(text) {
  const wrap = document.createElement("div");
  wrap.className = "bubble utente";
  const nameEl = document.createElement("div");
  nameEl.className = "who";
  nameEl.textContent = "Utente";
  const textEl = document.createElement("div");
  textEl.className = "text";
  textEl.textContent = text;
  wrap.appendChild(nameEl);
  wrap.appendChild(textEl);
  dialogoEl.appendChild(wrap);
}

function addCard(opzione) {
  const card = document.createElement("div");
  card.className = "card";

  const h3 = document.createElement("h3");
  h3.textContent = opzione.titolo;

  const p = document.createElement("p");
  p.textContent = opzione.testo;

  const rate = document.createElement("div");
  rate.className = "rate";
  rate.textContent = `Tasso di successo: ${opzione.rate}%`;

  card.appendChild(h3);
  card.appendChild(p);
  card.appendChild(rate);
  opzioniEl.appendChild(card);
}

function addErrorCard(message) {
  const card = document.createElement("div");
  card.className = "card error";
  const p = document.createElement("p");
  p.textContent = "Errore: " + message;
  card.appendChild(p);
  opzioniEl.appendChild(card);
}

async function handleUserPrompt() {
  const text = userPrompt.value.trim();
  if (!text) return;

  const apiKey = apiKeyInput ? apiKeyInput.value.trim() : "";
  if (apiKey) localStorage.setItem("anthropic_key", apiKey);

  resetUI();
  userPrompt.value = "";
  userPrompt.focus();

  addUserBubble(text);
  setStatus("dialogo", "In corso");
  btnInvia.disabled = true;

  abortController = new AbortController();

  try {
    const res = await fetch("/api/live", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text, apiKey }),
      signal: abortController.signal,
    });

    if (!res.ok) {
      const err = await res.json();
      setStatus("dialogo", "Errore");
      addErrorCard(err.error || "Errore server");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // ultima riga incompleta

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        let evt;
        try {
          evt = JSON.parse(line.slice(6));
        } catch {
          continue;
        }

        switch (evt.type) {
          case "bubble_start": {
            const container = evt.panel === "dialogo" ? dialogoEl : ragEl;
            if (evt.panel === "ragionamento") setStatus("ragionamento", "In corso");
            startBubble(container, evt.who);
            break;
          }
          case "token":
            appendToken(evt.who, evt.text);
            break;

          case "bubble_end":
            endBubble(evt.who);
            if (evt.panel === "dialogo") setStatus("dialogo", "Completo");
            else if (evt.panel === "ragionamento") setStatus("ragionamento", "Completo");
            break;

          case "phase_opzioni":
            setStatus("opzioni", "In corso");
            break;

          case "options":
            if (Array.isArray(evt.options)) {
              evt.options.forEach(addCard);
            }
            setStatus("opzioni", "Completo");
            break;

          case "done":
            break;

          case "error":
            addErrorCard(evt.message);
            setStatus("dialogo", "Errore");
            break;
        }
      }
    }
  } catch (err) {
    if (err.name !== "AbortError") {
      addErrorCard(err.message);
      setStatus("dialogo", "Errore");
    }
  } finally {
    btnInvia.disabled = false;
    abortController = null;
  }
}

btnReset.addEventListener("click", resetUI);
btnInvia.addEventListener("click", handleUserPrompt);
userPrompt.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleUserPrompt();
});

resetUI();
