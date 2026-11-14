#!/usr/bin/env python3
"""Cartelas de hora do vlog (18/10/2026, pedido dele: "tela preta com contagem da hora" entre as cenas).

Lê canal/episodios/<ep>/cartelas.json:
  {"cartelas": [{"nome": "hora-01", "hora": "15:15", "antes": null, "dia": "terça"}, ...]}
("antes" é a hora da cena anterior: os dígitos rolam dela até a "hora"; vazio, rolam 3 casas.)

Pra cada uma: monta a página do modelo templates/motion/hora.html (motor próprio), renderiza em 4K
30 qps, sintetiza os sons (whoosh na entrada, tique em cada dígito que para) e junta em
<pasta dos vídeos>/<ep>/trabalho/cartelas/<nome>.mov. Só refaz a que mudou.
No plano de edição, a cartela entra como item: {"cartela": "hora-01", "usar": true}.

Uso: python3 canal/scripts/cartelas-hora.py <ep> [--formato 16x9-4k] [--so hora-01,hora-02]
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import VIDEOS, marca, node_bin, playwright_core  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CANAL = RAIZ / "canal"
MODELO = CANAL / "templates" / "motion" / "hora.html"
MOTOR = CANAL / "templates" / "motion" / "motor"
FONTES = CANAL / "templates" / "fontes"
BIN = Path.home() / ".local" / "bin"
NODE = node_bin()

# o mesmo tempo do modelo (INICIO + 0,42 s é quando cada dígito para)
INICIO = [0.20, 0.27, 0.34, 0.41]
BASES = [3, 10, 6, 10]
DUR = 2.1


def sons(c: dict) -> list[dict]:
    alvo = [int(x) for x in c["hora"].replace(":", "")]
    de = [int(x) for x in c["antes"].replace(":", "")] if c.get("antes") else [(d - 3) % b for d, b in zip(alvo, BASES)]
    passos = [(a - d) % b for a, d, b in zip(alvo, de, BASES)]
    return [{"t": 0.06, "tipo": "whoosh", "vol": 0.35}] + [
        {"t": round(i + 0.42, 3), "tipo": "tique", "vol": 0.55} for i, p in zip(INICIO, passos) if p]


def rodar(cmd, **kw):
    r = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"falhou: {' '.join(str(x) for x in cmd[:6])}\n{(r.stdout + r.stderr)[-2000:]}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--formato", default="16x9-4k")
    ap.add_argument("--so", help="só estas (nomes separados por vírgula)")
    a = ap.parse_args()
    cfg = json.loads((CANAL / "episodios" / a.ep / "cartelas.json").read_text())
    pasta = VIDEOS / a.ep / "trabalho" / "cartelas"
    pasta.mkdir(parents=True, exist_ok=True)
    pw = [playwright_core()]
    if not pw:
        sys.exit("não achei o playwright-core no cache do npx")
    env = {**os.environ, "PATH": f"{NODE}:{BIN}:{os.environ.get('PATH', '')}", "PLAYWRIGHT_CORE": str(pw[0])}
    modelo = marca(MODELO.read_text())
    so = set(a.so.split(",")) if a.so else None
    for c in cfg["cartelas"]:
        nome = c["nome"]
        if so and nome not in so:
            continue
        dados = {k: c.get(k) for k in ("hora", "antes", "dia")}
        html = modelo.replace(modelo[modelo.index("/*CFG*/"):modelo.index("/*FIM*/") + 7],
                              "/*CFG*/" + json.dumps(dados, ensure_ascii=False) + "/*FIM*/")
        marca = hashlib.sha1((html + a.formato + (MOTOR / "motion.js").read_text()).encode()).hexdigest()[:12]
        final = pasta / f"{nome}.mov"
        selo = pasta / f"{nome}.selo"
        if final.exists() and selo.exists() and selo.read_text() == marca:
            print(f"  {nome}: já pronta ({c['hora']})")
            continue
        proj = pasta / nome
        (proj / "fontes").mkdir(parents=True, exist_ok=True)
        (proj / "index.html").write_text(html)
        shutil.copy(MOTOR / "motion.js", proj / "motion.js")
        for f in FONTES.glob("Manrope-*.ttf"):
            shutil.copy(f, proj / "fontes" / f.name)
        mudo = proj / "mudo.mp4"
        rodar([NODE / "node", MOTOR / "render.mjs", "--formato", a.formato, "--fps", "30", "--sub", "2",
               "--dur", str(DUR), "--out", mudo], cwd=proj, env=env)
        (proj / "sons.json").write_text(json.dumps(sons(c)))
        rodar([NODE / "node", MOTOR / "sfx.mjs", proj / "sons.json", proj / "sfx.wav"], cwd=proj, env=env)
        rodar([BIN / "ffmpeg", "-v", "error", "-y", "-i", mudo, "-i", proj / "sfx.wav",
               "-map", "0:v", "-map", "1:a", "-c:v", "copy",
               "-af", f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{DUR}",
               "-c:a", "pcm_s16le", "-t", str(DUR), final])
        selo.write_text(marca)
        shutil.rmtree(proj, ignore_errors=True)
        print(f"  {nome}: {c.get('antes') or '...'} > {c['hora']} · {c.get('dia', '')}")


if __name__ == "__main__":
    main()
