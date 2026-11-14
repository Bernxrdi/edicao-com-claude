# Prévias de música pra ele escolher (/musica): o vídeo entregue, com a voz restaurada, uma vez com cada música
# candidata, no volume que vai sair (~18 dB abaixo da voz). Ficam em trabalho/previas-musica/ e somem quando o
# definitivo sai. Uso (da raiz): python3 canal/scripts/reel/previas-musica.py <ep> <vN> <musica.mp3> [...]
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit import VIDEOS, marca  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finalizar import FF, mixar, voz_limpa  # noqa: E402


def main():
    ep, versao, musicas = sys.argv[1], sys.argv[2], sys.argv[3:]
    video = VIDEOS / ep
    pasta = video / "trabalho" / "previas-musica"
    pasta.mkdir(parents=True, exist_ok=True)
    voz = pasta / "voz.wav"
    print(voz_limpa(video / "editado" / "base.mp4", voz))
    alvos = [(None, "0-so-voz")] + [(Path(m).expanduser(), f"{k}-{Path(m).stem}") for k, m in enumerate(musicas, 1)]
    for arq, nome in alvos:
        audio = pasta / f"{nome}.wav"
        nota = mixar(voz, {"arquivo": str(arq)} if arq else None, audio)
        saida = pasta / f"previa-{nome}.mp4"
        subprocess.run([FF, "-v", "error", "-y", "-i", video / "editado" / f"{versao}.mp4", "-i", audio, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", saida], check=True)
        audio.unlink()
        print(f"{saida.name}: {nota}")
    for f in pasta.glob("voz*.wav"):
        f.unlink()


if __name__ == "__main__":
    main()
