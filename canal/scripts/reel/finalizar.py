# Fecha um reel: voz restaurada pelo Sidon (tira ruído e eco, como o "melhorar voz" do CapCut; /voz), música só
# se ele escolheu (plano "musica", vinda do /musica) calibrada pra ficar ~18 dB abaixo da voz, −14 LUFS, colada
# na animação do HyperFrames. Sai o definitivo em <pasta dos vídeos>/<ep>/editado/<vN>.mp4, com o retrato
# em versoes/<vN>.json, e a limpeza (versão anterior e arquivo de trabalho) na hora.
# Uso (da raiz): python3 canal/scripts/reel/finalizar.py <ep> <reel> [vN] [base]
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit import VIDEOS, marca  # noqa: E402

RAIZ = Path(__file__).resolve().parents[3]
FF = shutil.which("ffmpeg") or str(Path.home() / ".local/bin/ffmpeg")
VOZ_PY = Path.home() / ".local/share/edicao-com-claude/voz/torch/bin/python"  # o ambiente do Sidon (./instalar.sh)
SIDON = RAIZ / "voz" / "sidon.py"
# Depois do Sidon: só corpo e controle (o ruído e o eco ele já tirou)
ACABAMENTO = "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=10:release=150:makeup=2"
# Sem o Sidon (não instalado ou falhou): a cadeia antiga, com o redutor de ruído do ffmpeg
CADEIA_ANTIGA = ("highpass=f=75,arnndn=m={rnn}:mix=0.85,equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3500:t=q:w=1.4:g=2,"
                 "highshelf=f=9000:g=2,deesser=i=0.35,acompressor=threshold=-21dB:ratio=3:attack=8:release=140:makeup=2")
LOUD = "loudnorm=I=-14:TP=-1.5:LRA=11"


def rms(arq: Path) -> float:
    r = subprocess.run([FF, "-hide_banner", "-i", arq, "-af", "astats=metadata=0:reset=0", "-f", "null", "-"],
                       capture_output=True, text=True)
    return float(re.findall(r"RMS level dB: (-?[\d.]+)", r.stderr)[-1])


def voz_limpa(video: Path, saida: Path) -> str:
    """Áudio do vídeo → Sidon → acabamento. Devolve o que foi usado."""
    bruto = saida.with_name(saida.stem + "-entrada.wav")
    subprocess.run([FF, "-v", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", bruto], check=True)
    py, script = VOZ_PY, SIDON
    if py.exists() and script.exists():
        restaurada = saida.with_name(saida.stem + "-sidon.wav")
        r = subprocess.run([py, script, bruto, restaurada], capture_output=True, text=True, cwd=SIDON.parent)
        if r.returncode == 0 and restaurada.exists():
            subprocess.run([FF, "-v", "error", "-y", "-i", restaurada, "-af", ACABAMENTO, "-ar", "48000", saida], check=True)
            return "voz restaurada (Sidon)"
        print(f"  Sidon falhou, vai a cadeia antiga: {(r.stderr or '')[-300:]}")
    rnn = Path.home() / ".local/share/edicao-com-claude/arnndn/sh.rnnn"
    cadeia = CADEIA_ANTIGA.format(rnn=rnn) if rnn.exists() else CADEIA_ANTIGA.replace("arnndn=m={rnn}:mix=0.85", "afftdn=nf=-25")
    subprocess.run([FF, "-v", "error", "-y", "-i", bruto, "-af", cadeia, "-ar", "48000", saida], check=True)
    return "voz limpa (cadeia antiga)"


def mixar(voz: Path, musica: dict | None, saida: Path) -> str:
    """Voz + música (se tiver), −14 LUFS. A música é calibrada medindo: fica `abaixo_db` (padrão 18) abaixo da
    voz depois de abaixar na fala, com entrada e saída suaves."""
    if not musica or not musica.get("arquivo"):
        subprocess.run([FF, "-v", "error", "-y", "-i", voz, "-af", f"aformat=channel_layouts=stereo,{LOUD}", "-ar", "48000", saida], check=True)
        return "sem música"
    arq = Path(musica["arquivo"]).expanduser()
    alvo = -abs(musica.get("abaixo_db", 18))
    dur = float(subprocess.run([str(Path(FF).with_name("ffprobe")), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voz],
                               capture_output=True, text=True).stdout)
    rv, ganho = rms(voz), rms(voz) - 8 - rms(arq)
    leito = saida.with_name(saida.stem + "-leito.wav")
    def bed(g: float) -> None:
        fc = (f"[1:a]aformat=channel_layouts=stereo,atrim=start={musica.get('inicio', 0)},asetpts=PTS-STARTPTS,highpass=f=60,"
              f"equalizer=f=1800:t=q:w=1.0:g=-4,volume={g:.1f}dB,afade=t=in:d=0.4,afade=t=out:st={max(0, dur - 1.2):.2f}:d=1.2,atrim=0:{dur:.3f}[m];"
              "[0:a]aformat=channel_layouts=stereo[k];[m][k]sidechaincompress=threshold=0.05:ratio=2:attack=40:release=500[mb]")
        subprocess.run([FF, "-v", "error", "-y", "-i", voz, "-i", arq, "-filter_complex", fc, "-map", "[mb]", "-ar", "48000", leito], check=True)
    for _ in range(3):  # mede e corrige até ficar no alvo (cada música tem um volume)
        bed(ganho)
        erro = (rms(leito) - rv) - alvo
        if abs(erro) < 0.7:
            break
        ganho -= erro
    subprocess.run([FF, "-v", "error", "-y", "-i", voz, "-i", leito, "-filter_complex",
                    f"[0:a]aformat=channel_layouts=stereo[v];[v][1:a]amix=inputs=2:duration=first:normalize=0,{LOUD}[a]",
                    "-map", "[a]", "-ar", "48000", saida], check=True)
    leito.unlink(missing_ok=True)
    return f"música {arq.stem} ({rms(arq) + ganho - rv:+.0f} dB da voz, {alvo} dB depois de abaixar na fala)"


def main():
    ep, reel = sys.argv[1:3]
    versao = sys.argv[3] if len(sys.argv) > 3 else "v1"
    base = sys.argv[4] if len(sys.argv) > 4 else "base"
    video = VIDEOS / ep
    texto = RAIZ / "canal/episodios" / ep
    trab = video / "trabalho"
    voz = trab / f"{reel}-voz.wav"
    nota_voz = voz_limpa(video / "editado" / f"{base}.mp4", voz)
    # a animação pode passar da fala (final em motion): a voz ganha silêncio até o fim, e a música toca por baixo
    anim = float(subprocess.run([str(Path(FF).with_name("ffprobe")), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 trab / f"{reel}-animacao.mp4"], capture_output=True, text=True).stdout)
    cheia = trab / f"{reel}-voz-cheia.wav"
    subprocess.run([FF, "-v", "error", "-y", "-i", voz, "-af", f"apad=whole_dur={anim:.3f}", cheia], check=True)
    voz = cheia
    musica = json.loads((texto / "plano-de-edicao.json").read_text()).get("musica")
    audio = trab / f"{reel}-audio.wav"
    nota = f"{nota_voz} + {mixar(voz, musica, audio)}"
    saida = video / "editado" / f"{versao}.mp4"
    subprocess.run([FF, "-v", "error", "-y", "-i", trab / f"{reel}-animacao.mp4", "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", saida], check=True)
    retrato = json.loads((texto / "versoes" / f"{base}.json").read_text())
    retrato.update({"versao": versao, "renderizado": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "acabamento": f"trabalho/{reel} (HyperFrames) + {nota}, −14 LUFS", "corte_de": base})
    (texto / "versoes" / f"{versao}.json").write_text(json.dumps(retrato, ensure_ascii=False))
    print(f"{saida}  ({saida.stat().st_size / 1e6:.0f} MB, {nota})")
    limpar(video, reel, versao)


def limpar(video: Path, reel: str, versao: str) -> None:
    """O definitivo saiu: apaga as versões anteriores e o lixo de trabalho (decisão de 09/10/2026).
    Fica o que um ajuste precisa: o bruto, a base interna, o projeto da animação e as transcrições (json)."""
    apagado = 0
    alvos = [p for p in (video / "editado").glob("v*.mp4") if p.stem != versao]
    trab = video / "trabalho"
    alvos += [trab / reel / "renders", trab / f"{reel}-animacao.mp4", trab / "folhas", trab / "teste-ne", trab / "teste", trab / "voz-teste"]
    alvos += [p for p in trab.glob(f"{reel}-*.wav")] + [p for p in trab.glob("conf*")] + [p for p in trab.glob("previas*")]
    alvos += [p for p in trab.glob("*/*.wav")]
    for p in alvos:
        if not p.exists():
            continue
        apagado += sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else p.stat().st_size
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    print(f"  limpeza: {apagado / 1e6:.0f} MB de versão anterior e arquivo de trabalho")


if __name__ == "__main__":
    main()
