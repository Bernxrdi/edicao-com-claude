// Renderiza HTML em PNG com o Playwright que já está no cache do npx (sem npm install).
// Uso: PLAYWRIGHT_CORE=<pasta do playwright-core> node render.mjs <jobs.json>
// jobs.json: [{"html": "/abs/pagina.html", "png": "/abs/saida.png", "largura": 1280, "altura": 720}]
// Quem chama é o canal.py (comando thumbs), que acha o node e o playwright-core sozinho.

import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_CORE);
const jobs = JSON.parse(readFileSync(process.argv[2], "utf8"));

const browser = await chromium.launch();
try {
  for (const job of jobs) {
    const page = await browser.newPage({
      viewport: { width: job.largura, height: job.altura },
      deviceScaleFactor: 1,
    });
    await page.goto(pathToFileURL(job.html).href, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: job.png });
    await page.close();
    console.log(job.png);
  }
} finally {
  await browser.close();
}
