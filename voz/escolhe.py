# Escolhe a melhor tomada de cada fala do falar.py e grava com a marca d'água de IA (Perth, da Resemble AI).
# Fica a tomada com menos palavras erradas (o Whisper ouviu cada uma no ouvir.py); empate, a primeira.
# Acima de 5% de erro, avisa: gerar de novo ou a pessoa grava. Roda no ambiente torch do kit:
#   ~/.local/share/edicao-com-claude/voz/torch/bin/python -I escolhe.py <job.json>
import json
import re
import sys
import unicodedata
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import soundfile as sf  # noqa: E402

try:
    import perth  # noqa: E402
    MARCA = perth.PerthImplicitWatermarker()
except Exception as erro:  # sem a marca d'água o arquivo sai igual, com aviso
    MARCA = None
    print(f"aviso: marca d'água de IA indisponível ({erro}); as falas saem sem ela", flush=True)

job = Path(sys.argv[1])
trabalho = json.loads(job.read_text())
lido = json.loads(job.with_suffix(".lido.json").read_text())


def palavras(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.findall(r"[a-z0-9]+", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def wer(ref, hip):
    r, h = palavras(ref), palavras(hip)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        ant, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            ant, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, ant + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(1, len(r))


escolhas = {}
for f in trabalho:
    notas = [{"arq": a, "erro": round(wer(f["texto"], lido.get(a, "")), 3), "ouvido": lido.get(a, "")} for a in f["tomadas"]]
    melhor = min(notas, key=lambda n: n["erro"])
    wav, sr = sf.read(melhor["arq"], dtype="float32")
    sf.write(f["saida"], MARCA.apply_watermark(wav, sample_rate=sr) if MARCA else wav, sr)
    escolhas[f["id"]] = {"saida": f["saida"], "tomadas": notas, "escolhida": melhor["arq"]}
    aviso = "" if melhor["erro"] <= 0.05 else f"  · CONFERIR (número por extenso conta como erro) · ouviu: {melhor['ouvido']}"
    print(f"{Path(f['saida']).name}: {Path(melhor['arq']).name}, palavras erradas {melhor['erro'] * 100:.0f}%{aviso}", flush=True)
(job.parent / "escolhas.json").write_text(json.dumps(escolhas, ensure_ascii=False, indent=1))
job.unlink()
job.with_suffix(".lido.json").unlink()
