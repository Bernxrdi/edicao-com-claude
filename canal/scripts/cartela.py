#!/usr/bin/env python3
"""Renderiza uma cartela de tela cheia do motor próprio (templates/motion/<modelo>.html) pra entrar no plano
como item {"cartela": "<nome>"} (18/10/2026: o fim personalizado do vídeo, com o canal e o Instagram).

Sons: templates/motion/<modelo>.sons.json (lista de {t, tipo, vol}, pelo motor/sfx.mjs), se existir.
Arquivos que a página usa: --arquivo origem:destino (ex.: perfil/foto.png:assets/perfil.png; caminho a partir da raiz do kit).
Sai <pasta dos vídeos>/<ep>/trabalho/cartelas/<nome>.mov (4K, 30 qps, áudio PCM).

Uso: python3 canal/scripts/cartela.py <ep> <modelo> <nome> [--arquivo origem:destino ...]
"""
import argparse
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
MOTION = CANAL / "templates" / "motion"
BIN = Path.home() / ".local" / "bin"
NODE = node_bin()


def rodar(cmd, **kw):
    r = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"falhou: {' '.join(str(x) for x in cmd[:6])}\n{(r.stdout + r.stderr)[-2000:]}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep"); ap.add_argument("modelo"); ap.add_argument("nome")
    ap.add_argument("--arquivo", action="append", default=[])
    ap.add_argument("--formato", default="16x9-4k")
    a = ap.parse_args()
    pasta = VIDEOS / a.ep / "trabalho" / "cartelas"
    proj = pasta / a.nome
    (proj / "fontes").mkdir(parents=True, exist_ok=True)
    (proj / "index.html").write_text(marca((MOTION / f"{a.modelo}.html").read_text()))
    shutil.copy(MOTION / "motor" / "motion.js", proj / "motion.js")
    for f in (CANAL / "templates" / "fontes").glob("Manrope-*.ttf"):
        shutil.copy(f, proj / "fontes" / f.name)
    for par in a.arquivo:
        origem, destino = par.split(":", 1)
        o = Path(origem) if Path(origem).is_absolute() else RAIZ / origem
        (proj / destino).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(o, proj / destino)
    pw = playwright_core()
    env = {**os.environ, "PATH": f"{NODE}:{BIN}:{os.environ.get('PATH', '')}", "PLAYWRIGHT_CORE": str(pw)}
    rodar([NODE / "node", MOTION / "motor" / "render.mjs", "--formato", a.formato, "--fps", "30", "--sub", "2",
           "--out", proj / "mudo.mp4"], cwd=proj, env=env)
    dur = float(rodar([BIN / "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                       proj / "mudo.mp4"]).stdout.strip())
    sons = MOTION / f"{a.modelo}.sons.json"
    if sons.exists():
        rodar([NODE / "node", MOTION / "motor" / "sfx.mjs", sons, proj / "sfx.wav"], cwd=proj, env=env)
        audio = ["-i", proj / "sfx.wav"]
    else:
        audio = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    rodar([BIN / "ffmpeg", "-v", "error", "-y", "-i", proj / "mudo.mp4", *audio, "-map", "0:v", "-map", "1:a",
           "-c:v", "copy", "-af", f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{dur}",
           "-c:a", "pcm_s16le", "-t", f"{dur}", pasta / f"{a.nome}.mov"])
    shutil.rmtree(proj, ignore_errors=True)
    print(pasta / f"{a.nome}.mov", f"({dur:.1f} s)")


if __name__ == "__main__":
    main()
