// Sons de interface sintetizados no código (11/10/2026): clique, pop, baque e whoosh, cada um no
// tempo de um toque ou de uma troca de estado. Não é música: música só a que ele escolher (/musica).
// Uso: node sfx.mjs sons.json out/sfx.wav
// sons.json: [{"t": 0.80, "tipo": "clique"}, {"t": 2.0, "tipo": "whoosh", "vol": 0.6}, ...]
// Tempo: o do toque na lista de estados, ou o "hits" do beats.json quando tem música.

import { readFileSync, writeFileSync } from 'node:fs';

const SR = 48000;
const sons = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const fim = Math.max(...sons.map((c) => c.t)) + 1.5;
const buf = new Float32Array(Math.ceil(fim * SR));

let s = 42; const ruido = () => (s = (s * 1664525 + 1013904223) >>> 0) / 2147483648 - 1;   // com semente
const VOZES = {
  clique: [0.05, (t) => Math.sin(2 * Math.PI * 1800 * t) * Math.exp(-t * 90) * 0.5],
  pop:    [0.15, (t) => Math.sin(2 * Math.PI * (600 + 900 * t) * t) * Math.exp(-t * 30) * 0.4],
  baque:  [0.50, (t) => Math.sin(2 * Math.PI * (90 - 60 * t) * t) * Math.exp(-t * 9) * 0.9],
  whoosh: [0.35, (t) => ruido() * Math.sin(Math.PI * Math.min(1, t / 0.35)) * 0.25],
  tique:  [0.03, (t) => Math.sin(2 * Math.PI * 3200 * t) * Math.exp(-t * 160) * 0.3],
};
for (const c of sons) {
  const [dur, fn] = VOZES[c.tipo] || (() => { throw new Error('tipo: ' + Object.keys(VOZES)); })();
  const ini = Math.floor(c.t * SR), vol = c.vol ?? 1;
  for (let i = 0; i < dur * SR && ini + i < buf.length; i++) buf[ini + i] += fn(i / SR) * vol;
}

const n = buf.length, b = Buffer.alloc(44 + n * 2);   // WAV mono 16 bits
b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8);
b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34);
b.write('data', 36); b.writeUInt32LE(n * 2, 40);
for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, buf[i])) * 32767), 44 + i * 2);
writeFileSync(process.argv[3], b);
console.log(`${process.argv[3]} · ${sons.length} sons · ${fim.toFixed(1)} s`);
