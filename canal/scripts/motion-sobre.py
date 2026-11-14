#!/usr/bin/env python3
"""Um motion do motor próprio por cima de um trecho do vídeo dele, como cartela do plano (19/10/2026: a abertura
do canal, "parecida com o do final"). Generaliza o scripts/inscreva.py.

Renderiza templates/motion/<modelo>.html com fundo transparente (render.mjs --alfa), pega o trecho do bruto, desfoca
aos poucos, aplica a cor do plano ("acabamento"), cola o motion e os sons (<modelo>.sons.json) e grava
<pasta dos vídeos>/<ep>/trabalho/cartelas/<nome>.mov. No plano: {"cartela": "<nome>"}.

Uso: python3 canal/scripts/motion-sobre.py <ep> <modelo> <nome> <clipe do bruto> <início em s>
        [--arquivo origem:destino ...]   (ex.: perfil/foto.png:assets/perfil.png; caminho a partir da raiz do kit)
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
    ap.add_argument("ep"); ap.add_argument("modelo"); ap.add_argument("nome"); ap.add_argument("clipe"); ap.add_argument("ini", type=float)
    ap.add_argument("--arquivo", action="append", default=[])
    a = ap.parse_args()
    plano = json.loads((CANAL / "episodios" / a.ep / "plano-de-edicao.json").read_text())
    W, H, fps = plano["saida"]["largura"], plano["saida"]["altura"], plano["saida"].get("fps", 30)
    pasta = VIDEOS / a.ep / "trabalho" / "cartelas"
    proj = pasta / a.nome
    (proj / "fontes").mkdir(parents=True, exist_ok=True)
    (proj / "index.html").write_text(marca((MOTION / f"{a.modelo}.html").read_text()))
    shutil.copy(MOTION / "motor" / "motion.js", proj / "motion.js")
    for f in (CANAL / "templates" / "fontes").glob("Manrope-*.ttf"):
        shutil.copy(f, proj / "fontes" / f.name)
    for par in a.arquivo:
        origem, destino = par.split(":", 1)
        (proj / destino).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(origem) if Path(origem).is_absolute() else RAIZ / origem, proj / destino)
    pw = playwright_core()
    env = {**os.environ, "PATH": f"{NODE}:{BIN}:{os.environ.get('PATH', '')}", "PLAYWRIGHT_CORE": str(pw)}
    rodar([NODE / "node", MOTION / "motor" / "render.mjs", "--formato", "16x9-4k" if W >= 3840 else "16x9",
           "--fps", fps, "--sub", "1", "--alfa", "--out", proj / "motion.mov"], cwd=proj, env=env)
    dur = float(rodar([BIN / "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                       proj / "motion.mov"]).stdout.strip())
    sons = MOTION / f"{a.modelo}.sons.json"
    if sons.exists():
        rodar([NODE / "node", MOTION / "motor" / "sfx.mjs", sons, proj / "sfx.wav"], cwd=proj, env=env)
        audio = ["-i", proj / "sfx.wav"]
    else:
        audio = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    cor = plano.get("acabamento") or "null"
    k = "min(T/0.45,1)"
    fc = (f"[0:v]fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,{cor},"
          f"split[a][b];[b]gblur=sigma={24 * W / 1920:.0f}[bb];[a][bb]blend=all_expr='A*(1-{k})+B*{k}'[f];"
          f"[1:v]format=yuva444p10le[m];[f][m]overlay=format=auto,fade=t=in:st=0:d=0.2,format=yuv420p[v];"
          f"[2:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{dur}[s]")
    rodar([BIN / "ffmpeg", "-v", "error", "-y", "-ss", a.ini, "-t", dur, "-i",
           VIDEOS / a.ep / "bruto" / a.clipe, "-i", proj / "motion.mov", *audio,
           "-filter_complex", fc, "-map", "[v]", "-map", "[s]", "-c:v", "hevc_videotoolbox",
           "-b:v", "20M" if W >= 3840 else "8M", "-tag:v", "hvc1", "-c:a", "pcm_s16le", "-t", dur, pasta / f"{a.nome}.mov"])
    shutil.rmtree(proj, ignore_errors=True)
    print(pasta / f"{a.nome}.mov", f"({dur:.1f} s)")


if __name__ == "__main__":
    main()
