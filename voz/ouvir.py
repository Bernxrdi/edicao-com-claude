# O Whisper lê cada tomada do falar.py (pra conferir palavra por palavra). Roda no Python do mlx-whisper:
#   <python do mlx-whisper> -I ouvir.py saida.json tomada1.wav tomada2.wav ...   (o falar.py chama sozinho)
import json
import sys

import mlx_whisper

lido = {}
for arq in sys.argv[2:]:
    r = mlx_whisper.transcribe(arq, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="pt")
    lido[arq] = r["text"].strip()
open(sys.argv[1], "w").write(json.dumps(lido, ensure_ascii=False, indent=1))
