#!/usr/bin/env python3
"""O "se inscreve" do fim da abertura do vlog (18/10/2026), montado por cima de um trecho do vídeo dele.

Renderiza templates/motion/inscreva.html com fundo transparente (motor próprio, render.mjs --alfa),
pega o trecho do bruto, desfoca aos poucos (o "esmaecendo" que ele pediu), aplica a cor do plano
("acabamento"), cola o motion e os sons e grava <pasta dos vídeos>/<ep>/trabalho/cartelas/inscreva.mov.
No plano, entra como item: {"cartela": "inscreva", "usar": true}.

Uso: python3 canal/scripts/inscreva.py <ep> <clipe do bruto> <início em s>
"""
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
MOTOR = CANAL / "templates" / "motion" / "motor"
BIN = Path.home() / ".local" / "bin"
NODE = node_bin()
DUR = 3.4


def rodar(cmd, **kw):
    r = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"falhou: {' '.join(str(x) for x in cmd[:6])}\n{(r.stdout + r.stderr)[-2000:]}")
    return r


def main():
    ep, clipe, ini = sys.argv[1], sys.argv[2], float(sys.argv[3])
    plano = json.loads((CANAL / "episodios" / ep / "plano-de-edicao.json").read_text())
    W, H, fps = plano["saida"]["largura"], plano["saida"]["altura"], plano["saida"].get("fps", 30)
    pasta = VIDEOS / ep / "trabalho" / "cartelas"
    proj = pasta / "inscreva"
    (proj / "fontes").mkdir(parents=True, exist_ok=True)
    (proj / "index.html").write_text(marca((CANAL / "templates" / "motion" / "inscreva.html").read_text()))
    shutil.copy(MOTOR / "motion.js", proj / "motion.js")
    for f in (CANAL / "templates" / "fontes").glob("Manrope-*.ttf"):
        shutil.copy(f, proj / "fontes" / f.name)
    pw = playwright_core()
    env = {**os.environ, "PATH": f"{NODE}:{BIN}:{os.environ.get('PATH', '')}", "PLAYWRIGHT_CORE": str(pw)}
    formato = "16x9-4k" if W >= 3840 else "16x9"
    rodar([NODE / "node", MOTOR / "render.mjs", "--formato", formato, "--fps", fps, "--sub", "1", "--alfa",
           "--dur", DUR, "--out", proj / "motion.mov"], cwd=proj, env=env)
    sons = [{"t": 0.3, "tipo": "whoosh", "vol": 0.3}, {"t": 1.55, "tipo": "clique", "vol": 0.8},
            {"t": 1.67, "tipo": "pop", "vol": 0.5}]
    (proj / "sons.json").write_text(json.dumps(sons))
    rodar([NODE / "node", MOTOR / "sfx.mjs", proj / "sons.json", proj / "sfx.wav"], cwd=proj, env=env)
    cor = plano.get("acabamento") or "null"
    k = "min(T/0.45,1)"   # o desfoque entra junto com o véu do motion
    fc = (f"[0:v]fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,{cor},"
          f"split[a][b];[b]gblur=sigma={24 * W / 1920:.0f}[bb];"
          f"[a][bb]blend=all_expr='A*(1-{k})+B*{k}'[f];[1:v]format=yuva444p10le[m];"
          f"[f][m]overlay=format=auto,fade=t=in:st=0:d=0.3,format=yuv420p[v];"
          f"[2:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{DUR}[s]")
    rodar([BIN / "ffmpeg", "-v", "error", "-y", "-ss", ini, "-t", DUR, "-i", VIDEOS / ep / "bruto" / clipe,
           "-i", proj / "motion.mov", "-i", proj / "sfx.wav", "-filter_complex", fc, "-map", "[v]", "-map", "[s]",
           "-c:v", "hevc_videotoolbox", "-b:v", "20M" if W >= 3840 else "8M", "-tag:v", "hvc1",
           "-c:a", "pcm_s16le", "-t", DUR, pasta / "inscreva.mov"])
    shutil.rmtree(proj, ignore_errors=True)
    print(pasta / "inscreva.mov")


if __name__ == "__main__":
    main()
