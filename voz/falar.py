# Fala nova na voz de quem usa o kit: Qwen3-TTS 1.7B Base (Alibaba, Apache 2.0) pelo mlx-audio, local, sem conta.
# Imita a amostra guardada em ~/.local/share/edicao-com-claude/voz/referencia.wav (+ referencia.txt, o que é dito
# nela). Só a voz da própria pessoa, com ela sabendo (skill /voz, "A voz clonada").
#
#   <py do mlx> falar.py "texto" saida.wav [tomadas]
#   <py do mlx> falar.py --lista falas.txt <pasta> [tomadas]      (uma fala por linha, "id|texto")
#   <py do mlx> = ~/.local/share/edicao-com-claude/voz/mlx/bin/python -I
#
# Gera as tomadas (2 por padrão), o Whisper ouve cada uma (ouvir.py) e o escolhe.py fica com a que errou menos
# palavras, com a marca d'água de IA (Perth). Retoma: tomada que já existe não é gerada de novo, e o andamento
# fica gravado a cada fala. Uns 3 a 10 s pra cada 1 s de fala no M1. Rodar sozinho (sem render ao mesmo tempo).
import gc
import json
import subprocess
import sys
import time
import wave
from pathlib import Path

import mlx.core as mx
import numpy as np
from mlx_audio.tts.utils import load_model

AQUI = Path(__file__).resolve().parent
DADOS = Path.home() / ".local/share/edicao-com-claude/voz"
REF, REF_TXT = DADOS / "referencia.wav", DADOS / "referencia.txt"
TORCH = DADOS / "torch/bin/python"


def whisper_py() -> str:
    pasta = subprocess.run(["uv", "tool", "dir"], capture_output=True, text=True).stdout.strip()
    py = Path(pasta or Path.home() / ".local/share/uv/tools") / "mlx-whisper/bin/python"
    if not py.exists():
        sys.exit("não achei o mlx-whisper (rode ./instalar.sh na raiz do kit)")
    return str(py)


if not REF.exists() or not REF_TXT.exists():
    sys.exit(f"falta a amostra da voz em {DADOS} (skill /voz, 'A voz clonada': gravar 15 s e guardar)")

args = sys.argv[1:]
if args[0] == "--lista":
    pasta = Path(args[2])
    falas = [l.split("|", 1) for l in Path(args[1]).read_text().splitlines() if l.strip()]
    falas = [(i.strip(), t.strip(), pasta / f"{i.strip()}.wav") for i, t in falas]
    tomadas = int(args[3]) if len(args) > 3 else 2
else:
    saida = Path(args[1])
    falas = [(saida.stem, args[0], saida)]
    tomadas = int(args[2]) if len(args) > 2 else 2
falas = [f for f in falas if not f[2].exists()]
if not falas:
    sys.exit("nada a fazer: todas as falas já têm wav")
falas[0][2].parent.mkdir(parents=True, exist_ok=True)
job = falas[0][2].parent / ".falar-andamento.json"
trabalho = json.loads(job.read_text()) if job.exists() else []
feitos = {f["id"] for f in trabalho}

t0 = time.time()
modelo = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit")
print(f"Qwen3-TTS carregado em {time.time() - t0:.0f} s", flush=True)
ref_txt = REF_TXT.read_text().strip()


def gera(texto):
    it = modelo.generate(texto, ref_audio=str(REF), ref_text=ref_txt, lang_code="portuguese",
                         temperature=0.8, top_p=0.95, verbose=False)
    partes, sr = [], None
    for r in it:
        partes.append(np.array(r.audio, dtype=np.float32).reshape(-1))
        sr = r.sample_rate
    return np.concatenate(partes), sr


def grava(arq, wav, sr):
    with wave.open(str(arq), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(wav, -1, 1) * 32767).astype("<i2").tobytes())


for fid, texto, final in falas:
    takes = []
    for k in range(1, tomadas + 1):
        arq = final.with_name(f"{final.stem}-t{k}.wav")
        takes.append(str(arq))
        if arq.exists():                       # retomada: a tomada já saiu numa rodada que caiu
            continue
        mx.random.seed(100 + k)
        np.random.seed(100 + k)
        t = time.time()
        wav, sr = gera(texto)
        grava(arq, wav, sr)
        print(f"{arq.name}: {len(wav) / sr:.1f} s de fala em {time.time() - t:.0f} s", flush=True)
    if fid not in feitos:
        trabalho.append({"id": fid, "texto": texto, "saida": str(final), "tomadas": takes})
        feitos.add(fid)
    job.write_text(json.dumps(trabalho, ensure_ascii=False))

# libera a memória antes de ouvir e escolher (o M1 de 8 GB não segura os dois)
del modelo
gc.collect()
mx.clear_cache()
todas = [a for f in trabalho for a in f["tomadas"]]
subprocess.run([whisper_py(), "-I", str(AQUI / "ouvir.py"), str(job.with_suffix(".lido.json")), *todas], check=True)
subprocess.run([str(TORCH), "-I", str(AQUI / "escolhe.py"), str(job)], check=True)
