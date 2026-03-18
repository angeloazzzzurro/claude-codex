const dialogoEl      = document.getElementById("dialogo");
const ragEl          = document.getElementById("ragionamento");
const opzioniEl      = document.getElementById("opzioni");
const statusDialogo  = document.getElementById("statusDialogo");
const statusRag      = document.getElementById("statusRag");
const statusOpzioni  = document.getElementById("statusOpzioni");
const btnSimula      = document.getElementById("btnSimula");
const btnReset       = document.getElementById("btnReset");
const scenarioSelect = document.getElementById("scenarioSelect");
const minRateInput   = document.getElementById("minRate");
const userPrompt     = document.getElementById("userPrompt");
const btnInvia       = document.getElementById("btnInvia");

// Scenari: usati per "Avvia simulazione" → genera una domanda predefinita verso live AI
const scenari = [
  { id: "prodotto-ux",       titolo: "Prodotto / UX",           domanda: "come migliorare l'esperienza utente nell'onboarding" },
  { id: "scalabilita",       titolo: "Scalabilità / Operazioni", domanda: "come scalare le operazioni riducendo i costi marginali" },
  { id: "marketing-gtm",     titolo: "Marketing / Go-to-market", domanda: "come lanciare una campagna di acquisizione efficace" },
  { id: "tech-arch",         titolo: "Tecnologia / Architettura", domanda: "come migliorare l'architettura tecnica riducendo il debito" },
  { id: "vendite-business",  titolo: "Vendite / Business",       domanda: "come aumentare le vendite e ottimizzare il pricing" },
];

function populateScenarioSelect() {
  scenarioSelect.innerHTML = "";
  const opt0 = document.createElement("option");
  opt0.value = "random";
  opt0.textContent = "Random";
  scenarioSelect.appendChild(opt0);
  scenari.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = s.titolo;
    scenarioSelect.appendChild(opt);
  });
}

function getSelectedDomanda() {
  const v = scenarioSelect.value;
  if (v === "random") {
    return scenari[Math.floor(Math.random() * scenari.length)].domanda;
  }
  return (scenari.find((s) => s.id === v) || scenari[0]).domanda;
}

// ---- UI helpers ----

let abortController = null;

function resetUI() {
  if (abortController) { abortController.abort(); abortController = null; }
  dialogoEl.innerHTML   = "";
  ragEl.innerHTML       = "";
  opzioniEl.innerHTML   = "";
  setStatus("dialogo",     "Pronto");
  setStatus("ragionamento","In attesa");
  setStatus("opzioni",     "In attesa");
  btnSimula.disabled = false;
  btnInvia.disabled  = false;
}

function setStatus(panel, text) {
  if (panel === "dialogo")      statusDialogo.textContent = text;
  if (panel === "ragionamento") statusRag.textContent     = text;
  if (panel === "opzioni")      statusOpzioni.textContent = text;
}

function addBubbleStatic(container, who, text) {
  const wrap = document.createElement("div");
  wrap.className = `bubble ${who.toLowerCase()}`;
  const nameEl = document.createElement("div");
  nameEl.className = "who";
  nameEl.textContent = who;
  const textEl = document.createElement("div");
  textEl.className = "text";
  textEl.textContent = text;
  wrap.appendChild(nameEl);
  wrap.appendChild(textEl);
  container.appendChild(wrap);
  container.scrollTop = container.scrollHeight;
}

// Bubble attive durante lo streaming
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
  activeBubbles[who] = { textEl, text: "" };
}

function appendToken(who, token) {
  const b = activeBubbles[who];
  if (!b) return;
  b.text += token;
  b.textEl.textContent = b.text;
  b.textEl.innerHTML += '<span class="cursor">▍</span>';
  b.textEl.parentElement.parentElement.scrollTop = 99999;
}

function endBubble(who) {
  const b = activeBubbles[who];
  if (!b) return;
  b.textEl.textContent = b.text;
  delete activeBubbles[who];
}

function addCard(op) {
  const card = document.createElement("div");
  card.className = "card";
  const h3 = document.createElement("h3");
  h3.textContent = op.titolo;
  const p = document.createElement("p");
  p.textContent = op.testo;
  const rate = document.createElement("div");
  rate.className = "rate";
  rate.textContent = `Tasso di successo: ${op.rate}%`;
  card.appendChild(h3);
  card.appendChild(p);
  card.appendChild(rate);
  opzioniEl.appendChild(card);
}

function addMsgCard(text) {
  const card = document.createElement("div");
  card.className = "card";
  const p = document.createElement("p");
  p.textContent = text;
  card.appendChild(p);
  opzioniEl.appendChild(card);
}

function addErrorCard(msg) {
  const card = document.createElement("div");
  card.className = "card error";
  const p = document.createElement("p");
  p.textContent = "Errore: " + msg;
  card.appendChild(p);
  opzioniEl.appendChild(card);
}

// ---- Live AI call ----

const MAX_QUESTION_LEN = 2000;

async function runLive(question) {
  if (question.length > MAX_QUESTION_LEN) {
    addErrorCard(`Domanda troppo lunga (max ${MAX_QUESTION_LEN} caratteri)`);
    return;
  }

  const minRate = Math.max(0, Math.min(100, parseInt(minRateInput.value, 10) || 0));

  resetUI();
  addBubbleStatic(dialogoEl, "Utente", question);
  setStatus("dialogo", "In corso");
  btnSimula.disabled = true;
  btnInvia.disabled  = true;

  abortController = new AbortController();

  try {
    const res = await fetch("/api/live", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, minRate }),
      signal: abortController.signal,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: "Errore server" }));
      setStatus("dialogo", "Errore");
      addErrorCard(err.error || "Errore server");
      return;
    }

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer    = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        let evt;
        try { evt = JSON.parse(line.slice(6)); } catch { continue; }

        switch (evt.type) {
          case "bubble_start": {
            const cont = evt.panel === "dialogo" ? dialogoEl : ragEl;
            if (evt.panel === "ragionamento") setStatus("ragionamento", "In corso");
            startBubble(cont, evt.who);
            break;
          }
          case "token":
            appendToken(evt.who, evt.text);
            break;
          case "bubble_end":
            endBubble(evt.who);
            if (evt.panel === "dialogo")      setStatus("dialogo",      "Completo");
            if (evt.panel === "ragionamento") setStatus("ragionamento", "Completo");
            break;
          case "phase_opzioni":
            setStatus("opzioni", "In corso");
            break;
          case "options":
            if (Array.isArray(evt.options)) {
              const filtered = evt.options
                .filter((o) => o.rate >= minRate)
                .sort((a, b) => b.rate - a.rate)
                .slice(0, 2);
              if (filtered.length === 0) {
                addMsgCard("Nessuna opzione supera il tasso minimo. Abbassa la soglia e riprova.");
              } else {
                if (filtered.length === 1 && evt.options.length > 1) {
                  addMsgCard("Solo una opzione supera il tasso minimo. Aggiungo quella migliore sotto soglia.");
                  const fallback = evt.options
                    .filter((o) => o.rate < minRate)
                    .sort((a, b) => b.rate - a.rate)[0];
                  if (fallback) filtered.push(fallback);
                }
                filtered.forEach(addCard);
              }
            }
            setStatus("opzioni", "Completo");
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
    btnSimula.disabled = false;
    btnInvia.disabled  = false;
    abortController = null;
  }
}

// ---- Event handlers ----

btnSimula.addEventListener("click", () => {
  const domanda = getSelectedDomanda();
  userPrompt.value = "";
  runLive(domanda);
});

btnReset.addEventListener("click", resetUI);

btnInvia.addEventListener("click", () => {
  const text = userPrompt.value.trim();
  if (!text) return;
  userPrompt.value = "";
  userPrompt.focus();
  runLive(text);
});

userPrompt.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const text = userPrompt.value.trim();
    if (!text) return;
    userPrompt.value = "";
    userPrompt.focus();
    runLive(text);
  }
});

// ---- Init ----
populateScenarioSelect();
resetUI();
