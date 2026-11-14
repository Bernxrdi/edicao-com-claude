#!/usr/bin/env python3
"""Movimento por segundo de cada clipe do bruto (19/10/2026): a média da diferença entre quadros, de 0 (parado) pra
cima (ação). Serve pra escolher take de treino só onde ele está fazendo a repetição e tirar o que fica parado.
Imprime uma barrinha por segundo e grava trabalho/movimento.json.

Uso: python3 canal/scripts/movimento.py <ep> IMG_9884 IMG_9885 ...
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import VIDEOS, marca  # noqa: E402

ep, clipes = sys.argv[1], sys.argv[2:]
pasta = VIDEOS / ep
saida = pasta / "trabalho" / "movimento.json"
out = json.loads(saida.read_text()) if saida.exists() else {}
for c in clipes:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pasta / "bruto" / f"{c}.MOV"), "-vf",
                        "fps=10,scale=160:90,format=gray,tblend=all_mode=difference,signalstats,"
                        "metadata=print:key=lavfi.signalstats.YAVG", "-f", "null", "-"], capture_output=True, text=True)
    vals = [float(x) for x in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", r.stderr)]
    seg = [round(sum(vals[i:i + 10]) / max(1, len(vals[i:i + 10])), 2) for i in range(0, len(vals), 10)]
    out[c] = seg
    print(f"{c} ({len(seg)} s): " + "".join(" ▁▂▃▄▅▆▇█"[min(8, int(v / 1.2))] for v in seg))
saida.parent.mkdir(parents=True, exist_ok=True)
saida.write_text(json.dumps(out))
