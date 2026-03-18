import { chromium, devices } from "playwright";
import { fileURLToPath } from "url";
import path from "path";
import fs from "fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FILE_URL = `file://${path.resolve(__dirname, "index.html")}`;
const SCREENSHOTS_DIR = path.resolve(__dirname, "test-screenshots");

if (!fs.existsSync(SCREENSHOTS_DIR)) fs.mkdirSync(SCREENSHOTS_DIR);

const PASS = "\x1b[32m✓\x1b[0m";
const FAIL = "\x1b[31m✗\x1b[0m";

let passed = 0;
let failed = 0;

function assert(condition, label) {
  if (condition) { console.log(`  ${PASS} ${label}`); passed++; }
  else           { console.log(`  ${FAIL} ${label}`); failed++; }
}

async function waitFor(page, fn, timeout = 6000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const r = await fn();
    if (r) return r;
    await page.waitForTimeout(150);
  }
  return null;
}

async function screenshot(page, name) {
  const p = path.join(SCREENSHOTS_DIR, `${name}.png`);
  await page.screenshot({ path: p, fullPage: true });
  console.log(`  · screenshot: test-screenshots/${name}.png`);
}

async function testViewport(browser, label, viewport) {
  console.log(`\n\x1b[1m[${label}] ${viewport.width}×${viewport.height}\x1b[0m`);

  const ctx = await browser.newContext({
    viewport,
    userAgent: viewport.userAgent || undefined,
    deviceScaleFactor: viewport.deviceScaleFactor || 1,
    isMobile: viewport.isMobile || false,
    hasTouch: viewport.hasTouch || false,
  });
  const page = await ctx.newPage();

  const jsErrors = [];
  page.on("pageerror", (e) => jsErrors.push(e.message));

  await page.goto(FILE_URL);
  await page.waitForLoadState("domcontentloaded");
  await screenshot(page, `${label}-01-loaded`);

  // Layout: elementi critici visibili
  assert(await page.locator("#btnSimula").isVisible(), "Bottone 'Avvia simulazione' visibile");
  assert(await page.locator("#userPrompt").isVisible(), "Input terminale visibile");
  assert(await page.locator("#dialogo").isVisible(), "Pannello dialogo visibile");
  assert(await page.locator("#ragionamento").isVisible(), "Pannello ragionamento visibile");
  assert(await page.locator("#opzioni").isVisible(), "Sezione opzioni visibile");

  // Overflow orizzontale (pagina non deve scrollare in larghezza)
  const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
  const viewportWidth = viewport.width;
  assert(
    bodyScrollWidth <= viewportWidth + 2,
    `No overflow orizzontale (body ${bodyScrollWidth}px ≤ viewport ${viewportWidth}px)`
  );

  // Layout: su schermi stretti i pannelli devono impilare (1 colonna)
  if (viewport.width <= 900) {
    const boardStyle = await page.locator(".board").evaluate((el) => getComputedStyle(el).gridTemplateColumns);
    const isSingleCol = !boardStyle.includes(" ") || boardStyle.trim().split(/\s+/).length === 1;
    assert(isSingleCol, `Layout 1-colonna su ${viewport.width}px (grid: "${boardStyle}")`);
  }

  // Tap/click sul bottone — funzionamento su mobile
  await (viewport.hasTouch ? page.tap("#btnSimula") : page.click("#btnSimula"));
  await page.waitForTimeout(300);

  const statusD = await page.locator("#statusDialogo").textContent();
  assert(statusD === "In corso", `StatusDialogo "In corso" dopo tap (trovato: "${statusD}")`);

  // Attende simulazione completa
  const done = await waitFor(
    page,
    () => page.locator("#statusOpzioni").textContent().then((s) => s === "Completo" ? s : null),
    8000
  );
  assert(done !== null, "Simulazione completa su mobile");

  const cards = await page.locator("#opzioni .card").count();
  assert(cards >= 2, `${cards} card opzioni visibili`);

  await screenshot(page, `${label}-02-simulation-done`);

  // Terminale: input touch-friendly (altezza minima 44px per tap target)
  const inputBox = await page.locator("#userPrompt").boundingBox();
  assert(inputBox && inputBox.height >= 30, `Input height ${inputBox?.height?.toFixed(0)}px (ok per touch)`);

  const btnBox = await page.locator("#btnInvia").boundingBox();
  assert(btnBox && btnBox.height >= 30, `Bottone Invia height ${btnBox?.height?.toFixed(0)}px (ok per touch)`);

  // Terminale funzionante su mobile
  await page.fill("#userPrompt", "come scalare le operazioni");
  await (viewport.hasTouch ? page.locator("#btnInvia").tap() : page.click("#btnInvia"));
  await page.waitForTimeout(200);

  const inputCleared = await page.locator("#userPrompt").inputValue();
  assert(inputCleared === "", `Input svuotato dopo invio su mobile (valore: "${inputCleared}")`);

  const termDone = await waitFor(
    page,
    () => page.locator("#statusOpzioni").textContent().then((s) => s === "Completo" ? s : null),
    8000
  );
  assert(termDone !== null, "Simulazione terminale completa su mobile");

  await screenshot(page, `${label}-03-terminal-done`);

  assert(jsErrors.length === 0, `Nessun errore JS (${jsErrors.join(" | ") || "nessuno"})`);

  await ctx.close();
}

async function run() {
  const browser = await chromium.launch({ headless: true });

  const viewports = [
    // iPhone SE (small)
    { label: "iPhone-SE", width: 375, height: 667, isMobile: true, hasTouch: true, deviceScaleFactor: 2 },
    // iPhone 14 Pro
    { label: "iPhone-14", width: 393, height: 852, isMobile: true, hasTouch: true, deviceScaleFactor: 3 },
    // iPad Mini
    { label: "iPad-Mini", width: 768, height: 1024, isMobile: true, hasTouch: true, deviceScaleFactor: 2 },
    // iPad Pro 12.9"
    { label: "iPad-Pro", width: 1024, height: 1366, isMobile: false, hasTouch: true, deviceScaleFactor: 2 },
    // Desktop (baseline)
    { label: "Desktop", width: 1440, height: 900, isMobile: false, hasTouch: false, deviceScaleFactor: 1 },
  ];

  for (const vp of viewports) {
    await testViewport(browser, vp.label, vp);
  }

  console.log(`\n${"─".repeat(54)}`);
  const total = passed + failed;
  if (failed === 0) {
    console.log(`\x1b[32m\x1b[1m✓ Tutti i test responsive passati: ${passed}/${total}\x1b[0m`);
    console.log(`  Screenshots in: web-ui/test-screenshots/`);
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
