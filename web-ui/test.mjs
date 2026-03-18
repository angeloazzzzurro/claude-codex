import { chromium } from "playwright";
import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FILE_URL = `file://${path.resolve(__dirname, "index.html")}`;

const PASS = "\x1b[32m✓\x1b[0m";
const FAIL = "\x1b[31m✗\x1b[0m";
const INFO = "\x1b[36m·\x1b[0m";

let passed = 0;
let failed = 0;

function assert(condition, label) {
  if (condition) {
    console.log(`  ${PASS} ${label}`);
    passed++;
  } else {
    console.log(`  ${FAIL} ${label}`);
    failed++;
  }
}

async function waitFor(page, fn, timeout = 5000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const result = await fn();
    if (result) return result;
    await page.waitForTimeout(100);
  }
  return null;
}

async function bubbleCount(page, container) {
  return page.locator(`#${container} .bubble`).count();
}

async function cardCount(page) {
  return page.locator("#opzioni .card").count();
}

async function statusText(page, id) {
  return page.locator(`#${id}`).textContent();
}

async function run() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Cattura errori JS
  const jsErrors = [];
  page.on("pageerror", (e) => jsErrors.push(e.message));
  page.on("console", (msg) => {
    if (msg.type() === "error") jsErrors.push(msg.text());
  });

  await page.goto(FILE_URL);
  await page.waitForLoadState("domcontentloaded");

  // ─── SUITE 1: Caricamento pagina ────────────────────────────────────────────
  console.log("\n\x1b[1m[1] Caricamento pagina\x1b[0m");

  assert(jsErrors.length === 0, `Nessun errore JS al caricamento (trovati: ${jsErrors.join(", ") || "nessuno"})`);
  assert(await page.locator("#btnSimula").isVisible(), "Bottone 'Avvia simulazione' visibile");
  assert(await page.locator("#btnReset").isVisible(), "Bottone 'Reset' visibile");
  assert(await page.locator("#userPrompt").isVisible(), "Input terminale visibile");
  assert(await page.locator("#btnInvia").isVisible(), "Bottone 'Invia' visibile");
  assert(await page.locator("#scenarioSelect").isVisible(), "Select scenario visibile");

  const optCount = await page.locator("#scenarioSelect option").count();
  assert(optCount === 6, `Select ha 6 opzioni (Random + 5 scenari), trovate: ${optCount}`);

  const statusD = await statusText(page, "statusDialogo");
  assert(statusD === "Pronto", `StatusDialogo iniziale = "Pronto" (trovato: "${statusD}")`);

  // ─── SUITE 2: Bottone Avvia Simulazione ─────────────────────────────────────
  console.log("\n\x1b[1m[2] Bottone 'Avvia simulazione'\x1b[0m");

  await page.click("#btnSimula");
  await page.waitForTimeout(200);

  const statusAfterClick = await statusText(page, "statusDialogo");
  assert(statusAfterClick === "In corso", `StatusDialogo = "In corso" subito dopo click (trovato: "${statusAfterClick}")`);

  // Primo bubble dialogo appare subito (delay=0)
  const firstBubble = await waitFor(page, () => bubbleCount(page, "dialogo").then((n) => n >= 1), 2000);
  assert(firstBubble !== null, "Primo bubble dialogo appare entro 2s");

  // Tutti i bubble dialogo (3) appaiono entro 3s
  const allDialogo = await waitFor(page, () => bubbleCount(page, "dialogo").then((n) => n >= 3), 3000);
  assert(allDialogo !== null, "Tutti e 3 i bubble dialogo appaiono entro 3s");

  // Status dialogo → Completo
  const statusDCompleto = await waitFor(
    page,
    () => statusText(page, "statusDialogo").then((s) => s === "Completo" ? s : null),
    3500
  );
  assert(statusDCompleto !== null, "StatusDialogo diventa 'Completo'");

  // Bubble ragionamento appaiono
  const ragBubbles = await waitFor(page, () => bubbleCount(page, "ragionamento").then((n) => n >= 2), 4000);
  assert(ragBubbles !== null, "Bubble ragionamento (min 2) appaiono");

  const statusRagCompleto = await waitFor(
    page,
    () => statusText(page, "statusRag").then((s) => s === "Completo" ? s : null),
    5000
  );
  assert(statusRagCompleto !== null, "StatusRag diventa 'Completo'");

  // Opzioni appaiono
  const cards = await waitFor(page, () => cardCount(page).then((n) => n >= 2), 6000);
  assert(cards !== null, "Almeno 2 card opzioni appaiono");

  const statusOptCompleto = await waitFor(
    page,
    () => statusText(page, "statusOpzioni").then((s) => s === "Completo" ? s : null),
    6500
  );
  assert(statusOptCompleto !== null, "StatusOpzioni diventa 'Completo'");

  // Verifica che i rate siano visibili
  const rateTexts = await page.locator(".rate").allTextContents();
  const ratesOk = rateTexts.length >= 2 && rateTexts.every((t) => t.includes("Tasso di successo:"));
  assert(ratesOk, `Rate success visibili nelle card: [${rateTexts.join(" | ")}]`);

  // ─── SUITE 3: Bottone Reset ──────────────────────────────────────────────────
  console.log("\n\x1b[1m[3] Bottone Reset\x1b[0m");

  await page.click("#btnReset");
  await page.waitForTimeout(200);

  const dialogoBubblesAfterReset = await bubbleCount(page, "dialogo");
  assert(dialogoBubblesAfterReset === 0, `Dialogo svuotato dopo Reset (bubble rimasti: ${dialogoBubblesAfterReset})`);

  const ragBubblesAfterReset = await bubbleCount(page, "ragionamento");
  assert(ragBubblesAfterReset === 0, `Ragionamento svuotato dopo Reset (bubble rimasti: ${ragBubblesAfterReset})`);

  const cardsAfterReset = await cardCount(page);
  assert(cardsAfterReset === 0, `Opzioni svuotate dopo Reset (card rimaste: ${cardsAfterReset})`);

  const statusAfterReset = await statusText(page, "statusDialogo");
  assert(statusAfterReset === "Pronto", `StatusDialogo torna "Pronto" dopo Reset (trovato: "${statusAfterReset}")`);

  // ─── SUITE 4: Terminale — input e invio ─────────────────────────────────────
  console.log("\n\x1b[1m[4] Terminale (input utente)\x1b[0m");

  await page.fill("#userPrompt", "voglio migliorare la ux del prodotto");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(100);

  // Input deve essere stato svuotato
  const inputValue = await page.locator("#userPrompt").inputValue();
  assert(inputValue === "", `Input terminale svuotato dopo invio (valore: "${inputValue}")`);

  // Bubble "Utente" presente
  const utenteBubbles = await page.locator("#dialogo .bubble:has(.who)").count();
  assert(utenteBubbles >= 1, `Bubble Utente presente nel dialogo (count: ${utenteBubbles})`);

  // Bubble "Claude Ricevuto" presente
  const whoTexts = await page.locator("#dialogo .who").allTextContents();
  const hasRicevuto = await page.locator("#dialogo .text").evaluateAll((els) =>
    els.some((el) => el.textContent.includes("Ricevuto"))
  );
  assert(hasRicevuto, `Bubble "Ricevuto" di Claude presente dopo invio terminale`);

  // Scenario prodotto-ux rilevato da keyword "ux"
  const selectValue = await page.locator("#scenarioSelect").inputValue();
  assert(selectValue === "prodotto-ux", `Scenario rilevato correttamente come "prodotto-ux" (trovato: "${selectValue}")`);

  // Attende che la simulazione termini
  const terminalCardsOk = await waitFor(page, () => cardCount(page).then((n) => n >= 2), 7000);
  assert(terminalCardsOk !== null, "Simulazione da terminale completa con >= 2 card");

  const finalStatus = await waitFor(
    page,
    () => statusText(page, "statusOpzioni").then((s) => s === "Completo" ? s : null),
    7500
  );
  assert(finalStatus !== null, "StatusOpzioni 'Completo' dopo simulazione terminale");

  // ─── SUITE 5: Simulazione multipla (re-run senza blocco) ────────────────────
  console.log("\n\x1b[1m[5] Re-run: seconda simulazione senza reset manuale\x1b[0m");

  await page.click("#btnSimula");
  await page.waitForTimeout(300);

  const rerunDialogo = await waitFor(page, () => bubbleCount(page, "dialogo").then((n) => n >= 1), 2000);
  assert(rerunDialogo !== null, "Seconda simulazione parte subito (no blocco running)");

  const rerunFinal = await waitFor(
    page,
    () => statusText(page, "statusOpzioni").then((s) => s === "Completo" ? s : null),
    8000
  );
  assert(rerunFinal !== null, "Seconda simulazione completa correttamente");

  // ─── SUITE 6: Terminale durante simulazione in corso (race condition) ────────
  console.log("\n\x1b[1m[6] Race condition: terminale durante simulazione in corso\x1b[0m");

  await page.click("#btnSimula");
  await page.waitForTimeout(600); // simulazione a metà

  await page.fill("#userPrompt", "come scalare le operazioni");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(200);

  // La nuova simulazione deve aver preso il controllo
  const raceStatusD = await statusText(page, "statusDialogo");
  assert(
    raceStatusD === "In corso" || raceStatusD === "Completo",
    `Dopo race condition: statusDialogo è valido ("${raceStatusD}")`
  );

  // Scenario scalabilita rilevato
  const raceSelectValue = await page.locator("#scenarioSelect").inputValue();
  assert(
    raceSelectValue === "scalabilita",
    `Scenario "scalabilita" rilevato da keyword "scalare" (trovato: "${raceSelectValue}")`
  );

  // Simulazione completa correttamente
  const raceFinal = await waitFor(
    page,
    () => statusText(page, "statusOpzioni").then((s) => s === "Completo" ? s : null),
    8000
  );
  assert(raceFinal !== null, "Simulazione dopo race condition completa correttamente");

  // ─── SUITE 7: Tutti gli scenari ──────────────────────────────────────────────
  console.log("\n\x1b[1m[7] Tutti gli scenari (click selettivo)\x1b[0m");

  const scenarioIds = ["prodotto-ux", "scalabilita", "marketing-gtm", "tech-arch", "vendite-business"];

  for (const sid of scenarioIds) {
    await page.selectOption("#scenarioSelect", sid);
    await page.click("#btnSimula");

    const done = await waitFor(
      page,
      () => statusText(page, "statusOpzioni").then((s) => s === "Completo" ? s : null),
      8000
    );
    const cardsN = await cardCount(page);
    assert(done !== null && cardsN >= 1, `Scenario "${sid}": completato con ${cardsN} card`);
  }

  // ─── SUITE 8: Errori JS durante tutta la sessione ───────────────────────────
  console.log("\n\x1b[1m[8] Errori JS accumulati durante tutta la sessione\x1b[0m");
  assert(jsErrors.length === 0, `Nessun errore JS (${jsErrors.length} trovati: ${jsErrors.join(" | ") || "nessuno"})`);

  // ─── Riepilogo ───────────────────────────────────────────────────────────────
  console.log(`\n${"─".repeat(50)}`);
  const total = passed + failed;
  if (failed === 0) {
    console.log(`\x1b[32m\x1b[1m✓ Tutti i test passati: ${passed}/${total}\x1b[0m`);
  } else {
    console.log(`\x1b[31m\x1b[1m✗ ${failed} test falliti su ${total}\x1b[0m`);
  }

  await browser.close();
  process.exit(failed > 0 ? 1 : 0);
}

run().catch((err) => {
  console.error("\x1b[31m[FATAL]\x1b[0m", err.message);
  process.exit(1);
});
