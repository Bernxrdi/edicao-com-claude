# A biblioteca de música liberada, por clima (canal/formatos.md, "Música"): o editor escolhe sozinho pelo
# tipo do vídeo, sem repetir faixa na mesma semana. Fonte: Mixkit (Mixkit Stock Music Free License: redes e
# anúncio, sem crédito). Música famosa nunca entra aqui (o Rights Manager e o Content ID derrubam).
# Uso (da raiz):
#   python3 canal/scripts/reel/biblioteca-musica.py baixar [--por-clima 10]   # uma vez, e pra renovar
#   python3 canal/scripts/reel/biblioteca-musica.py escolher <clima|tipo> --ep <ep>
#       imprime o JSON pro "musica" do plano-de-edicao.json e marca a faixa como usada
#   python3 canal/scripts/reel/biblioteca-musica.py lista
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit import VIDEOS, marca  # noqa: E402

BIB = VIDEOS / "_musicas" / "biblioteca"
INDICE = BIB / "indice.json"
USADAS = BIB / "usadas.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

# Clima: (páginas da Mixkit, quanto abaixo da voz a música fica, em dB). Ajuste dele entra aqui e no formatos.md.
CLIMAS = {
    "animada": (["discover/young", "dance-pop", "hip-hop"], 16),
    "energia": (["mood/energetic", "edm", "drum-and-bass"], 16),
    "discreta": (["ambient", "easy-listening"], 20),
    "lofi": (["chillout", "downtempo"], 20),
    "corporativa": (["corporate-music"], 20),
}
TIPO = {"lifestyle": "animada", "treino": "energia", "fala": "discreta", "explicativo": "lofi", "produto": "corporativa"}


def ler(caminho: Path, padrao):
    try:
        return json.loads(caminho.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def pagina(slug: str) -> list[dict]:
    pedido = urllib.request.Request(f"https://mixkit.co/free-stock-music/{slug}/", headers={"User-Agent": UA})
    html = urllib.request.urlopen(pedido, timeout=30).read().decode("utf-8", "ignore")
    faixas = []
    for bloco in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            dado = json.loads(bloco)
        except json.JSONDecodeError:
            continue
        for g in dado.get("@graph", []):
            for f in g.get("itemListElement", []) if g.get("@type") == "ItemList" else []:
                if f.get("url", "").endswith(".mp3"):
                    m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", f.get("duration", "")) or None
                    seg = (int(m[1] or 0) * 60 + int(m[2] or 0)) if m else 0
                    faixas.append({"titulo": f.get("name", ""), "artista": f.get("byArtist", ""), "url": f["url"],
                                   "segundos": seg, "genero": f.get("genre", ""), "licenca": f.get("copyrightNotice", "")})
    return faixas


def baixar(a: argparse.Namespace) -> None:
    indice = ler(INDICE, {})
    for clima, (slugs, _) in CLIMAS.items():
        destino = BIB / clima
        destino.mkdir(parents=True, exist_ok=True)
        ja = {f["url"] for f in indice.get(clima, [])}
        candidatas = []
        for slug in slugs:
            try:
                candidatas += [f for f in pagina(slug) if f["url"] not in ja and f["segundos"] >= 60]
            except Exception as erro:
                print(f"  {clima}/{slug}: não abriu ({str(erro)[:80]})")
        vistas, novas = set(), []
        for f in candidatas:
            if f["url"] not in vistas:
                vistas.add(f["url"])
                novas.append(f)
        falta = max(0, a.por_clima - len(indice.get(clima, [])))
        for f in novas[:falta]:
            nome = re.sub(r"[^a-z0-9]+", "-", f["titulo"].lower()).strip("-") or "faixa"
            arq = destino / f"{f['url'].split('/')[-1].split('.')[0]}-{nome}.mp3"
            try:
                pedido = urllib.request.Request(f["url"], headers={"User-Agent": UA})
                arq.write_bytes(urllib.request.urlopen(pedido, timeout=60).read())
            except Exception:
                continue
            indice.setdefault(clima, []).append({**f, "arquivo": str(arq)})
        print(f"{clima}: {len(indice.get(clima, []))} faixas")
    BIB.mkdir(parents=True, exist_ok=True)
    INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=1))


def escolher(a: argparse.Namespace) -> None:
    clima = TIPO.get(a.clima, a.clima)
    if clima not in CLIMAS:
        sys.exit(f"clima desconhecido: {a.clima} (tem: {', '.join(CLIMAS)}; ou o tipo: {', '.join(TIPO)})")
    faixas = [f for f in ler(INDICE, {}).get(clima, []) if Path(f["arquivo"]).exists()]
    if not faixas:
        sys.exit(f"a biblioteca de {clima} está vazia: rodar 'baixar' primeiro")
    usadas = ler(USADAS, [])
    semana = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    recentes = {u["arquivo"] for u in usadas if u["dia"] >= semana}
    livres = [f for f in faixas if f["arquivo"] not in recentes] or faixas
    f = random.choice(livres)
    usadas.append({"dia": dt.date.today().isoformat(), "arquivo": f["arquivo"], "ep": a.ep or ""})
    USADAS.write_text(json.dumps(usadas[-200:], ensure_ascii=False, indent=1))
    print(json.dumps({"arquivo": f["arquivo"], "abaixo_db": CLIMAS[clima][1], "inicio": 0, "clima": clima,
                      "volume": 0.15 if CLIMAS[clima][1] <= 16 else 0.10,  # o render do longo (canal.py) usa este
                      "titulo": f"{f['titulo']} ({f['artista']}, Mixkit)"}, ensure_ascii=False))


def lista(_: argparse.Namespace) -> None:
    indice = ler(INDICE, {})
    for clima in CLIMAS:
        nomes = [f["titulo"] for f in indice.get(clima, [])]
        print(f"{clima} ({len(nomes)}): {', '.join(nomes[:10])}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="comando", required=True)
    b = sub.add_parser("baixar")
    b.add_argument("--por-clima", type=int, default=10)
    b.set_defaults(funcao=baixar)
    e = sub.add_parser("escolher")
    e.add_argument("clima", help="o clima, ou o tipo do vídeo (lifestyle, treino, fala, explicativo, produto)")
    e.add_argument("--ep", help="o episódio que vai usar")
    e.set_defaults(funcao=escolher)
    sub.add_parser("lista").set_defaults(funcao=lista)
    a = ap.parse_args()
    a.funcao(a)


if __name__ == "__main__":
    main()
