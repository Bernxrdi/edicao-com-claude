# Monta o projeto do HyperFrames de um reel a partir do modelo: acha cada deixa na transcrição da versão
# cortada (Whisper de novo sobre a vN: os tempos do bruto vinham adiantados em alguns trechos), corrige o
# texto da legenda e prepara os arquivos. O projeto (vídeo e fontes) fica fora do workspace, em
# <pasta dos vídeos>/<ep>/trabalho/reel<N>/.
# Uso (da raiz): python3 canal/scripts/reel/montar-motion.py <ep> <reel> [base]   (modelo e deixas em episodios/<ep>/motion-fonte/)
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit import VIDEOS, marca  # noqa: E402

RAIZ = Path(__file__).resolve().parents[3]
FONTES = RAIZ / "canal/templates/fontes"
BASE = RAIZ / "canal/templates/motion/reel-base.template.html"
BIN = Path.home() / ".local/bin"
AQUI = Path(__file__).resolve().parent

ICONES = {
    "__USER__": '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>',
    "__CHECKS__": '<svg viewBox="0 0 24 24"><path d="M18 6 7 17l-5-5"/><path d="m22 10-7.5 7.5L13 16"/></svg>',
    "__CLOCK__": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "__SEND__": '<svg viewBox="0 0 24 24"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>',
    "__BELL__": '<svg viewBox="0 0 24 24"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    "__CHECK__": '<svg viewBox="0 0 24 24"><path d="m6 12 4 4 8-9"/></svg>',
    "__CHECKC__": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/></svg>',
    "__HEART__": '<svg viewBox="0 0 24 24"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
    "__PLANE__": '<svg viewBox="0 0 24 24"><path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4 20-7z"/></svg>',
}


def n(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def main():
    ep, reel = sys.argv[1], sys.argv[2]
    versao = sys.argv[3] if len(sys.argv) > 3 else "base"
    video = VIDEOS / ep
    texto = RAIZ / "canal/episodios" / ep
    fonte = texto / "motion-fonte" if (texto / "motion-fonte" / f"{reel}.json").exists() else AQUI  # modelo e deixas do reel
    cfg = json.loads((fonte / f"{reel}.json").read_text())
    retrato = json.loads((texto / "versoes" / f"{versao}.json").read_text())
    dur = retrato["duracao"]
    outro = float(cfg.get("outro", {}).get("segundos", 0))  # final em motion depois da fala

    # transcrição literal de novo, sobre a base (palavra por palavra, no tempo do vídeo final). O prompt com
    # hesitação faz o Whisper mostrar "né", "hã" e repetição em vez de limpar: é a prova de que o corte ficou limpo
    base_mp4 = video / "editado" / f"{versao}.mp4"
    tdir = video / "trabalho" / f"{versao}-literal"
    tjson = tdir / f"{versao}.json"
    if not tjson.exists() or tjson.stat().st_mtime < base_mp4.stat().st_mtime:
        tdir.mkdir(parents=True, exist_ok=True)
        wav = tdir / f"{versao}.wav"
        subprocess.run([BIN / "ffmpeg", "-v", "error", "-y", "-i", video / "editado" / f"{versao}.mp4", "-ac", "1", "-ar", "16000", wav], check=True)
        subprocess.run([BIN / "mlx_whisper", wav, "--model", "mlx-community/whisper-large-v3-turbo", "--language", "pt",
                        "--word-timestamps", "True", "--condition-on-previous-text", "False",
                        "--initial-prompt", "Então, é... né? hã... tipo, ele ele vai, o o cliente, tá?",
                        "--output-format", "json", "--output-dir", tdir, "--output-name", versao, "--verbose", "False"], check=True)
    W = [{"p": w["word"].strip(), "i": round(w["start"], 3), "f": round(w["end"], 3)}
         for s in json.loads(tjson.read_text())["segments"] for w in s.get("words", [])]
    N = [n(w["p"]) for w in W]

    # deixas: nome, frase, qual palavra da frase marca o tempo
    T, F, cursor, faltou = {}, {}, 0, []
    for nome, frase, k in cfg["deixas"]:
        alvo = frase.split()
        achou = next((i for i in range(cursor, len(N) - len(alvo) + 1) if N[i:i + len(alvo)] == alvo), None)
        if achou is None:
            faltou.append(nome)
            continue
        T[nome], F[nome] = W[achou + k]["i"], W[achou + k]["f"]
        cursor = achou
    if faltou:
        sys.exit("deixas não achadas: " + ", ".join(faltou))

    # legenda: o texto corrigido (o Whisper erra número e uma ou outra palavra), em caixa baixa, sem pontuação
    pal = [dict(w, t=w["p"]) for w in W]
    for padrao, troca in cfg["correcoes"]:
        alvo = padrao.split()
        i = 0
        while i <= len(pal) - len(alvo):
            if [n(w["p"]) for w in pal[i:i + len(alvo)]] == alvo:
                for j, novo in enumerate(troca):
                    if novo is None:
                        pal[i + j + 1]["i"] = pal[i + j]["i"]
                        pal[i + j]["fora"] = True
                    else:
                        pal[i + j]["t"] = novo
                i += len(alvo)
            else:
                i += 1
    pal = [w for w in pal if not w.get("fora")]
    chaves = {round(T[c], 3) for c in cfg["destaques"]}
    blocos, atual = [], []
    for w in pal:
        txt = re.sub(r"[.,!?;:…\"“”]", "", w["t"].lower()).strip()
        if not txt:
            continue
        if atual:
            junto = " ".join(x["t"] for x in atual + [{"t": txt}])
            if len(atual) >= 3 or len(junto) > 16 or w["i"] - atual[-1]["f"] > 0.35 or re.search(r"[.,!?]$", atual[-1]["cru"]):
                blocos.append(atual)
                atual = []
        atual.append({"t": txt, "i": w["i"], "f": w["f"], "k": round(w["i"], 3) in chaves, "cru": w["t"]})
    if atual:
        blocos.append(atual)
    LEG = [{"i": b[0]["i"], "f": b[-1]["f"], "p": [{"t": x["t"], "k": x["k"]} for x in b]} for b in blocos]

    proj = video / "trabalho" / reel
    (proj / "assets" / "fontes").mkdir(parents=True, exist_ok=True)
    for ttf in FONTES.glob("Manrope-*.ttf"):
        shutil.copy(ttf, proj / "assets" / "fontes" / ttf.name)
    rosto = proj / "assets" / "rosto.mp4"
    marca = proj / "assets" / ".rosto-de"
    if not rosto.exists() or not marca.exists() or marca.read_text() != versao or rosto.stat().st_mtime < base_mp4.stat().st_mtime:
        # H.264 com quadro-chave a cada 15 quadros: o HyperFrames extrai rápido e busca certo
        subprocess.run([BIN / "ffmpeg", "-v", "error", "-y", "-i", video / "editado" / f"{versao}.mp4", "-an", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-g", "15", "-movflags", "+faststart", rosto], check=True)
        marca.write_text(versao)
    if (fonte / f"{reel}.template.html").exists():  # modelo próprio do reel
        s = marca((fonte / f"{reel}.template.html").read_text())
    else:  # o modelo base, com as cenas do reel (se tiver) e a legenda
        s = marca(BASE.read_text())
        ler = lambda nome: (fonte / nome).read_text() if (fonte / nome).exists() else ""
        fim = cfg.get("outro", {}).get("linhas", ["curte e manda pra quem", "<b>vende</b> contigo"])
        s = s.replace("__FIM__", "".join(f'<span class="l"><span class="p">{x}</span></span>' for x in fim))
        s = (s.replace("<!--__CENAS__-->", ler("cenas.html")).replace("/*__CSS__*/", ler("cenas.css"))
              .replace("/*__ROTEIRO__*/", ler("roteiro.js")).replace("__TITULO__", cfg.get("titulo", ep)))
    for k, v in ICONES.items():
        s = s.replace(k, v)
    s = (s.replace("/*__T__*/ {}", json.dumps(T)).replace("/*__F__*/ {}", json.dumps(F))
          .replace("/*__LEG__*/ []", json.dumps(LEG, ensure_ascii=False))
          .replace("__DURV__", f"{dur:.3f}").replace("__DUR__", f"{dur + outro:.3f}"))
    (proj / "index.html").write_text(s)
    print(f"{proj / 'index.html'}")
    print(f"{len(T)} deixas, {len(LEG)} legendas, {dur:.2f} s" + (f" + {outro:.1f} s de final em motion" if outro else ""))
    print(" | ".join(" ".join(x["t"].upper() if x["k"] else x["t"] for x in b["p"]) for b in LEG))


if __name__ == "__main__":
    main()
