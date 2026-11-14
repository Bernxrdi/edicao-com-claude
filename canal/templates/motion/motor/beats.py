# /// script
# requires-python = ">=3.10"
# dependencies = ["librosa>=0.10", "numpy", "soundfile"]
# ///
"""Grade de batidas da música que ele escolheu (11/10/2026).

Uso: uv run beats.py musica.wav > beats.json   (a página e o render.mjs leem esse arquivo)

- beats: onde cada estado muda (a troca de cena cai na batida)
- downbeats: uma a cada 4 batidas, onde vão os momentos grandes
- hits: os picos medidos do áudio, onde entram os sons de interface (clique, whoosh)

Música só a que ele escolher pelo /musica. Sem música, a grade é um BPM fixo (M.batida no motion.js).
"""
import json
import sys

import librosa
import numpy as np

y, sr = librosa.load(sys.argv[1], sr=None, mono=True)
tempo, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
beats = librosa.frames_to_time(frames, sr=sr).round(3).tolist()

onset = librosa.onset.onset_strength(y=y, sr=sr)
peaks = librosa.util.peak_pick(onset, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=10)

json.dump({
    "bpm": round(float(np.atleast_1d(tempo)[0]), 2),
    "beats": beats,
    "downbeats": beats[::4],
    "hits": librosa.frames_to_time(peaks, sr=sr).round(3).tolist(),
    "duracao": round(len(y) / sr, 3),
}, sys.stdout, indent=1)
