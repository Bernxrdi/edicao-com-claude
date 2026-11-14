# Sidon (sarulab-speech, MIT): restauração de voz (ruído, eco, banda) em 48 kHz, na CPU.
# Adaptado da demo oficial (huggingface.co/spaces/sarulab-speech/sidon_demo_beta). Uso: python sidon.py entrada.wav saida.wav
import sys
import soundfile as sf
import torch
import torchaudio.functional as AF
import transformers
from huggingface_hub import hf_hub_download as dl

R = "sarulab-speech/sidon-v0.1"
fe = torch.jit.load(dl(R, "feature_extractor_cpu.pt"), map_location="cpu")
dec = torch.jit.load(dl(R, "decoder_cpu.pt"), map_location="cpu")
pre = transformers.SeamlessM4TFeatureExtractor.from_pretrained("facebook/w2v-bert-2.0")
x, sr = sf.read(sys.argv[1], dtype="float32")
x = torch.tensor(x if x.ndim == 1 else x.mean(1))
n = int(48000 / sr * len(x))
pico = x.abs().max()
x = 0.9 * x / pico
x = torch.nn.functional.pad(AF.resample(AF.highpass_biquad(x[None], sr, 50), sr, 16000), (0, 24000)).view(-1)
out, c = [], None
with torch.inference_mode():
    for ch in x.split(16000 * 96):
        f = fe(pre(torch.nn.functional.pad(ch, (160, 160)).numpy(), sampling_rate=16000, return_tensors="pt")["input_features"])["last_hidden_state"]
        if c is not None:
            f = torch.cat([c, f], 1)
        out.append(dec(f.transpose(1, 2)).view(-1)[:-960])
        c = f[:, -1:]
sf.write(sys.argv[2], torch.cat(out)[:n].numpy(), 48000)
