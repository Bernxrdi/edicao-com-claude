// Render do motor próprio (11/10/2026): anda no tempo, chama window.seek(t) na página e manda
// cada quadro pro ffmpeg. Subquadros misturados dão o desfoque de movimento.
// Playwright do cache do npx (sem npm install), igual ao scripts/render.mjs do canal.
//
// Uso (da pasta do projeto do vídeo):
//   PLAYWRIGHT_CORE=<pasta do playwright-core> node render.mjs [opções]
//   --html index.html   página do filme (padrão: index.html)
//   --formato 9x16      9x16 (1080x1920) · 4x5 (1080x1350) · 1x1 (1080x1080) · 16x9 (1920x1080) · 16x9-4k (3840x2160, canal)
//   --fps 60 --sub 4    quadros por segundo e subquadros por quadro (sub 1 = sem desfoque)
//   --dur 15            duração em segundos (padrão: window.DUR da página)
//   --de 0 --ate 15     só um trecho (pra conferir o que mudou sem refazer tudo)
//   --stills 0.5,1,2.5  em vez do vídeo, um PNG por tempo (a folha de uma batida por quadro)
//   --stills beats      um PNG por batida do beats.json da pasta
//   --out out/silent.mp4
//   --alfa              fundo transparente: sai MOV ProRes 4444 pra colar por cima de vídeo (a página não pinta fundo)
// Saída: MP4 H.264 yuv420p CRF 16, sem som. O som entra depois (README, "Som").

import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { resolve, dirname } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_CORE);

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const FORMATOS = { '9x16': [1080, 1920], '4x5': [1080, 1350], '1x1': [1080, 1080], '16x9': [1920, 1080], '16x9-4k': [3840, 2160] };
const formato = arg('formato', '9x16');
const [W, H] = FORMATOS[formato] || (() => { throw new Error('formato: ' + Object.keys(FORMATOS)); })();
const FPS = Number(arg('fps', 60)), SUB = Number(arg('sub', 4));
const html = resolve(arg('html', 'index.html'));
const stills = arg('stills', null);
const ALFA = argv.includes('--alfa');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(html).href + '?render=1&formato=' + formato, { waitUntil: 'load' });
await page.evaluate(async () => { await document.fonts.ready; if (window.pronto) await window.pronto; });
const DUR = Number(arg('dur', 0)) || await page.evaluate(() => window.DUR || 10);

// Canvas: o quadro sai direto do canvas (mais rápido). Página em DOM: print da página.
const temCanvas = await page.evaluate(() => !!document.querySelector('canvas#c'));
const quadro = async (t, tipo = 'png') => {
  await page.evaluate((tt) => window.seek(tt), t);
  const o = { type: tipo, omitBackground: ALFA };
  return temCanvas ? page.locator('canvas#c').screenshot(o) : page.screenshot(o);
};

if (stills) {
  // Um PNG por tempo: é a folha que se olha antes do render inteiro.
  let tempos;
  if (stills === 'beats') {
    const b = JSON.parse(readFileSync(resolve(dirname(html), 'beats.json'), 'utf8'));
    tempos = b.beats.filter((t) => t <= DUR);
  } else tempos = stills.split(',').map(Number);
  const pasta = resolve(arg('out', 'out/stills'));
  mkdirSync(pasta, { recursive: true });
  for (const [i, t] of tempos.entries()) {
    const png = await quadro(t + 0.001);
    writeFileSync(`${pasta}/${String(i).padStart(3, '0')}_${t.toFixed(2)}s.png`, png);
  }
  console.log(`${tempos.length} stills em ${pasta}`);
  await browser.close();
  process.exit(0);
}

const de = Number(arg('de', 0)), ate = Math.min(Number(arg('ate', DUR)), DUR);
const out = resolve(arg('out', 'out/silent.mp4'));
mkdirSync(dirname(out), { recursive: true });
if (existsSync(out)) console.log('reescrevendo', out);

// tmix junta SUB subquadros seguidos; select fica com um de cada grupo.
const vf = SUB > 1 ? `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/${FPS}/TB` : 'null';
const cod = ALFA ? ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le']
  : ['-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-g', String(FPS), '-movflags', '+faststart'];
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-i', '-',
  '-vf', vf, '-r', String(FPS), ...cod, out], { stdio: ['pipe', 'inherit', 'inherit'] });

const t0 = Date.now();
const total = Math.round((ate - de) * FPS * SUB);
for (let i = 0; i < total; i++) {
  const png = await quadro(de + i / (FPS * SUB));
  if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
  if (i % (FPS * SUB * 2) === 0) console.log(`${(i / (FPS * SUB)).toFixed(0)}s de ${(ate - de).toFixed(1)}s`);
}
ff.stdin.end();
await new Promise((r) => ff.on('close', r));
await browser.close();
console.log(`${out} · ${formato} ${W}x${H} · ${FPS} qps x ${SUB} sub · ${((Date.now() - t0) / 1000).toFixed(0)} s de render`);
