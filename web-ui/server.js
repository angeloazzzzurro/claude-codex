const express = require("express");
const Anthropic = require("@anthropic-ai/sdk");
const path = require("path");

const app = express();
app.use(express.json());
app.use(express.static(__dirname));

app.post("/api/live", async (req, res) => {
  const { question, apiKey } = req.body;
  if (!question || !question.trim()) {
    return res.status(400).json({ error: "question mancante" });
  }

  const key = apiKey || process.env.ANTHROPIC_API_KEY;
  if (!key) {
    return res.status(401).json({ error: "API key mancante" });
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  const send = (type, data = {}) => {
    res.write(`data: ${JSON.stringify({ type, ...data })}\n\n`);
  };

  try {
    const client = new Anthropic({ apiKey: key });

    // --- FASE 1: Claude risponde (dialogo) ---
    send("bubble_start", { who: "Claude", panel: "dialogo" });

    let claudeResponse = "";
    const claudeStream = client.messages.stream({
      model: "claude-sonnet-4-6",
      max_tokens: 350,
      system:
        "Sei Claude, un consulente strategico. Rispondi sempre in italiano con 2-3 frasi concise e dirette. Niente elenchi puntati.",
      messages: [{ role: "user", content: question }],
    });

    for await (const chunk of claudeStream) {
      if (
        chunk.type === "content_block_delta" &&
        chunk.delta.type === "text_delta"
      ) {
        claudeResponse += chunk.delta.text;
        send("token", { who: "Claude", panel: "dialogo", text: chunk.delta.text });
      }
    }
    send("bubble_end", { who: "Claude", panel: "dialogo" });

    // --- FASE 2: Codex risponde (ragionamento) ---
    send("bubble_start", { who: "Codex", panel: "ragionamento" });

    let codexResponse = "";
    const codexStream = client.messages.stream({
      model: "claude-sonnet-4-6",
      max_tokens: 350,
      system:
        "Sei Codex, un agente tecnico e pratico. Integra il punto di vista strategico con un approccio concreto ed esecutivo. Italiano, 2-3 frasi. Niente elenchi.",
      messages: [
        { role: "user", content: question },
        {
          role: "assistant",
          content: `[Claude, strategico]: ${claudeResponse}`,
        },
        {
          role: "user",
          content: "Aggiungi la tua prospettiva tecnica/operativa.",
        },
      ],
    });

    for await (const chunk of codexStream) {
      if (
        chunk.type === "content_block_delta" &&
        chunk.delta.type === "text_delta"
      ) {
        codexResponse += chunk.delta.text;
        send("token", { who: "Codex", panel: "ragionamento", text: chunk.delta.text });
      }
    }
    send("bubble_end", { who: "Codex", panel: "ragionamento" });

    // --- FASE 3: Genera opzioni finali ---
    send("phase_opzioni");

    const optMsg = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 700,
      system:
        'Sei un consulente che sintetizza una conversazione in esattamente 2 opzioni azionabili. Rispondi SOLO con JSON valido, nessun testo aggiuntivo, in questo formato:\n[{"titolo":"Opzione A: nome","testo":"descrizione concreta in una frase.","rate":82},{"titolo":"Opzione B: nome","testo":"descrizione concreta in una frase.","rate":71}]',
      messages: [
        {
          role: "user",
          content: `Domanda: ${question}\n\nClaude (strategico): ${claudeResponse}\n\nCodex (esecutivo): ${codexResponse}\n\nGenera 2 opzioni concrete con tasso di successo stimato tra 55 e 92.`,
        },
      ],
    });

    let options;
    try {
      const raw = optMsg.content[0].text.trim();
      // estrai il JSON anche se ci sono caratteri extra
      const match = raw.match(/\[[\s\S]*\]/);
      options = JSON.parse(match ? match[0] : raw);
    } catch {
      options = [
        { titolo: "Opzione A", testo: claudeResponse.slice(0, 120), rate: 75 },
        { titolo: "Opzione B", testo: codexResponse.slice(0, 120), rate: 68 },
      ];
    }

    send("options", { options });
    send("done");
  } catch (err) {
    send("error", { message: err.message });
  }

  res.end();
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Simulatore live su http://localhost:${PORT}`);
});
