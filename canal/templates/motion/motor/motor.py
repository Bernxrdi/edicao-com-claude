"""O resto do motor próprio, em ffmpeg (11/10/2026). Roda com python3 da pasta do projeto do vídeo.

  python3 motor.py folhas out/silent.mp4 [--tira 4.2] [--emenda]
      contato.png (2 quadros por segundo), celular.png (como lê com 360 px de largura) e, com
      --tira, 12 quadros seguidos em volta de uma ação rápida (pega salto e sobreposição).
      --emenda grava o vídeo duas vezes seguidas (loop_check.mp4) pra ver a emenda do loop.
      Folhas pequenas de propósito: é o que o Claude olha na crítica, e imagem custa conta.

  python3 motor.py mixar out/silent.mp4 out/final.mp4 [--sfx out/sfx.wav] [--musica m.wav]
      junta imagem, sons de interface e a música que ele escolheu, música de 18 a 25 dB abaixo
      quando tem voz (aqui não tem: música no volume dela, sons por cima) e tudo em -14 LUFS.

  python3 motor.py web out/final.mp4 out/web.mp4
      saída pra página: H.264 1080p sem áudio, faststart, até uns 4 MB, e o poster (primeiro quadro).
"""
import argparse
import subprocess
import sys
from pathlib import Path


def ff(*args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)])
    if r.returncode:
        sys.exit(f"ffmpeg falhou ({r.returncode})")


def duracao(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(video)], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def folhas(a):
    v = Path(a.video); pasta = v.parent
    dur = duracao(v)
    linhas = max(1, -(-int(dur * 2) // 6))
    ff("-i", v, "-vf", f"fps=2,scale=270:-1,tile=6x{linhas}:padding=4:color=gray", "-frames:v", 1,
       pasta / "contato.png")
    ff("-i", v, "-vf", f"fps=1,scale=360:-1,tile=5x{max(1, -(-int(dur) // 5))}:padding=4:color=gray",
       "-frames:v", 1, pasta / "celular.png")
    feitos = ["contato.png", "celular.png"]
    if a.tira is not None:
        ff("-ss", max(0, a.tira - 0.1), "-i", v, "-vf", "scale=320:-1,tile=12x1", "-frames:v", 1,
           pasta / f"tira-{a.tira}.png")
        feitos.append(f"tira-{a.tira}.png")
    if a.emenda:
        ff("-stream_loop", 1, "-i", v, "-c", "copy", pasta / "loop_check.mp4")
        feitos.append("loop_check.mp4")
    print(f"{pasta}: " + ", ".join(feitos))


def mixar(a):
    entradas = ["-i", a.video]
    trilhas = []
    if a.musica:
        entradas += ["-i", a.musica]; trilhas.append(f"[{len(trilhas) + 1}:a]")
    if a.sfx:
        entradas += ["-i", a.sfx]; trilhas.append(f"[{len(trilhas) + 1}:a]")
    if not trilhas:
        sys.exit("nada pra mixar: passe --sfx e/ou --musica")
    mix = (f"{''.join(trilhas)}amix=inputs={len(trilhas)}:normalize=0[m];" if len(trilhas) > 1
           else f"{trilhas[0]}anull[m];")
    ff(*entradas, "-filter_complex", mix + "[m]loudnorm=I=-14:TP=-1.5:LRA=11[a]",
       "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
       "-movflags", "+faststart", a.saida)
    print(a.saida)


def web(a):
    s = Path(a.saida)
    ff("-i", a.video, "-an", "-vf", "scale='if(gt(iw,ih),1920,1080)':-2", "-c:v", "libx264", "-preset", "slow",
       "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", s)
    ff("-i", s, "-frames:v", 1, s.with_suffix(".poster.jpg"))
    print(f"{s} · {s.stat().st_size / 1e6:.1f} MB (passou de 4 MB: subir o -crf) · poster {s.with_suffix('.poster.jpg').name}")


p = argparse.ArgumentParser(description="folhas, mixagem e saída pra web do motor próprio")
sub = p.add_subparsers(dest="cmd", required=True)
f = sub.add_parser("folhas"); f.add_argument("video"); f.add_argument("--tira", type=float); f.add_argument("--emenda", action="store_true")
m = sub.add_parser("mixar"); m.add_argument("video"); m.add_argument("saida"); m.add_argument("--sfx"); m.add_argument("--musica")
w = sub.add_parser("web"); w.add_argument("video"); w.add_argument("saida")
a = p.parse_args()
{"folhas": folhas, "mixar": mixar, "web": web}[a.cmd](a)
