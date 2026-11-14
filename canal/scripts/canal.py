#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""A máquina de edição do kit edicao-com-claude.

Uso: uv run canal/scripts/canal.py <comando> ...   (--help em qualquer comando)

Cada comando é um passo do fluxo do CLAUDE.md do canal. Tudo local e grátis: ffmpeg,
mlx-whisper (GPU do M1), a visão do Mac (visao.swift) e o Playwright do cache do npx.
Texto mora em canal/episodios/<ep>/; vídeo em <pasta dos vídeos>/<ep>/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import CFG, VIDEOS, marca  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CANAL = RAIZ / "canal"
EPISODIOS = CANAL / "episodios"
TEMPLATES = CANAL / "templates"
FONTES = TEMPLATES / "fontes"
SCRIPTS = CANAL / "scripts"
INBOX = CANAL / "ideias" / "inbox.md"
BIN = Path.home() / ".local" / "bin"
MODELO_WHISPER = "mlx-community/whisper-large-v3-turbo"
HYPERFRAMES = "hyperframes@0.8.140"  # fixo pra render sair igual; subir junto com o plugin (/motion)
EXT_VIDEO = {".mov", ".mp4", ".m4v"}
NOTA = "canal"

# Ajustáveis por episódio no plano-de-edicao.json ("parametros"). Ajuste que ele pedir e
# que valer pra sempre muda aqui e vai pro contexto/aprendizados.md.
PARAMETROS_PADRAO = {
    "palavra_erro": CFG["palavra_erro"],
    "folga_antes": 0.12,   # s de respiro antes da primeira palavra de um trecho
    "folga_depois": 0.22,  # s depois da última (o Whisper costuma cortar o fim da palavra)
    "juntar_pausa": 0.35,  # pausa menor que isso entre trechos fica no vídeo
    "pausa_frase": 0.7,    # pausa que separa uma frase da outra (pra achar o início do erro)
    "volta_maxima": 15.0,  # o erro nunca apaga mais que isso pra trás
    "fala_minima": 0.35,   # fração do clipe com fala pra ele contar como "fala" e não "rotina"
    "silencio_db": -35,    # abaixo disso o áudio conta como silêncio (lugar barulhento: subir pra -30)
    "silencio_min": 0.25,  # silêncio mais curto que isso não é cortado
}

FIM_FRASE = re.compile(r"[.!?…]$")
ALUCINACOES = ("amaraorg", "legendaspelacomunidade")  # frases que o Whisper inventa em silêncio

# HDR do iPhone (HLG ou PQ) pra SDR. Lento em 4K: o certo é gravar com "Vídeo HDR" desligado.
def tonemap(transferencia: str) -> str:
    return (f"zscale=tin={transferencia}:pin=bt2020:min=bt2020nc:t=linear:npl=100,format=gbrpf32le,"
            "zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


# ---------------------------------------------------------------- utilidades

def sair(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def ferramenta(nome: str) -> str:
    local = BIN / nome
    if local.exists():
        return str(local)
    achado = shutil.which(nome)
    if achado:
        return achado
    sair(f"não achei {nome}. Rode ./instalar.sh na raiz do kit.")


def rodar(cmd: list, **kw) -> subprocess.CompletedProcess:
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sair(f"falhou: {' '.join(str(c) for c in cmd[:8])} ...\n{r.stderr[-3000:]}")
    return r


def agora() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def hms(s: float, decimos: bool = False) -> str:
    s = max(0.0, s)
    h, resto = divmod(s, 3600)
    m, seg = divmod(resto, 60)
    base = f"{int(m):02d}:{seg:04.1f}" if decimos else f"{int(m):02d}:{int(seg):02d}"
    return f"{int(h)}:{base}" if h >= 1 else base


def ler_tempo(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    t = 0.0
    for parte in str(v).strip().split(":"):
        t = t * 60 + float(parte)
    return t


def norm(txt: str) -> str:
    t = unicodedata.normalize("NFD", txt.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", t)


def livre_gb() -> float:
    return shutil.disk_usage(Path.home()).free / 1e9


def tamanho(p: Path) -> int:
    if not p.exists():
        return 0
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def episodio(ep: str) -> tuple[Path, Path]:
    texto, video = EPISODIOS / ep, VIDEOS / ep
    if not texto.exists():
        existentes = sorted(p.name for p in EPISODIOS.iterdir() if p.is_dir())
        sair(f"episódio {ep} não existe. Existentes: {', '.join(existentes) or 'nenhum'}")
    for sub in ("bruto", "editado", "cortes-instagram", "trabalho"):
        (video / sub).mkdir(parents=True, exist_ok=True)
    return texto, video


def sondar(arquivo: Path) -> dict:
    r = rodar([ferramenta("ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", arquivo])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        sair(f"{arquivo} não tem vídeo")
    auds = [s for s in d["streams"] if s["codec_type"] == "audio"]
    aud = next((s for s in auds if s.get("codec_name") == "aac"), auds[0] if auds else None)
    larg, alt = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if abs(rot) % 180 == 90:
        larg, alt = alt, larg
    num, den = (v.get("avg_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    trc = v.get("color_transfer", "")
    tags = d["format"].get("tags", {})
    return {
        "duracao": round(float(d["format"].get("duration") or v.get("duration") or 0), 3),
        "largura": larg, "altura": alt, "fps": round(fps, 3),
        "hdr": trc in ("arib-std-b67", "smpte2084"), "transferencia": trc,
        "audio": aud["index"] if aud else None,
        "criado": tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time") or "",
    }


def clipes_brutos(video: Path) -> list[Path]:
    return sorted(p for p in (video / "bruto").iterdir() if p.suffix.lower() in EXT_VIDEO)


def resolver_video(video: Path, alvo: str) -> Path:
    if re.fullmatch(r"v\d+|final", alvo):
        p = video / "editado" / f"{alvo}.mp4"
    elif (video / "bruto" / alvo).exists():
        p = video / "bruto" / alvo
    else:
        p = Path(alvo).expanduser()
    if not p.exists():
        sair(f"não achei o vídeo {alvo}")
    return p


def visao() -> str:
    binario, fonte = BIN / "canal-visao", SCRIPTS / "visao.swift"
    if not binario.exists() or binario.stat().st_mtime < fonte.stat().st_mtime:
        rodar(["swiftc", "-O", fonte, "-o", binario])
    return str(binario)


def rostos(imagens: list) -> list[dict]:
    return json.loads(rodar([visao(), "rostos", *imagens]).stdout)


def maior_rosto(resultado: dict) -> dict | None:
    lista = resultado.get("rostos") or []
    return max(lista, key=lambda f: f["w"] * f["h"]) if lista else None


# ---------------------------------------------------------------- novo, espaço, ideias, importar

def cmd_novo(a):
    data = a.data or dt.date.today().isoformat()
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.slug):
        sair("slug: minúsculas, números e hífen (ex.: semana-de-treino)")
    ep = f"{data}-{a.slug}"
    texto, video = EPISODIOS / ep, VIDEOS / ep
    texto.mkdir(parents=True, exist_ok=True)
    for sub in ("bruto", "editado", "cortes-instagram", "trabalho"):
        (video / sub).mkdir(parents=True, exist_ok=True)
    print(ep)
    print(f"texto: {texto}")
    print(f"vídeo: {video}")


def cmd_espaco(a):
    print(f"livre no Mac: {livre_gb():.1f} GB")
    if not VIDEOS.exists():
        return
    for ep in sorted(p for p in VIDEOS.iterdir() if p.is_dir()):
        partes = {n: tamanho(ep / n) / 1e9 for n in ("bruto", "editado", "cortes-instagram", "trabalho")}
        desc = " · ".join(f"{n} {g:.2f} GB" for n, g in partes.items() if g >= 0.005)
        print(f"{ep.name}: {desc or 'vazio'}")


def cmd_ideias(a):
    if a.criar:
        corpo = f'make new note with properties {{name:"{NOTA}", body:"<h1>{NOTA}</h1><div>uma ideia por linha</div>"}}'
        script = (f'tell application "Notes"\nif (count of (notes whose name is "{NOTA}")) is 0 then {corpo}\n'
                  f'return plaintext of (first note whose name is "{NOTA}")\nend tell')
    else:
        script = (f'tell application "Notes"\nif (count of (notes whose name is "{NOTA}")) is 0 then return "__SEM_NOTA__"\n'
                  f'return plaintext of (first note whose name is "{NOTA}")\nend tell')
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=40)
    except subprocess.TimeoutExpired:
        sair("o Notas não respondeu. Provável: o macOS está pedindo permissão pra controlar o Notas "
             "(ele clica em OK) e aí roda de novo.")
    if r.returncode != 0:
        sair(f"não consegui ler o Notas: {r.stderr.strip()}\nSe for permissão: Ajustes do Sistema > "
             "Privacidade e Segurança > Automação, liberar o Notas pro app que roda o Claude.")
    texto = r.stdout.strip()
    if texto == "__SEM_NOTA__":
        sair(f'não existe a nota "{NOTA}" no Notas. Pra criar: canal.py ideias --criar')
    linhas = []
    for l in texto.splitlines()[1:]:
        l = re.sub(r"^([-•*·☐☑✓]|\d+[.)])\s*", "", l.strip()).strip()
        if l and norm(l) != "umaideiaporlinha":
            linhas.append(l)
    registro = CANAL / "ideias" / ".notas-importadas"
    vistas = set(registro.read_text().split()) if registro.exists() else set()
    inbox_norm = norm(INBOX.read_text())
    novas = [l for l in linhas if norm(l) and norm(l) not in vistas and norm(l) not in inbox_norm]
    if novas:
        hoje = dt.date.today().isoformat()
        with INBOX.open("a") as f:
            for l in novas:
                f.write(f"- {hoje} · {l} · nota do iPhone\n")
    registro.write_text("\n".join(sorted(vistas | {norm(l) for l in linhas})) + "\n")
    print(f"{len(novas)} ideia(s) nova(s) no inbox, de {len(linhas)} na nota.")
    for l in novas:
        print(f"  + {l}")


def cmd_importar(a):
    texto, video = episodio(a.ep)
    origem = Path(a.de).expanduser()
    if not a.arquivos:
        cands = sorted((p for p in origem.iterdir() if p.is_file() and p.suffix.lower() in EXT_VIDEO),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if not cands:
            sair(f"nenhum vídeo em {origem}")
        print(f"vídeos em {origem} (mais novos primeiro). Rode de novo passando os arquivos:")
        for p in cands[:40]:
            quando = dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")
            print(f"  {p.name}  {p.stat().st_size / 1e9:.2f} GB  {quando}")
        return
    arquivos = [Path(x).expanduser() if Path(x).expanduser().is_absolute() else origem / x for x in a.arquivos]
    faltam = [str(p) for p in arquivos if not p.exists()]
    if faltam:
        sair("não achei: " + ", ".join(faltam))
    total = sum(p.stat().st_size for p in arquivos) / 1e9
    if total * 4 > livre_gb():
        print(f"atenção: {total:.1f} GB de bruto e {livre_gb():.1f} GB livres. A edição precisa de uns "
              f"{total * 3:.0f} GB de folga; apague episódios antigos antes de renderizar.")
    for p in arquivos:
        destino = video / "bruto" / p.name
        n = 1
        while destino.exists():
            destino = video / "bruto" / f"{p.stem}-{n}{p.suffix}"
            n += 1
        shutil.move(str(p), destino)
        print(f"  {p.name} > bruto/{destino.name}")
    print(f"livre: {livre_gb():.1f} GB")


# ---------------------------------------------------------------- transcrever

def extrair_palavras(saida_whisper: dict) -> list[dict]:
    palavras = []
    for seg in saida_whisper.get("segments", []):
        if any(h in norm(seg.get("text", "")) for h in ALUCINACOES):
            continue
        for w in seg.get("words", []):
            txt = w["word"].strip()
            if txt:
                palavras.append({"p": txt, "i": round(w["start"], 3), "f": round(w["end"], 3),
                                 "prob": round(w.get("probability", 1.0), 3)})
    return palavras


def carregar_palavras(trab: Path, arquivo: str) -> list[dict]:
    p = trab / f"{Path(arquivo).stem}.palavras.json"
    return json.loads(p.read_text()) if p.exists() else []


def cmd_transcrever(a):
    texto, video = episodio(a.ep)
    trab = video / "trabalho"
    lista = clipes_brutos(video)
    if not lista:
        sair("bruto/ está vazio. Primeiro: importar.")
    meta_arq = trab / "clipes.json"
    meta = json.loads(meta_arq.read_text()) if meta_arq.exists() else {}
    for p in lista:
        if p.name not in meta or a.forcar:
            meta[p.name] = sondar(p)
    meta_arq.write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    hdr = [n for n, m in meta.items() if m["hdr"]]
    if hdr:
        print(f"atenção: {len(hdr)} clipe(s) em HDR ({', '.join(hdr)}). A edição converte pra SDR, mas fica "
              "lenta em 4K. No iPhone: Ajustes > Câmera > Gravar Vídeo > desligar Vídeo HDR.")
    ffmpeg, whisper = ferramenta("ffmpeg"), ferramenta("mlx_whisper")
    for p in lista:
        destino = trab / f"{p.stem}.palavras.json"
        if destino.exists() and not a.forcar:
            print(f"  {p.name}: já transcrito")
            continue
        m = meta[p.name]
        if m["audio"] is None:
            destino.write_text("[]")
            print(f"  {p.name}: sem áudio")
            continue
        wav = trab / f"{p.stem}.wav"
        rodar([ffmpeg, "-v", "error", "-y", "-i", p, "-map", f"0:{m['audio']}", "-ac", "1", "-ar", "16000", wav])
        inicio = time.time()
        rodar([whisper, wav, "--model", MODELO_WHISPER, "--language", "pt", "--word-timestamps", "True",
               "--condition-on-previous-text", "False", "--hallucination-silence-threshold", "2",
               "--output-format", "json", "--output-dir", trab, "--output-name", p.stem,
               "--verbose", "False"])
        bruto = json.loads((trab / f"{p.stem}.json").read_text())
        palavras = extrair_palavras(bruto)
        destino.write_text(json.dumps(palavras, ensure_ascii=False))
        wav.unlink(missing_ok=True)
        print(f"  {p.name}: {len(palavras)} palavras, {hms(m['duracao'])} de vídeo em {time.time() - inicio:.0f} s")


# ---------------------------------------------------------------- plano de edição

def achar_erros(palavras: list[dict], p: dict) -> list[dict]:
    """Cada palavra de erro apaga ela mesma e a frase que veio antes (o take errado)."""
    alvo = [norm(t) for t in p["palavra_erro"].split()]
    junto = "".join(alvo)
    n = [norm(w["p"]) for w in palavras]
    erros, ultimo, i = [], -1, 0
    while i < len(palavras):
        if n[i:i + len(alvo)] == alvo:
            k = len(alvo)
        elif n[i] == junto:
            k = 1
        else:
            i += 1
            continue
        fim_kw = i + k - 1
        j = i - 1
        if j <= ultimo:
            ini_idx = i
        else:
            while j - 1 > ultimo:
                ant = palavras[j - 1]
                if FIM_FRASE.search(ant["p"]):
                    break
                if palavras[j]["i"] - ant["f"] >= p["pausa_frase"]:
                    break
                if palavras[i]["i"] - ant["i"] > p["volta_maxima"]:
                    break
                j -= 1
            ini_idx = j
        ini = palavras[ini_idx]["i"] - 0.05
        if ini_idx > 0:
            ini = max(ini, palavras[ini_idx - 1]["f"] + 0.02)
        fim = palavras[fim_kw]["f"] + 0.15
        if fim_kw + 1 < len(palavras):
            fim = min(fim, palavras[fim_kw + 1]["i"] - 0.05)
        erros.append({"inicio": round(max(0.0, ini), 3), "fim": round(fim, 3),
                      "texto": " ".join(w["p"] for w in palavras[ini_idx:fim_kw + 1])})
        ultimo = fim_kw
        i = fim_kw + 1
    return erros


def subtrair(intervalos: list, cortes: list) -> list[list[float]]:
    saida = []
    for a, b in intervalos:
        partes = [(a, b)]
        for c0, c1 in cortes:
            novas = []
            for x, y in partes:
                if c1 <= x or c0 >= y:
                    novas.append((x, y))
                    continue
                if c0 > x:
                    novas.append((x, c0))
                if c1 < y:
                    novas.append((c1, y))
            partes = novas
        saida.extend([list(t) for t in partes])
    return saida


def intervalos_de_fala(palavras: list[dict], erros: list[dict], dur: float, p: dict) -> list[list[float]]:
    cortes = [(e["inicio"], e["fim"]) for e in erros]
    ivs: list[list[float]] = []
    for w in palavras:
        meio = (w["i"] + w["f"]) / 2
        if any(c0 <= meio <= c1 for c0, c1 in cortes):
            continue
        a, b = max(0.0, w["i"] - p["folga_antes"]), min(dur, w["f"] + p["folga_depois"])
        if ivs and a - ivs[-1][1] <= p["juntar_pausa"]:
            ivs[-1][1] = max(ivs[-1][1], b)
        else:
            ivs.append([a, b])
    return ivs


def silencios(clipe: Path, m: dict, p: dict, trab: Path) -> list[tuple[float, float]]:
    """Trechos em silêncio de verdade no áudio (ffmpeg silencedetect), guardados em trabalho/."""
    if m["audio"] is None:
        return [(0.0, m["duracao"])]
    cache = trab / f"{clipe.stem}.silencios.json"
    chave = f"{p['silencio_db']}:{p['silencio_min']}"
    dados = json.loads(cache.read_text()) if cache.exists() else {}
    if chave not in dados:
        r = subprocess.run([ferramenta("ffmpeg"), "-hide_banner", "-nostats", "-i", str(clipe), "-map",
                            f"0:{m['audio']}", "-af", f"silencedetect=n={p['silencio_db']}dB:d={p['silencio_min']}",
                            "-f", "null", "-"], capture_output=True, text=True)
        inicios = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
        fins = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
        fins += [m["duracao"]] * (len(inicios) - len(fins))
        dados[chave] = [[max(0.0, a), b] for a, b in zip(inicios, fins)]
        cache.write_text(json.dumps(dados))
    return [tuple(s) for s in dados[chave]]


def planejar_clipe(nome: str, m: dict, palavras: list[dict], p: dict, sils: list[tuple[float, float]]) -> dict:
    dur = m["duracao"]
    fala = sum(max(0.0, w["f"] - w["i"]) for w in palavras)
    tipo = "fala" if dur > 0 and fala / dur >= p["fala_minima"] and len(palavras) >= 6 else "rotina"
    erros = achar_erros(palavras, p)
    if tipo == "fala":
        # Corta só a lacuna entre palavras que também é silêncio no áudio: palavra que o
        # Whisper não reconheceu continua no vídeo.
        lacunas = complemento(intervalos_de_fala(palavras, erros, dur, p), dur)
        mudo = [(max(a, s0), min(b, s1)) for a, b in lacunas for s0, s1 in sils
                if min(b, s1) - max(a, s0) >= p["silencio_min"]]
        manter = subtrair([[0.0, dur]], mudo)
    else:
        manter = [[0.0, dur]]
    manter = subtrair(manter, [(e["inicio"], e["fim"]) for e in erros])
    manter = [[round(x, 3), round(y, 3)] for x, y in manter if y - x >= 0.25]
    clipe = {"arquivo": nome, "tipo": tipo, "usar": True, "duracao": dur, "trechos": manter, "erros": erros}
    if tipo == "rotina":
        clipe["revisar"] = "rotina: escolher o trecho bom olhando a folha (canal.py folha)"
    return clipe


def duracao_mantida(c: dict) -> float:
    if c.get("cartela"):
        return c.get("duracao", 0.0)
    return sum((t[1] - t[0]) / (t[2] if len(t) > 2 else 1.0) for t in c["trechos"])


def complemento(trechos: list, dur: float) -> list[tuple[float, float]]:
    buracos, cursor = [], 0.0
    for a, b in sorted(trechos):
        if a - cursor > 0.05:
            buracos.append((cursor, a))
        cursor = max(cursor, b)
    if dur - cursor > 0.05:
        buracos.append((cursor, dur))
    return buracos


def escrever_lista(texto: Path, plano: dict, trab: Path) -> Path:
    clipes = plano["clipes"]
    bruto = sum(c["duracao"] for c in clipes if not c.get("cartela"))
    editado = sum(duracao_mantida(c) for c in clipes if c.get("usar", True))
    L = [f"# Lista de cortes · {plano['episodio']}", "",
         f"> Gerada em {plano['gerado']} a partir de `plano-de-edicao.json`. Pra mudar: pedir em texto, "
         "o Claude ajusta o plano e renderiza de novo.", "",
         f"**Bruto:** {hms(bruto)} · **editado:** {hms(editado)} · **saiu:** {hms(bruto - editado)}", ""]
    for n, c in enumerate(clipes, 1):
        if c.get("cartela"):
            L += [f"## {n}. cartela {c['cartela']}" + (f" · {c['nota']}" if c.get("nota") else ""), ""]
            continue
        fora = "" if c["usar"] else " · FORA DO VÍDEO"
        L.append(f"## {n}. {c['arquivo']} · {c['tipo']} · {hms(c['duracao'])} > {hms(duracao_mantida(c))}{fora}")
        for e in c["erros"]:
            L.append(f'- **Erro** {hms(e["inicio"], True)} a {hms(e["fim"], True)}: "{e["texto"]}"')
        if c["tipo"] == "fala":
            cortes_erro = [(e["inicio"], e["fim"]) for e in c["erros"]]
            pausas = [(a, b) for a, b in complemento([t[:2] for t in c["trechos"]], c["duracao"])
                      if not any(a < c1 and b > c0 for c0, c1 in cortes_erro)]
            if pausas:
                maiores = sorted(pausas, key=lambda x: x[1] - x[0], reverse=True)[:4]
                L.append(f"- **Pausas cortadas:** {len(pausas)}, somando {sum(b - a for a, b in pausas):.1f} s. "
                         "Maiores: " + ", ".join(f"{hms(a)} ({b - a:.1f} s)" for a, b in maiores))
            palavras = carregar_palavras(trab, c["arquivo"])
            dentro = [w["p"] for w in palavras
                      if any(t[0] <= (w["i"] + w["f"]) / 2 <= t[1] for t in c["trechos"])]
            if dentro:
                L.append(f'- **Começa em:** "{" ".join(dentro[:10])}..."')
                L.append(f'- **Termina em:** "...{" ".join(dentro[-10:])}"')
        else:
            L.append(f"- Trecho usado: " + ", ".join(f"{hms(t[0], True)} a {hms(t[1], True)}"
                                                    + (f" ({t[2]}x)" if len(t) > 2 else "") for t in c["trechos"]))
            if c.get("revisar"):
                L.append(f"- {c['revisar']}")
        L.append("")
    arq = texto / "lista-de-cortes.md"
    arq.write_text("\n".join(L))
    return arq


def cmd_plano(a):
    texto, video = episodio(a.ep)
    trab = video / "trabalho"
    arq = texto / "plano-de-edicao.json"
    antigo = json.loads(arq.read_text()) if arq.exists() else None
    if antigo and not a.refazer:
        if a.so_lista:
            print(escrever_lista(texto, antigo, trab))
            return
        sair("o plano já existe (e pode ter ajuste à mão). Pra recalcular do zero: --refazer. "
             "Pra só reescrever a lista de cortes: --so-lista")
    meta_arq = trab / "clipes.json"
    if not meta_arq.exists():
        sair("falta transcrever: canal.py transcrever <ep>")
    meta = json.loads(meta_arq.read_text())
    params = {**PARAMETROS_PADRAO, **((antigo or {}).get("parametros") or {})}
    clipes = []
    for nome, m in sorted(meta.items(), key=lambda kv: (kv[1].get("criado") or "", kv[0])):
        clipe = video / "bruto" / nome
        if clipe.exists():
            clipes.append(planejar_clipe(nome, m, carregar_palavras(trab, nome), params,
                                         silencios(clipe, m, params, trab)))
    quatro_k = any(min(m["largura"], m["altura"]) >= 2160 for m in meta.values())
    larg, alt = (3840, 2160) if quatro_k else (1920, 1080)
    if meta and all(m["altura"] > m["largura"] for m in meta.values()):  # gravado em pé (reels)
        larg, alt = alt, larg
    saida = (antigo or {}).get("saida") or {"largura": larg, "altura": alt, "fps": 30}
    plano = {"episodio": a.ep, "gerado": agora(), "parametros": params, "saida": saida,
             "musica": (antigo or {}).get("musica"), "clipes": clipes}
    arq.write_text(json.dumps(plano, indent=2, ensure_ascii=False))
    lista = escrever_lista(texto, plano, trab)
    print(arq)
    print(lista)


# ---------------------------------------------------------------- render

def so_a_ultima(video: Path, fica: set[str]) -> None:
    """Versão nova apaga as anteriores na hora (decisão de 09/10/2026: "senão fica muito giga").
    Fica o que está em `fica` (a nova e a base dela) e a base interna do reel (editado/base.mp4)."""
    for p in (video / "editado").glob("v*.mp4"):
        if p.stem not in fica:
            p.unlink(missing_ok=True)
            print(f"  apagada a versão anterior: {p.name}")


def versoes(video: Path) -> list[str]:
    return sorted((p.stem for p in (video / "editado").glob("v*.mp4")), key=lambda s: int(s[1:]))


def cmd_render(a):
    texto, video = episodio(a.ep)
    plano = json.loads((texto / "plano-de-edicao.json").read_text())
    meta = json.loads((video / "trabalho" / "clipes.json").read_text())
    feitas = versoes(video)
    versao = a.versao or f"v{int(feitas[-1][1:]) + 1 if feitas else 1}"
    W, H = plano["saida"]["largura"], plano["saida"]["altura"]
    fps = plano["saida"].get("fps", 30)
    # Item do plano: clipe do bruto ou cartela já renderizada ({"cartela": "hora-01"}, em trabalho/cartelas/,
    # 18/10/2026). Trecho: [início, fim] ou [início, fim, velocidade] (0.5 = câmera lenta, do bruto em 60 qps).
    # Clipe colado numa cartela escurece pro preto antes dela e volta do preto depois (fade_cartela).
    itens = [c for c in plano["clipes"] if c.get("usar", True)]
    fade_cartela = plano.get("parametros", {}).get("fade_cartela", 0.3)
    segs = []
    for n, c in enumerate(itens):
        if c.get("cartela"):
            arq = video / "trabalho" / "cartelas" / f"{c['cartela']}.mov"
            if not arq.exists():
                sair(f"falta renderizar a cartela {c['cartela']} (scripts/cartelas-hora.py)")
            segs.append((c, 0.0, sondar(arq)["duracao"], 1.0, 0.0, 0.0, None))
            continue
        trechos = [t for t in c["trechos"] if t[1] - t[0] >= 0.25]
        antes = n > 0 and itens[n - 1].get("cartela")
        depois = n + 1 < len(itens) and itens[n + 1].get("cartela")
        for k, t in enumerate(trechos):
            vel = t[2] if len(t) > 2 and t[2] else 1.0
            recorte = (t[3] if len(t) > 3 else None) or c.get("recorte")
            segs.append((c, t[0], t[1], vel, c.get("fade_entrada", fade_cartela) if antes and k == 0 else 0.0,
                         c.get("fade_saida", fade_cartela) if depois and k == len(trechos) - 1 else 0.0, recorte))
    if not segs:
        sair("o plano não tem nenhum trecho pra usar")
    total = sum((y - x) / v for _, x, y, v, _, _, _ in segs)
    precisa = total * (0.0075 if W >= 3840 else 0.003) + 1
    if precisa > livre_gb():
        sair(f"pouco espaço: a render precisa de uns {precisa:.1f} GB e há {livre_gb():.1f} GB livres")
    ffmpeg = ferramenta("ffmpeg")
    pasta = video / "trabalho" / "segmentos" / versao
    shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True)
    # Cada trecho pronto fica guardado pela receita dele (18/10/2026): no ajuste, só refaz o que mudou.
    guardados = video / "trabalho" / "segmentos" / "prontos"
    guardados.mkdir(parents=True, exist_ok=True)
    usados = set()
    taxa = "20M" if W >= 3840 else "8M"
    lista, mapa, cursor, inicio = [], [], 0.0, time.time()
    acabamento = plano.get("acabamento")  # a cor do vídeo inteiro (filtro do ffmpeg), só nos clipes
    for k, (c, x, y, vel, f_in, f_out, recorte) in enumerate(segs, 1):
        cartela = c.get("cartela")
        fonte = video / "trabalho" / "cartelas" / f"{cartela}.mov" if cartela else video / "bruto" / c["arquivo"]
        m = sondar(fonte) if cartela else meta[c["arquivo"]]
        # Duração no quadro exato: vídeo e áudio do trecho saem do mesmo tamanho (senão escorregam a cada corte)
        d = round((y - x) / vel * fps) / fps
        vf = [tonemap(m["transferencia"])] if m["hdr"] else []
        if vel != 1.0:
            vf.append(f"setpts=PTS/{vel}")
        if recorte and recorte.get("modo") == "inteiro":
            # Vertical sem zoom (18/10/2026, "o jiu está com muito zoom e não pega eu"): o quadro em pé no centro,
            # com ele mesmo desfocado e escurecido preenchendo os lados. zoom > 1 aproxima um pouco, y escolhe a altura.
            fh = int(H * recorte.get("zoom", 1.0)) // 2 * 2
            oy = int(min(max(recorte.get("y", 0.5) * fh - H / 2, 0), fh - H))
            vf.append(f"split[fr][fu];[fu]scale={W // 8}:{H // 8}:force_original_aspect_ratio=increase,crop={W // 8}:{H // 8},"
                      f"gblur=sigma=5,scale={W}:{H},eq=brightness=-0.1:saturation=0.8[fu2];"
                      f"[fr]scale=-2:{fh},crop=iw:{H}:0:{oy}[fr2];[fu2][fr2]overlay=(W-w)/2:0")
        elif recorte:
            # Recorte no formato da saída: vertical vira 16:9 em volta da ação, ou um punch-in que tira algo do quadro.
            # x e y são o centro (0 a 1), zoom 1 é o maior recorte que cabe.
            iw, ih = m["largura"], m["altura"]
            cw = min(iw, ih * W / H) / recorte.get("zoom", 1.0)
            ch = cw * H / W
            cx = min(max(recorte.get("x", 0.5) * iw - cw / 2, 0), iw - cw)
            cy = min(max(recorte.get("y", 0.5) * ih - ch / 2, 0), ih - ch)
            vf.append(f"crop={int(cw) // 2 * 2}:{int(ch) // 2 * 2}:{int(cx)}:{int(cy)}")
        vf += [f"fps={fps}", f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos",
               f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0B0B0B", "setsar=1"]
        if acabamento and not cartela:
            vf.append(acabamento)
        if c.get("cinema"):
            # Barras de cinema (2,39:1) no edit de treino: "edit cinematográfica mesmo" (18/10/2026)
            barra = int((H - W / 2.39) / 2)
            vf.append(f"drawbox=x=0:y=0:w=iw:h={barra}:color=black:t=fill,drawbox=x=0:y=ih-{barra}:w=iw:h={barra}:color=black:t=fill")
        if f_in:
            vf.append(f"fade=t=in:st=0:d={f_in}")
        if f_out:
            vf.append(f"fade=t=out:st={d - f_out:.3f}:d={f_out}")
        vf.append("format=yuv420p")
        # Imagem de outro clipe por cima da fala (19/10/2026: "capricha na edição, pega os vídeos"): a voz continua
        # e a cena cobre. No item: "coberturas": [{"t": tempo no clipe da fala, "d": s, "arquivo": ..., "ini": s}]
        cobre = [cv for cv in (c.get("coberturas") or []) if not cartela and vel == 1.0 and x <= cv["t"] < y - 0.3]
        receita = json.dumps([str(fonte), fonte.stat().st_mtime, x, y, vel, f_in, f_out, recorte, W, H, fps, taxa,
                              None if cartela else acabamento, c.get("volume", 1.0)] + (["cinema"] if c.get("cinema") else [])
                             + (["cobre", cobre] if cobre else []), sort_keys=True)
        saida = guardados / f"{hashlib.sha1(receita.encode()).hexdigest()[:16]}.mov"
        usados.add(saida.name)
        cmd = [ffmpeg, "-v", "error", "-y", "-ss", f"{x:.3f}", "-t", f"{(y - x):.3f}", "-i", fonte]
        if m["audio"] is None:
            cmd += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            amap = "1:a"
        else:
            amap = f"0:{m['audio']}"
        af = ["aresample=48000"]
        if vel != 1.0:
            af.append(f"atempo={max(0.5, vel)}")
        if c.get("volume", 1.0) != 1.0:
            af.append(f"volume={c['volume']}")
        fade_a, fade_b = max(min(0.03, d / 4), f_in), max(min(0.03, d / 4), f_out)
        af += [f"afade=t=in:d={fade_a:.3f}", f"afade=t=out:st={d - fade_b:.3f}:d={fade_b:.3f}",
               f"apad,atrim=0:{d:.3f}"]
        mapa_v, filtro = ["-map", "0:v:0"], ["-vf", ",".join(vf)]
        if cobre:
            n_in = 1 if m["audio"] is not None else 2
            partes = ["[0:v]" + ",".join(vf[:-1]) + "[b0]"]
            for j, cv in enumerate(cobre, 1):
                mc = meta[cv["arquivo"]]
                r, dd = cv["t"] - x, min(cv["d"], y - cv["t"])
                cmd += ["-ss", f"{cv['ini']:.3f}", "-t", f"{dd + 0.2:.3f}", "-i", video / "bruto" / cv["arquivo"]]
                cvf = [tonemap(mc["transferencia"])] if mc["hdr"] else []
                if cv.get("recorte"):
                    rc, iw, ih = cv["recorte"], mc["largura"], mc["altura"]
                    cw = min(iw, ih * W / H) / rc.get("zoom", 1.0)
                    ch = cw * H / W
                    cx = min(max(rc.get("x", 0.5) * iw - cw / 2, 0), iw - cw)
                    cy = min(max(rc.get("y", 0.5) * ih - ch / 2, 0), ih - ch)
                    cvf.append(f"crop={int(cw) // 2 * 2}:{int(ch) // 2 * 2}:{int(cx)}:{int(cy)}")
                cvf += [f"fps={fps}", f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos",
                        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0B0B0B", "setsar=1"] + ([acabamento] if acabamento else [])
                partes.append(f"[{n_in + j - 1}:v]{','.join(cvf)},setpts=PTS-STARTPTS+{r:.3f}/TB[c{j}]")
                partes.append(f"[b{j - 1}][c{j}]overlay=eof_action=pass:enable='between(t,{r:.3f},{r + dd:.3f})'[b{j}]")
            partes.append(f"[b{len(cobre)}]format=yuv420p[v]")
            mapa_v, filtro = ["-map", "[v]"], ["-filter_complex", ";".join(partes)]
        cmd += mapa_v + ["-map", amap] + filtro + ["-af", ",".join(af),
                "-c:v", "hevc_videotoolbox", "-b:v", taxa, "-tag:v", "hvc1", "-g", str(fps * 2),
                "-c:a", "pcm_s16le", "-ac", "2", "-frames:v", str(round(d * fps)), saida.with_suffix(".tmp.mov")]  # áudio cru: o AAC vai uma vez só, no fim
        if not saida.exists():
            rodar(cmd)
            saida.with_suffix(".tmp.mov").rename(saida)
        lista.append(saida)
        extra = {k: v for k, v in (("id", c.get("id")), ("vel", vel if vel != 1.0 else None),
                                   ("mudo", True if c.get("volume", 1.0) == 0 else None)) if v is not None}
        if cartela:
            mapa.append({"cartela": cartela, "inicio": 0.0, "fim": round(d, 3), "saida_inicio": round(cursor, 3), **extra})
        else:
            mapa.append({"arquivo": c["arquivo"], "inicio": x, "fim": round(x + d * vel, 3),
                         "saida_inicio": round(cursor, 3), **extra})
        cursor += d
        print(f"  {k}/{len(segs)} {cartela or c['arquivo']} {hms(x, True)} a {hms(y, True)}"
              + (f" ({vel}x)" if vel != 1.0 else ""))
    (pasta / "lista.txt").write_text("".join(f"file '{p}'\n" for p in lista))
    junto = pasta / "junto.mov"
    rodar([ffmpeg, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "lista.txt", "-c", "copy", junto.name],
          cwd=pasta)
    destino = video / "editado" / f"{versao}.mp4"
    cmd = [ffmpeg, "-v", "error", "-y", "-i", junto]
    loud = "loudnorm=I=-14:TP=-1.5:LRA=11"
    # Música: a do vídeo inteiro ("musica") ou uma por trecho ("musicas", 18/10/2026: o edit do treino),
    # cada uma de um item do plano até outro ("de"/"ate": o nome do arquivo ou da cartela).
    faixas = []
    musica = plano.get("musica") or {}
    if musica.get("arquivo"):
        faixas.append({**musica, "_ini": 0.0, "_fim": cursor, "entrada": musica.get("entrada", 0.0),
                       "saida": musica.get("saida", 2.0)})
    for mu in plano.get("musicas") or []:
        ini = [s["saida_inicio"] for s in mapa if mu["de"] in (s.get("id"), s.get("arquivo"), s.get("cartela"))]
        fim = [s["saida_inicio"] + (s["fim"] - s["inicio"]) / s.get("vel", 1.0) for s in mapa
               if mu["ate"] in (s.get("id"), s.get("arquivo"), s.get("cartela"))]
        if not ini or not fim:
            sair(f"música {Path(mu['arquivo']).name}: não achei '{mu['de']}' ou '{mu['ate']}' no plano")
        faixas.append({**mu, "_ini": min(ini), "_fim": min(cursor, max(fim) + mu.get("depois", 0.0))})
    if faixas:
        fc, rotulos = [], []
        n_chave = sum(1 for f in faixas if f.get("abaixar_na_fala", True))
        fc.append(f"[0:a]asplit={n_chave + 1}[voz]" + "".join(f"[ch{i}]" for i in range(n_chave)))
        ch = 0
        for j, f in enumerate(faixas, 1):
            cmd += ["-stream_loop", "-1", "-i", Path(f["arquivo"]).expanduser()]
            dur = f["_fim"] - f["_ini"]
            ent, sai_ = f.get("entrada", 0.6), min(f.get("saida", 1.5), dur / 2)
            fc.append(f"[{j}:a]aresample=48000,aformat=channel_layouts=stereo,"
                      f"atrim=start={f.get('inicio', 0.0):.3f}:duration={dur:.3f},asetpts=PTS-STARTPTS,"
                      f"volume={f.get('volume', 0.15)},afade=t=in:d={ent:.3f},"
                      f"afade=t=out:st={dur - sai_:.3f}:d={sai_:.3f},"
                      f"adelay=delays={int(f['_ini'] * 1000)}:all=1[m{j}]")
            if f.get("abaixar_na_fala", True):
                fc.append(f"[m{j}][ch{ch}]sidechaincompress=threshold=0.02:ratio=12:attack=20:release=400[mb{j}]")
                ch += 1
                rotulos.append(f"[mb{j}]")
            else:
                rotulos.append(f"[m{j}]")
        fc.append(f"[voz]{''.join(rotulos)}amix=inputs={len(rotulos) + 1}:duration=first:normalize=0[mix]")
        cmd += ["-filter_complex", ";".join(fc) + f";[mix]{loud}[a]", "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "0:a", "-af", loud]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", destino]
    rodar(cmd)
    shutil.rmtree(pasta, ignore_errors=True)
    for p in guardados.glob("*.mov"):              # o que esta versão não usou sai (o disco não enche)
        if p.name not in usados:
            p.unlink(missing_ok=True)
    # O retrato da versão: o plano usado e as palavras já no tempo do vídeo final.
    # Sobrevive ao apagar o bruto; é dele que sai a transcrição.
    # Cada palavra vai pro trecho onde ela TERMINA. O Whisper estica o início da palavra pra dentro do
    # silêncio de antes, mas acerta o fim: pelo meio da palavra, a primeira de cada trecho ("Se", "A",
    # "É") sumia da legenda; pelo pedaço dentro, a palavra cortada logo depois do fim aparecia.
    palavras = []
    trab = video / "trabalho"
    # Cartela, câmera lenta e trecho mudo ficam fora: não têm fala no tempo certo.
    fala = [s for s in mapa if "arquivo" in s and "vel" not in s and not s.get("mudo")]
    for arquivo in dict.fromkeys(s["arquivo"] for s in fala):
        segs_arq = [s for s in fala if s["arquivo"] == arquivo]
        for w in carregar_palavras(trab, arquivo):
            s = next((s for s in segs_arq if s["inicio"] + 0.05 < w["f"] <= s["fim"] + 0.12), None)
            if s:
                desloc = s["saida_inicio"] - s["inicio"]
                palavras.append({"p": w["p"], "i": round(max(w["i"], s["inicio"]) + desloc, 3),
                                 "f": round(min(w["f"], s["fim"]) + desloc, 3)})
    palavras.sort(key=lambda w: w["i"])
    (texto / "versoes").mkdir(exist_ok=True)
    retrato = {"versao": versao, "renderizado": agora(), "duracao": round(cursor, 3),
               "plano": plano, "segmentos": mapa, "palavras": palavras}
    (texto / "versoes" / f"{versao}.json").write_text(json.dumps(retrato, ensure_ascii=False))
    print(f"{destino}  ({hms(cursor)}, {destino.stat().st_size / 1e9:.2f} GB, em {time.time() - inicio:.0f} s)")
    if versao.startswith("v"):  # a base interna do reel ("base") não apaga a versão entregue
        so_a_ultima(video, {versao})


# ---------------------------------------------------------------- motion (HyperFrames por cima da versão)

def hyperframes(args: list, pasta: Path, falhar: bool = True) -> subprocess.CompletedProcess:
    node, _ = node_e_playwright()
    env = {**os.environ, "PATH": f"{Path(node).parent}:{BIN}:{os.environ.get('PATH', '')}"}
    r = subprocess.run([str(Path(node).parent / "npx"), "--yes", HYPERFRAMES, *map(str, args)],
                       capture_output=True, text=True, cwd=pasta, env=env)
    if falhar and r.returncode != 0:
        sair(f"hyperframes {args[0]} falhou em {pasta.name}:\n{(r.stdout + r.stderr)[-3000:]}")
    return r


def cmd_motion(a):
    """Renderiza as cartelas de motion.json (HTML do HyperFrames, fundo transparente) e cola cada uma
    no tempo dela por cima da versão base. Sai a próxima vN; o corte e as palavras não mudam."""
    texto, video = episodio(a.ep)
    cfg = json.loads((texto / "motion.json").read_text())
    base = a.base or cfg.get("base") or (versoes(video) or [None])[-1]
    fonte = video / "editado" / f"{base}.mp4"
    retrato_base = texto / "versoes" / f"{base}.json"
    if not fonte.exists() or not retrato_base.exists():
        sair(f"não achei a versão base {base} (vídeo e versoes/{base}.json)")
    m = sondar(fonte)
    W, fps = m["largura"], round(m["fps"])
    trab = video / "trabalho" / "motion"
    (trab / "render").mkdir(parents=True, exist_ok=True)
    so = set(a.so.split(",")) if a.so else None
    cartelas, inicio = [], time.time()
    for c in cfg["cartelas"]:
        nome, ini = c["cartela"], ler_tempo(c["inicio"])
        html_fonte = texto / "motion" / f"{nome}.html"
        if not html_fonte.exists():
            sair(f"não achei {html_fonte}")
        pasta = trab / nome
        (pasta / "fontes").mkdir(parents=True, exist_ok=True)
        for f in FONTES.glob("*.ttf"):
            if not (pasta / "fontes" / f.name).exists():
                shutil.copy(f, pasta / "fontes" / f.name)
        shutil.copy(html_fonte, pasta / "index.html")
        mov = trab / "render" / f"{nome}.mov"
        if a.refazer or not mov.exists() or mov.stat().st_mtime < html_fonte.stat().st_mtime or (so and nome in so):
            hyperframes(["check"], pasta)
            t0 = time.time()
            hyperframes(["render", "--format", "mov", "--resolution", "4k" if W >= 3840 else "1080p",
                         "--fps", fps, "--quiet", "-o", mov, "."], pasta)
            print(f"  {nome}: renderizada em {time.time() - t0:.0f} s ({mov.stat().st_size / 1e6:.0f} MB)")
        d = sondar(mov)["duracao"]
        if ini + d > m["duracao"] + 0.05:
            print(f"  atenção: {nome} passa do fim do vídeo ({hms(ini + d, True)} > {hms(m['duracao'], True)})")
        cartelas.append({"cartela": nome, "inicio": round(ini, 3), "fim": round(ini + d, 3), "arquivo": mov})
    versao = a.versao or f"v{int(versoes(video)[-1][1:]) + 1}"
    destino = video / "editado" / f"{versao}.mp4"
    cmd = [ferramenta("ffmpeg"), "-v", "error", "-y", "-i", fonte]
    fc, atual = [], "0:v"
    for k, c in enumerate(cartelas, 1):
        cmd += ["-i", c["arquivo"]]
        fc.append(f"[{k}:v]setpts=PTS-STARTPTS+{c['inicio']:.3f}/TB[o{k}]")
        fc.append(f"[{atual}][o{k}]overlay=eof_action=pass:enable='between(t,{c['inicio']:.3f},{c['fim']:.3f})'[v{k}]")
        atual = f"v{k}"
    fc.append(f"[{atual}]format=yuv420p[v]")
    taxa = "20M" if W >= 3840 else "8M"
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "0:a?",
            "-c:v", "hevc_videotoolbox", "-b:v", taxa, "-tag:v", "hvc1", "-g", str(fps * 2),
            "-c:a", "copy", "-movflags", "+faststart", destino]
    rodar(cmd)
    retrato = json.loads(retrato_base.read_text())
    retrato.update({"versao": versao, "renderizado": agora(), "base": base,
                    "motion": [{k: v for k, v in c.items() if k != "arquivo"} for c in cartelas]})
    (texto / "versoes" / f"{versao}.json").write_text(json.dumps(retrato, ensure_ascii=False))
    print(f"{destino}  ({len(cartelas)} cartela(s) sobre a {base}, {destino.stat().st_size / 1e9:.2f} GB, "
          f"em {time.time() - inicio:.0f} s)")
    so_a_ultima(video, {versao, base})


# ---------------------------------------------------------------- transcrição do vídeo final

def dividir_linha(txt: str, limite: int = 42) -> str:
    if len(txt) <= limite:
        return txt
    meio = len(txt) // 2
    espacos = [i for i, ch in enumerate(txt) if ch == " "]
    if not espacos:
        return txt
    corte = min(espacos, key=lambda i: abs(i - meio))
    return txt[:corte] + "\n" + txt[corte + 1:]


def blocos_srt(palavras: list[dict]) -> list[list[dict]]:
    blocos, atual = [], []
    for w in palavras:
        if atual:
            junto = " ".join(x["p"] for x in atual + [w])
            frase_longa = FIM_FRASE.search(atual[-1]["p"]) and len(" ".join(x["p"] for x in atual)) > 30
            if len(junto) > 84 or w["f"] - atual[0]["i"] > 6 or w["i"] - atual[-1]["f"] > 0.6 or frase_longa:
                blocos.append(atual)
                atual = []
        atual.append(w)
    if atual:
        blocos.append(atual)
    return blocos


def t_srt(s: float) -> str:
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    seg, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{seg:02d},{ms:03d}"


def cmd_transcricao(a):
    texto, video = episodio(a.ep)
    todas = sorted((p.stem for p in (texto / "versoes").glob("v*.json")), key=lambda s: int(s[1:]))
    if not todas:
        sair("nenhuma versão renderizada ainda")
    versao = a.versao or todas[-1]
    retrato = json.loads((texto / "versoes" / f"{versao}.json").read_text())
    palavras = retrato["palavras"]
    (texto / "transcricao.json").write_text(json.dumps(
        {"versao": versao, "duracao": retrato["duracao"], "palavras": palavras}, ensure_ascii=False))
    srt = []
    blocos = blocos_srt(palavras)
    for n, b in enumerate(blocos, 1):
        fim = b[-1]["f"] + 0.2
        if n < len(blocos):
            fim = min(fim, blocos[n][0]["i"])
        srt.append(f"{n}\n{t_srt(b[0]['i'])} --> {t_srt(fim)}\n{dividir_linha(' '.join(w['p'] for w in b))}\n")
    (texto / "transcricao.srt").write_text("\n".join(srt))
    md = [f"# Transcrição · {a.ep} · {versao}", "",
          f"> Vídeo de {hms(retrato['duracao'])}. O tempo de cada palavra está em `transcricao.json`; a legenda "
          "pro YouTube em `transcricao.srt`. É a base de títulos, descrição, capítulos e cortes.", ""]
    paragrafo, inicio_par = [], None
    for k, w in enumerate(palavras):
        if inicio_par is None:
            inicio_par = w["i"]
        paragrafo.append(w["p"])
        prox = palavras[k + 1] if k + 1 < len(palavras) else None
        pausa = prox["i"] - w["f"] if prox else 99
        tam = len(" ".join(paragrafo))
        if prox is None or pausa > 1.2 or (FIM_FRASE.search(w["p"]) and tam > 280):
            md += [f"**[{hms(inicio_par)}]** {' '.join(paragrafo)}", ""]
            paragrafo, inicio_par = [], None
    (texto / "transcricao.md").write_text("\n".join(md))
    print(f"{versao}: {len(palavras)} palavras, {len(blocos)} legendas")
    for nome in ("transcricao.md", "transcricao.srt", "transcricao.json"):
        print(texto / nome)


# ---------------------------------------------------------------- olhar o vídeo (folha e frame)

def cmd_folha(a):
    """Uma imagem com quadros do vídeo e o tempo de cada um: o jeito do Claude 'ver' sem assistir."""
    texto, video = episodio(a.ep)
    alvo = resolver_video(video, a.alvo)
    m = sondar(alvo)
    ini = ler_tempo(a.de) if a.de else 0.0
    fim = min(ler_tempo(a.ate), m["duracao"]) if a.ate else m["duracao"]
    passo = a.passo or max(1, math.ceil((fim - ini) / a.quadros))
    n = max(1, math.ceil((fim - ini) / passo))
    linhas = math.ceil(n / 4)
    saida = video / "trabalho" / "folhas" / f"{alvo.stem}-{int(ini)}-{int(fim)}.jpg"
    saida.parent.mkdir(parents=True, exist_ok=True)
    fonte = str(FONTES / "Manrope-SemiBold.ttf")
    vf = []
    if m["hdr"]:
        vf.append(tonemap(m["transferencia"]))
    vf += [f"fps=1/{passo}", "scale=480:-2",
           f"drawtext=fontfile={fonte}:text='%{{pts\\:hms\\:{ini}}}':x=8:y=8:fontsize=20:fontcolor=white:"
           "box=1:boxcolor=black@0.6:boxborderw=6",
           f"tile=4x{linhas}:padding=4:margin=4"]
    cmd = [ferramenta("ffmpeg"), "-v", "error", "-y"]
    if passo >= 2:
        cmd += ["-skip_frame", "nokey"]
    cmd += ["-ss", f"{ini:.3f}", "-t", f"{fim - ini:.3f}", "-i", alvo, "-vf", ",".join(vf), "-frames:v", "1",
            "-q:v", "4", saida]
    rodar(cmd)
    print(saida)


def cmd_frame(a):
    texto, video = episodio(a.ep)
    alvo = resolver_video(video, a.alvo)
    t = ler_tempo(a.tempo)
    nome = a.nome or f"{alvo.stem}-{t:.1f}"
    saida = video / "trabalho" / "frames" / f"{nome}.png"
    saida.parent.mkdir(parents=True, exist_ok=True)
    m = sondar(alvo)
    cmd = [ferramenta("ffmpeg"), "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", alvo, "-frames:v", "1"]
    if m["hdr"]:
        cmd += ["-vf", tonemap(m["transferencia"])]
    rodar(cmd + [saida])
    print(saida)


def cmd_recorte(a):
    print(rodar([visao(), "recorte", Path(a.entrada).expanduser(), Path(a.saida).expanduser()]).stdout.strip())


# ---------------------------------------------------------------- thumbs

def node_e_playwright() -> tuple[str, str]:
    nodes = sorted((Path.home() / ".nvm" / "versions" / "node").glob("v*/bin/node"),
                   key=lambda p: [int(x) for x in p.parts[-3][1:].split(".")])
    node = str(nodes[-1]) if nodes else shutil.which("node")
    cores = list((Path.home() / ".npm" / "_npx").glob("*/node_modules/playwright-core"))
    if not node or not cores:
        sair("não achei o node ou o playwright-core (rode ./instalar.sh na raiz do kit)")
    versao = lambda p: [int(x) for x in json.loads((p / "package.json").read_text())["version"].split(".")[:3]]
    return node, str(max(cores, key=versao))


def renderizar(jobs: list[dict], trab: Path) -> None:
    node, core = node_e_playwright()
    arq = trab / "jobs.json"
    arq.write_text(json.dumps(jobs))
    rodar([node, SCRIPTS / "render.mjs", arq], env={**os.environ, "PLAYWRIGHT_CORE": core})


def recortar(img: Path, saida: Path) -> None:
    """Tira o fundo pelo BiRefNet (rembg, birefnet-portrait, grátis e local) e aplica a máscara na foto
    original. O recorte da visão do Mac deixava borda branca no cabelo e na orelha (aprendizados, 10/10/2026)."""
    mascara = saida.with_name(saida.stem + "-mascara.png")
    rodar([ferramenta("uvx"), "--python", "3.12", "--from", "rembg[cpu,cli]==2.0.67", "rembg", "i", "-m", "birefnet-portrait",
           "-om", img, mascara])
    rodar([ferramenta("ffmpeg"), "-v", "error", "-y", "-i", img, "-i", mascara, "-filter_complex",
           "[1:v]format=gray,scale=iw:ih[m];[0:v][m]alphamerge,format=rgba", saida])


def recorte_justo(rec: Path) -> Path:
    """O recorte cortado no contorno da pessoa (pro layout A: o rosto ocupa a altura da thumb)."""
    justo = rec.with_name(rec.stem + "-justo.png")
    if justo.exists() and justo.stat().st_mtime >= rec.stat().st_mtime:
        return justo
    m = sondar(rec)
    pw, ph = 384, max(2, round(384 * m["altura"] / m["largura"]))
    r = subprocess.run([ferramenta("ffmpeg"), "-v", "error", "-i", str(rec), "-vf", f"alphaextract,scale={pw}:{ph}",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    px = r.stdout
    linhas = [y for y in range(ph) if max(px[y * pw:(y + 1) * pw]) > 128]
    colunas = [x for x in range(pw) if max(px[x::pw][:ph]) > 128]
    if r.returncode or not linhas or not colunas:
        return rec
    fx, fy = m["largura"] / pw, m["altura"] / ph
    x, y = int(min(colunas) * fx), int(min(linhas) * fy)
    w = min(m["largura"] - x, int((max(colunas) + 1) * fx) - x)
    h = min(m["altura"] - y, int((max(linhas) + 1) * fy) - y)
    rodar([ferramenta("ffmpeg"), "-v", "error", "-y", "-i", rec, "-vf", f"crop={w}:{h}:{x}:{y}", justo])
    return justo


def frase_html(frase: str) -> str:
    seguro = html.escape(frase)
    return re.sub(r"\*(.+?)\*", r"<strong>\1</strong>", seguro).replace("\n", "<br>")


def cmd_thumbs(a):
    """Lê episodios/<ep>/thumbs/thumbs.json e renderiza cada variação em 1280x720 e 320x180."""
    texto, video = episodio(a.ep)
    pasta = texto / "thumbs"
    spec = json.loads((pasta / "thumbs.json").read_text())
    modelo = marca((TEMPLATES / "thumb.html").read_text())
    trab = video / "trabalho" / "thumbs"
    trab.mkdir(parents=True, exist_ok=True)
    jobs = []
    for v in spec["variacoes"]:
        img = Path(v["imagem"]).expanduser()
        if not img.is_absolute():
            img = video / "trabalho" / "frames" / img
        if not img.exists():
            sair(f"variação {v['id']}: não achei a imagem {img}")
        layout = v.get("layout", "A").upper()
        info = rostos([img])[0]
        rosto = maior_rosto(info)
        lado = v.get("lado") or ("esquerda" if rosto and rosto["x"] + rosto["w"] / 2 < 0.4 else "direita")
        largura_texto = 600
        palavras = re.sub(r"[*\n]", " ", v["frase"]).split()
        maior = max((len(p) for p in palavras), default=6)
        tamanho_fonte = v.get("tamanho") or max(72, min(128, int(largura_texto / (maior * 0.6))))
        fundos = ""
        if layout in ("A", "C"):
            rec = trab / f"recorte-{img.stem}.png"
            if not rec.exists() or rec.stat().st_mtime < img.stat().st_mtime:
                recortar(img, rec)
            imagem, estilo = (rec if layout == "C" else recorte_justo(rec)), (f"filter:{v['filtro']};" if v.get("filtro") else "")
            if layout == "C":
                lado = "centro"
                largura_texto = 1180
                tamanho_fonte = v.get("tamanho") or 104
                fs = [Path(f).expanduser() if Path(f).expanduser().is_absolute() else video / "trabalho" / "frames" / f
                      for f in v.get("fundos", [])]
                fundos = "".join(f'<img class="fundo f{i}" src="{f.as_uri()}" alt="">' for i, f in enumerate(fs, 1))
            elif v.get("fundo"):
                f = Path(v["fundo"]).expanduser()
                f = f if f.is_absolute() else video / "trabalho" / "frames" / f
                estilo_fundo = f' style="filter:{v["filtro_fundo"]}"' if v.get("filtro_fundo") else ""
                fundos = f'<img class="fundo-cena" src="{f.as_uri()}"{estilo_fundo} alt="">'
        else:
            # B: a cena inteira com zoom, empurrada pra o rosto cair do lado oposto ao painel
            iw, ih = info["largura"], info["altura"]
            zoom = v.get("zoom", 1.25)
            dh = 720 * zoom
            dw = max(iw / ih * dh, 1280 * zoom)
            dh = dw * ih / iw
            fx = (rosto["x"] + rosto["w"] / 2) if rosto else 0.5
            fy = (rosto["y"] + rosto["h"] / 2) if rosto else 0.4
            alvo_x = 0.72 * 1280 if lado == "direita" else 0.28 * 1280
            esq = min(0.0, max(1280 - dw, alvo_x - fx * dw))
            topo = min(0.0, max(720 - dh, 0.42 * 720 - fy * dh))
            imagem, estilo = img, (f"left:{esq:.0f}px;top:{topo:.0f}px;width:{dw:.0f}px;height:{dh:.0f}px;"
                                   + (f"filter:{v['filtro']};" if v.get("filtro") else ""))
        pagina = (modelo.replace("{{FONTES}}", FONTES.as_uri()).replace("{{CLASSES}}", f"{layout} {lado}")
                  .replace("{{IMAGEM}}", imagem.as_uri()).replace("{{IMG_ESTILO}}", estilo).replace("{{FUNDOS}}", fundos)
                  .replace("{{FRASE}}", frase_html(v["frase"])).replace("{{TAMANHO}}", str(tamanho_fonte))
                  .replace("{{LARGURA_TEXTO}}", str(largura_texto))
                  .replace("{{LARGURA_IMAGEM}}", str(v.get("largura_imagem") or 1280 - largura_texto - 60 - 40 - 24))
                  .replace("{{ALTURA_RECORTE}}", str(v.get("altura_recorte", 100))))
        h = pasta / f"thumb-{v['id']}.html"
        h.write_text(pagina)
        jobs.append({"html": str(h), "png": str(pasta / f"thumb-{v['id']}.png"), "largura": 1280, "altura": 720})
    renderizar(jobs, trab)
    ffmpeg = ferramenta("ffmpeg")
    for j in jobs:
        png = Path(j["png"])
        mini = png.with_name(png.stem + "-mini.png")
        rodar([ffmpeg, "-v", "error", "-y", "-i", png, "-vf", "scale=320:180:flags=lanczos", mini])
        nota = ""
        if png.stat().st_size > 2_000_000:
            jpg = png.with_suffix(".jpg")
            rodar([ffmpeg, "-v", "error", "-y", "-i", png, "-q:v", "2", jpg])
            nota = f" (passou de 2 MB: subir o {jpg.name})"
        print(f"{png}  {png.stat().st_size / 1e6:.1f} MB{nota}")
        print(mini)


# ---------------------------------------------------------------- cortes verticais

def ass_t(s: float) -> str:
    s = max(0.0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def limpar(p: str) -> str:
    return re.sub(r"[.,!?;:…\"“”()]", "", p.lower())


def escrever_ass(arq: Path, palavras: list[dict], destaques: list[str]) -> None:
    dest = {norm(d) for d in destaques}
    blocos, atual = [], []
    for w in palavras:
        if atual:
            junto = " ".join(limpar(x["p"]) for x in atual + [w])
            if (len(atual) >= 3 or len(junto) > 15 or w["i"] - atual[-1]["f"] > 0.35
                    or re.search(r"[.,!?;:…]$", atual[-1]["p"])):
                blocos.append(atual)
                atual = []
        atual.append(w)
    if atual:
        blocos.append(atual)
    eventos = []
    for k, b in enumerate(blocos):
        ini, fim = b[0]["i"], max(b[-1]["f"] + 0.12, b[0]["i"] + 0.3)
        if k + 1 < len(blocos):
            fim = min(fim, blocos[k + 1][0]["i"])
        txt = " ".join("{\\c&H00EFB686&}" + limpar(w["p"]) + "{\\r}" if norm(w["p"]) in dest else limpar(w["p"])
                       for w in b)
        eventos.append(f"Dialogue: 0,{ass_t(ini)},{ass_t(fim)},Legenda,,0,0,0,,{txt}")
    # Papel #F6F5F2, contorno Tinta #0B0B0B, destaque #86B6EF (ASS escreve a cor como &HAABBGGRR)
    arq.write_text("\n".join([
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0",
        "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
        "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        "Style: Legenda,Manrope ExtraBold,100,&H00F2F5F6,&H00F2F5F6,&H000B0B0B,&H000B0B0B,0,0,0,0,100,100,0,0,1,6,0,"
        "2,80,80,620,1", "",
        "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        *eventos, ""]))


def cmd_vertical(a):
    """Lê episodios/<ep>/cortes.json e gera cada corte 9:16 com legenda em cortes-instagram/."""
    texto, video = episodio(a.ep)
    transc = json.loads((texto / "transcricao.json").read_text())
    # Versão com motion: o corte sai da base dela (mesmo tempo), porque a cartela do 16:9 não cabe no 9:16
    retrato = texto / "versoes" / f"{transc['versao']}.json"
    origem = (json.loads(retrato.read_text()).get("base") if retrato.exists() else None) or transc["versao"]
    fonte = video / "editado" / f"{origem}.mp4"
    if not fonte.exists():
        sair(f"não achei {fonte} (a transcrição é da {transc['versao']})")
    cortes = json.loads((texto / "cortes.json").read_text())
    if a.so:
        cortes = [c for c in cortes if str(c["id"]) in a.so.split(",")]
    m = sondar(fonte)
    W, H = m["largura"], m["altura"]
    cw = int(round(H * 9 / 16 / 2)) * 2
    if H < 1920:
        print(f"atenção: fonte com {H} px de altura; o vertical vai sair ampliado e menos nítido (grave em 4K)")
    ffmpeg = ferramenta("ffmpeg")
    for c in cortes:
        ini, fim = ler_tempo(c["inicio"]), ler_tempo(c["fim"])
        d = fim - ini
        if d > 90 and not a.permitir_longo:
            print(f"corte {c['id']}: {d:.0f} s passa dos 90 s da API do Reels. Encurte ou use --permitir-longo")
            continue
        pasta = video / "trabalho" / "vertical" / f"c{int(c['id']):02d}"
        shutil.rmtree(pasta, ignore_errors=True)
        pasta.mkdir(parents=True)
        passo = max(1.0, d / 12)
        rodar([ffmpeg, "-v", "error", "-ss", f"{ini:.3f}", "-t", f"{d:.3f}", "-i", fonte,
               "-vf", f"fps=1/{passo:.3f},scale=960:-2", pasta / "q%02d.jpg"])
        achados = [maior_rosto(r) for r in rostos(sorted(str(p) for p in pasta.glob("q*.jpg")))]
        achados = [f for f in achados if f]
        cx = statistics.median(f["x"] + f["w"] / 2 for f in achados) if achados else 0.5
        if "centro_x" in c:
            cx = float(c["centro_x"])
        x = int(min(max(cx * W - cw / 2, 0), W - cw)) // 2 * 2
        trecho = [{"p": w["p"], "i": w["i"] - ini, "f": w["f"] - ini} for w in transc["palavras"]
                  if ini <= (w["i"] + w["f"]) / 2 < fim]
        escrever_ass(pasta / "legenda.ass", trecho, c.get("destaques", []))
        saida = video / "cortes-instagram" / f"corte-{int(c['id']):02d}.mp4"
        fade = 0.06
        vf = (f"crop={cw}:{H}:{x}:0,scale=1080:1920:flags=lanczos,setsar=1,fps=30,"
              f"subtitles=legenda.ass:fontsdir={FONTES}")
        rodar([ffmpeg, "-v", "error", "-y", "-ss", f"{ini:.3f}", "-t", f"{d:.3f}", "-i", fonte, "-vf", vf,
               "-af", f"afade=t=in:d={fade},afade=t=out:st={max(0.0, d - fade):.3f}:d={fade}",
               "-c:v", "h264_videotoolbox", "-b:v", "10M", "-profile:v", "high", "-pix_fmt", "yuv420p", "-g", "60",
               "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", saida],
              cwd=pasta)
        previa = pasta / "previa.jpg"
        rodar([ffmpeg, "-v", "error", "-y", "-ss", f"{d / 2:.2f}", "-i", saida, "-frames:v", "1",
               "-vf", "scale=540:-2", previa])
        sem = "" if achados else " (nenhum rosto achado: centro)"
        print(f"corte {c['id']}: {hms(d)} · rosto em {cx:.2f}{sem} · {saida}")
        print(f"  prévia: {previa}")


# ---------------------------------------------------------------- estado e limpeza

def cmd_estado(a):
    texto, video = episodio(a.ep)
    brutos = clipes_brutos(video)
    trab = video / "trabalho"
    transcritos = [p for p in brutos if (trab / f"{p.stem}.palavras.json").exists()]
    itens = [
        ("bruto", f"{len(brutos)} clipe(s), {tamanho(video / 'bruto') / 1e9:.1f} GB" if brutos else "vazio"),
        ("transcrição do bruto", f"{len(transcritos)}/{len(brutos)}" if brutos else "-"),
        ("plano de edição", "sim" if (texto / "plano-de-edicao.json").exists() else "não"),
        ("versões", ", ".join(versoes(video)) or "nenhuma"),
        ("transcrição final", json.loads((texto / "transcricao.json").read_text())["versao"]
         if (texto / "transcricao.json").exists() else "não"),
    ]
    for nome in ("motion.json", "titulos.md", "descricao.md", "cortes.json", "calendario.md"):
        itens.append((nome, "sim" if (texto / nome).exists() else "não"))
    thumbs = sorted((texto / "thumbs").glob("thumb-*[0-9].png")) if (texto / "thumbs").exists() else []
    itens.append(("thumbs", str(len(thumbs))))
    cortes = sorted((video / "cortes-instagram").glob("corte-*.mp4"))
    itens.append(("cortes verticais", str(len(cortes))))
    print(f"{a.ep}  (livre no Mac: {livre_gb():.1f} GB)")
    for nome, valor in itens:
        print(f"  {nome}: {valor}")


def cmd_apagar_bruto(a):
    texto, video = episodio(a.ep)
    alvos = [video / "bruto", video / "trabalho"] + ([video / "editado"] if a.tambem_editado else [])
    soltos = []
    if a.manter:
        # Aprovou (decisão de 09/10/2026): fica só a versão aprovada e a base dela (o corte vertical sai da base)
        if not (video / "editado" / f"{a.manter}.mp4").exists():
            sair(f"não achei editado/{a.manter}.mp4")
        retrato = texto / "versoes" / f"{a.manter}.json"
        base = json.loads(retrato.read_text()).get("base") if retrato.exists() else None
        fica = {a.manter, base}
        # sai toda versão que não ficou, inclusive a base interna do reel (editado/base.mp4)
        soltos = [p for p in (video / "editado").glob("*.mp4") if p.stem not in fica]
    total = (sum(tamanho(p) for p in alvos) + sum(p.stat().st_size for p in soltos)) / 1e9
    if not a.sim:
        print(f"apagaria {total:.1f} GB: " + ", ".join(str(p) for p in alvos + soltos))
        print("Só apaga com --sim, depois que ele aprovar. O texto do episódio (transcrição, versões) fica.")
        return
    for p in alvos:
        shutil.rmtree(p, ignore_errors=True)
        p.mkdir(parents=True, exist_ok=True)
    for p in soltos:
        p.unlink(missing_ok=True)
    print(f"apagado: {total:.1f} GB. Livre agora: {livre_gb():.1f} GB")


# ---------------------------------------------------------------- linha de comando

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("novo", help="cria a pasta de texto e a de vídeo de um episódio")
    s.add_argument("slug")
    s.add_argument("--data", help="AAAA-MM-DD (padrão: hoje)")
    s.set_defaults(f=cmd_novo)

    s = sub.add_parser("espaco", help="espaço livre e tamanho de cada episódio")
    s.set_defaults(f=cmd_espaco)

    s = sub.add_parser("ideias", help='puxa a nota "canal" do Notas pro inbox')
    s.add_argument("--criar", action="store_true", help="cria a nota se não existir")
    s.set_defaults(f=cmd_ideias)

    s = sub.add_parser("importar", help="move os vídeos do AirDrop (Downloads) pro bruto/")
    s.add_argument("ep")
    s.add_argument("arquivos", nargs="*")
    s.add_argument("--de", default="~/Downloads")
    s.set_defaults(f=cmd_importar)

    s = sub.add_parser("transcrever", help="transcreve cada clipe do bruto (palavra por palavra)")
    s.add_argument("ep")
    s.add_argument("--forcar", action="store_true")
    s.set_defaults(f=cmd_transcrever)

    s = sub.add_parser("plano", help="monta o plano de edição e a lista de cortes")
    s.add_argument("ep")
    s.add_argument("--refazer", action="store_true", help="recalcula do zero (perde ajuste à mão nos clipes)")
    s.add_argument("--so-lista", action="store_true", help="só reescreve a lista-de-cortes.md")
    s.set_defaults(f=cmd_plano)

    s = sub.add_parser("render", help="renderiza o plano em editado/vN.mp4")
    s.add_argument("ep")
    s.add_argument("--versao", help="vN (padrão: a próxima)")
    s.set_defaults(f=cmd_render)

    s = sub.add_parser("motion", help="cola as cartelas do HyperFrames (motion.json) por cima da versão")
    s.add_argument("ep")
    s.add_argument("--base", help="vN sem motion (padrão: a do motion.json)")
    s.add_argument("--versao", help="vN de saída (padrão: a próxima)")
    s.add_argument("--so", help="re-renderiza só estas cartelas (nomes separados por vírgula)")
    s.add_argument("--refazer", action="store_true", help="re-renderiza todas as cartelas")
    s.set_defaults(f=cmd_motion)

    s = sub.add_parser("transcricao", help="transcrição do vídeo final (.md, .srt, .json)")
    s.add_argument("ep")
    s.add_argument("--versao", help="vN (padrão: a última)")
    s.set_defaults(f=cmd_transcricao)

    s = sub.add_parser("folha", help="folha de quadros com o tempo de cada um, pra olhar o vídeo")
    s.add_argument("ep")
    s.add_argument("alvo", help="nome do clipe no bruto, ou vN")
    s.add_argument("--de")
    s.add_argument("--ate")
    s.add_argument("--passo", type=float, help="segundos entre quadros")
    s.add_argument("--quadros", type=int, default=24)
    s.set_defaults(f=cmd_folha)

    s = sub.add_parser("frame", help="tira um quadro em resolução cheia")
    s.add_argument("ep")
    s.add_argument("alvo")
    s.add_argument("tempo")
    s.add_argument("--nome")
    s.set_defaults(f=cmd_frame)

    s = sub.add_parser("recorte", help="tira o fundo de uma imagem (PNG transparente)")
    s.add_argument("entrada")
    s.add_argument("saida")
    s.set_defaults(f=cmd_recorte)

    s = sub.add_parser("thumbs", help="renderiza as thumbs de thumbs/thumbs.json")
    s.add_argument("ep")
    s.set_defaults(f=cmd_thumbs)

    s = sub.add_parser("vertical", help="gera os cortes 9:16 de cortes.json")
    s.add_argument("ep")
    s.add_argument("--so", help="ids separados por vírgula")
    s.add_argument("--permitir-longo", action="store_true", help="aceita corte com mais de 90 s")
    s.set_defaults(f=cmd_vertical)

    s = sub.add_parser("estado", help="o que já existe de um episódio")
    s.add_argument("ep")
    s.set_defaults(f=cmd_estado)

    s = sub.add_parser("apagar-bruto", help="apaga bruto e trabalho (só com --sim, depois que ele aprovou)")
    s.add_argument("ep")
    s.add_argument("--sim", action="store_true")
    s.add_argument("--manter", metavar="vN", help="versão aprovada: apaga também as outras versões")
    s.add_argument("--tambem-editado", action="store_true")
    s.set_defaults(f=cmd_apagar_bruto)

    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
