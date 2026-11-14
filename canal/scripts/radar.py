#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""O robô do grupo do WhatsApp: lê o grupo de criação de conteúdo e guarda o que chegou pro /semana.

Uso: uv run canal/scripts/radar.py <comando>   (rodar, instalar, desinstalar, estado)

Lê só o grupo do canal/radar.toml, só leitura, no banco do WhatsApp do Mac (o app precisa estar
instalado e logado). Puxa o título de cada link (X, YouTube, Instagram, site), separa referência
(vídeo, post, perfil, criativo) de tema (ideia, notícia) e acrescenta cada mensagem nova em
canal/semanas/do-grupo.md. Foto e vídeo mandados no grupo entram com o caminho do arquivo.

Não usa IA nem chave nenhuma: é só script. O que precisa de IA (ler a referência, fazer a pauta)
acontece na sessão do Claude Code, no /semana. Os dados do robô ficam em
~/.local/share/edicao-com-claude/radar/ (estado, entrada.json e log).
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import plistlib
import re
import shutil
import sqlite3
import subprocess
import tomllib
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "canal" / "radar.toml"
PILHA = RAIZ / "canal" / "semanas" / "do-grupo.md"
DADOS = Path.home() / ".local/share/edicao-com-claude/radar"
ESTADO = DADOS / "estado.json"
ENTRADA = DADOS / "entrada.json"
ROTULO = "com.edicao-com-claude.radar"
PLIST = Path.home() / f"Library/LaunchAgents/{ROTULO}.plist"
WHATSAPP = Path.home() / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
EPOCA_APPLE = dt.datetime(2001, 1, 1, tzinfo=dt.timezone.utc)
RAJADA = dt.timedelta(minutes=10)  # foto sem legenda vai junto da mensagem mandada perto dela
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")
CABECALHO = """\
<!-- quem escreve: canal/scripts/radar.py (só acrescenta embaixo). Quem lê: o /semana, no dia de gravar. -->
# O que chegou no grupo

> O robô acrescenta aqui cada mensagem nova do grupo do WhatsApp (canal/radar.toml), com o título dos
> links. "#ref" na mensagem marca referência; "#tema", tema. O /semana lê, faz a pauta e marca o que já usou.

"""

RE_URL = re.compile(r"https?://[^\s<>\"']+")
RE_X = re.compile(r"https?://(?:www\.|mobile\.)?(?:x|twitter)\.com/([^/?#]+)/status/(\d+)")
RE_YT = re.compile(r"https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch|shorts/)|youtu\.be/)")
# Link desses tipos é referência (o jeito de alguém fazer); o resto é tema (o assunto).
CLASSES = [
    ("ig_reel", re.compile(r"instagram\.com/(?:[^/?#]+/)?(?:reel|reels|tv)/([A-Za-z0-9_-]+)")),
    ("ig_post", re.compile(r"instagram\.com/(?:[^/?#]+/)?p/([A-Za-z0-9_-]+)")),
    ("ig_story", re.compile(r"instagram\.com/stories/([A-Za-z0-9._]+)")),
    ("ig_perfil", re.compile(r"instagram\.com/(?!explore|accounts|direct|about|legal|developer)([A-Za-z0-9._]{2,30})/?(?:[?#]|$)")),
    ("yt_video", re.compile(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/)|youtu\.be/)([A-Za-z0-9_-]{6,})")),
    ("yt_canal", re.compile(r"youtube\.com/(@[^/?#]+|channel/[^/?#]+|c/[^/?#]+|user/[^/?#]+)")),
    ("tiktok", re.compile(r"tiktok\.com/")),
    ("pinterest", re.compile(r"pin\.it/|pinterest\.[a-z.]+/pin/")),
    ("behance", re.compile(r"behance\.net/")),
    ("dribbble", re.compile(r"dribbble\.com/")),
]
REFERENCIA = {nome for nome, _ in CLASSES}


def classificar(url: str) -> str:
    for nome, padrao in CLASSES:
        if padrao.search(url):
            return nome
    return "x" if RE_X.match(url) else "site"


def agora() -> dt.datetime:
    return dt.datetime.now().astimezone()


def ler_json(caminho: Path, padrao):
    try:
        return json.loads(caminho.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def gravar_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1))


def curto(texto: str, n: int = 300) -> str:
    texto = re.sub(r"\s+", " ", texto or "").strip()
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def normalizar(nome: str) -> str:
    nome = unicodedata.normalize("NFC", nome).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[‐-―−]", "-", nome)).strip()


# ---------------------------------------------------------------- WhatsApp (só leitura)

def conectar() -> sqlite3.Connection:
    if not WHATSAPP.exists():
        raise LookupError("não achei o banco do WhatsApp do Mac (o app WhatsApp está instalado e logado?)")
    return sqlite3.connect(f"{WHATSAPP.as_uri()}?mode=ro", uri=True, timeout=10)


def achar_grupo(con: sqlite3.Connection, nome: str) -> int:
    grupos = con.execute(
        "SELECT Z_PK, ZPARTNERNAME FROM ZWACHATSESSION WHERE ZCONTACTJID LIKE '%@g.us' AND ZPARTNERNAME IS NOT NULL"
    ).fetchall()
    achados = [pk for pk, nome_grupo in grupos if normalizar(nome_grupo) == normalizar(nome)]
    if not achados:
        raise LookupError(f'grupo "{nome}" não achado no WhatsApp do Mac (o nome no radar.toml está igual ao do app?)')
    if len(achados) > 1:
        raise LookupError(f'mais de um grupo chamado "{nome}"; renomeia um deles')
    return achados[0]


def mensagens_do_grupo(nome: str, desde: dt.datetime) -> list[dict]:
    con = conectar()
    try:
        pk = achar_grupo(con, nome)
        linhas = con.execute(
            "SELECT Z_PK, ZMESSAGEDATE, ZTEXT FROM ZWAMESSAGE WHERE ZCHATSESSION = ? AND ZMESSAGEDATE >= ? "
            "AND ZMESSAGETYPE NOT IN (6, 10) AND ZTEXT IS NOT NULL AND trim(ZTEXT) != '' ORDER BY ZMESSAGEDATE",
            (pk, (desde - EPOCA_APPLE).total_seconds()),
        ).fetchall()
    finally:
        con.close()
    return [{"id": i, "quando": (EPOCA_APPLE + dt.timedelta(seconds=d)).astimezone().isoformat(), "texto": t}
            for i, d, t in linhas]


def midias_do_grupo(nome: str, desde: dt.datetime) -> list[dict]:
    """Foto, vídeo e arquivo mandados direto no grupo. Arquivo vazio = o WhatsApp do Mac ainda não baixou."""
    con = conectar()
    try:
        pk = achar_grupo(con, nome)
        msg = {c[1] for c in con.execute("PRAGMA table_info(ZWAMESSAGE)")}
        item = {c[1] for c in con.execute("PRAGMA table_info(ZWAMEDIAITEM)")}
        if "ZMEDIALOCALPATH" not in item:
            return []
        if "ZMEDIAITEM" in msg:
            juncao = "JOIN ZWAMEDIAITEM i ON i.Z_PK = m.ZMEDIAITEM"
        elif "ZMESSAGE" in item:
            juncao = "JOIN ZWAMEDIAITEM i ON i.ZMESSAGE = m.Z_PK"
        else:
            return []
        legenda = "i.ZTITLE" if "ZTITLE" in item else "NULL"
        linhas = con.execute(
            f"SELECT m.Z_PK, m.ZMESSAGEDATE, m.ZMESSAGETYPE, i.ZMEDIALOCALPATH, {legenda} FROM ZWAMESSAGE m {juncao} "
            "WHERE m.ZCHATSESSION = ? AND m.ZMESSAGEDATE >= ? AND m.ZMESSAGETYPE IN (1, 2, 8, 11) ORDER BY m.ZMESSAGEDATE",
            (pk, (desde - EPOCA_APPLE).total_seconds()),
        ).fetchall()
    finally:
        con.close()
    saida = []
    for i, d, tipo, caminho, titulo in linhas:
        arquivo = next((str(b / caminho) for b in (WHATSAPP.parent / "Message", WHATSAPP.parent)
                        if caminho and (b / caminho).is_file()), "")
        saida.append({"id": i, "quando": (EPOCA_APPLE + dt.timedelta(seconds=d)).astimezone().isoformat(),
                      "origem": {1: "imagem", 2: "video", 11: "video"}.get(tipo, "arquivo"),
                      "texto": titulo or "", "arquivo": arquivo})
    return saida


# ---------------------------------------------------------------- links

def baixar(url: str, limite: int = 400_000, timeout: int = 12) -> bytes:
    pedido = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"})
    with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
        return resposta.read(limite)


def meta(pagina: str, nome: str) -> str:
    nome = re.escape(nome)
    for padrao in (rf'<meta[^>]+(?:property|name)=["\']{nome}["\'][^>]*content=["\']([^"\']*)',
                   rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\']{nome}["\']'):
        if achado := re.search(padrao, pagina, re.I):
            return html.unescape(achado[1]).strip()
    return ""


def resolver_link(url: str, cache: dict) -> dict:
    """Título e texto do link: X pelo fxtwitter (post público), YouTube pelo oEmbed, o resto pelas meta tags.
    Erro não vai pro cache: tenta de novo na próxima rodada."""
    if url in cache:
        return cache[url]
    info = {"url": url}
    try:
        if achado := RE_X.match(url):
            post = json.loads(baixar(f"https://api.fxtwitter.com/{achado[1]}/status/{achado[2]}")).get("tweet") or {}
            autor = post.get("author") or {}
            info.update(titulo=f"{autor.get('name', '')} (@{autor.get('screen_name', achado[1])})", texto=post.get("text", ""))
        elif RE_YT.match(url):
            dados = json.loads(baixar("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")))
            info.update(titulo=dados.get("title", ""), texto=f"canal {dados.get('author_name', '')}")
        else:
            pagina = baixar(url).decode("utf-8", "ignore")
            titulo = meta(pagina, "og:title")
            if not titulo and (achado := re.search(r"<title[^>]*>(.*?)</title>", pagina, re.I | re.S)):
                titulo = html.unescape(achado[1]).strip()
            info.update(titulo=titulo, texto=meta(pagina, "og:description") or meta(pagina, "description"))
        cache[url] = info
    except Exception as erro:  # link fora do ar, bloqueado ou lento: fica só o endereço
        info["erro"] = curto(str(erro), 120)
    return info


# ---------------------------------------------------------------- a pilha do /semana

def itens_do_grupo(grupo: list[dict], midias: list[dict]) -> list[dict]:
    itens = []
    for m in grupo:
        links = [{"url": l["url"], "classe": classificar(l["url"]), "titulo": l.get("titulo", ""),
                  "resumo": curto(l.get("texto", ""))} for l in m["links"]]
        texto = m["texto"].casefold()
        forcado = "ref" if "#ref" in texto else "tema" if "#tema" in texto else ""
        ref = forcado == "ref" or (forcado != "tema" and any(l["classe"] in REFERENCIA for l in links))
        itens.append({"id": m["id"], "quando": m["quando"], "origem": "texto", "texto": m["texto"],
                      "arquivo": "", "links": links, "tipo": "referência" if ref else "tema"})
    for m in midias:
        tema = "#tema" in m["texto"].casefold()
        itens.append({**m, "links": [], "tipo": "tema" if tema else "referência"})
    itens.sort(key=lambda i: i["quando"])
    return itens


def sem_legenda(item: dict) -> bool:
    return item["origem"] != "texto" and not (item["texto"] or "").strip()


def item_md(item: dict) -> str:
    quando = dt.datetime.fromisoformat(item["quando"])
    linhas = [l.strip() for l in (item["texto"] or "").strip().splitlines() if l.strip()]
    nome = {"imagem": "foto", "video": "vídeo"}.get(item["origem"], item["origem"])
    if item["origem"] != "texto" and not linhas:
        linhas = [f"({nome} sem legenda)"]
    saida = [f"- **{quando:%d/%m/%Y %H:%M}** · {item['tipo']} · {linhas[0] if linhas else ''}"]
    saida += [f"  {l}" for l in linhas[1:]]
    for l in item.get("links", []):
        resumo = "" if l["classe"].startswith("ig_") else l.get("resumo", "")  # no Instagram o título já traz a legenda
        if partes := [curto(p, 220) for p in (l.get("titulo"), resumo) if p]:
            saida.append(f"  - link: {' · '.join(partes)}")
    if item["origem"] != "texto":
        saida.append(f"  - {nome}: `{item['arquivo']}`" if item["arquivo"]
                     else f"  - {nome}: o WhatsApp do Mac ainda não tinha baixado (abrir o grupo no Mac)")
    return "\n".join(saida) + "\n"


def guardar(itens: list[dict], estado: dict, momento: dt.datetime) -> int:
    """Acrescenta na pilha o que ainda não entrou. Foto sem legenda espera a rajada fechar."""
    feitos = set(estado.get("feitos", []))
    novos = 0
    PILHA.parent.mkdir(parents=True, exist_ok=True)
    if not PILHA.exists():
        PILHA.write_text(CABECALHO)
    with PILHA.open("a") as arquivo:
        for item in itens:
            if item["id"] in feitos:
                continue
            if sem_legenda(item) and momento - dt.datetime.fromisoformat(item["quando"]) < RAJADA:
                continue
            arquivo.write(item_md(item))
            feitos.add(item["id"])
            novos += 1
    if itens:  # o que saiu da janela de dias não volta mais
        menor = min(i["id"] for i in itens)
        feitos = {i for i in feitos if i >= menor}
    estado["feitos"] = sorted(feitos)
    return novos


# ---------------------------------------------------------------- comandos

def ler_config() -> dict:
    if not CONFIG.exists():
        raise SystemExit(f"falta o {CONFIG} (a /entrevista cria; o modelo é o radar.exemplo.toml)")
    return tomllib.loads(CONFIG.read_text())


def rodar(_: argparse.Namespace) -> None:
    cfg = ler_config()
    nome = cfg.get("grupo_whatsapp", "").strip()
    if not nome:
        raise SystemExit("grupo_whatsapp vazio no canal/radar.toml")
    estado = ler_json(ESTADO, {})
    cache = estado.setdefault("links", {})
    momento = agora()
    desde = momento - dt.timedelta(days=cfg.get("dias_grupo", 14))
    try:
        grupo = mensagens_do_grupo(nome, desde)
        for m in grupo:
            m["links"] = [resolver_link(u.rstrip(".,;:!?)]"), cache) for u in RE_URL.findall(m["texto"])]
        midias = midias_do_grupo(nome, desde)
    except (LookupError, sqlite3.Error) as erro:
        print(f"{momento:%d/%m %H:%M} WhatsApp: {erro}")
        if "unable to open" in str(erro) or "authorization" in str(erro).lower():
            print("  provável permissão do macOS: Ajustes > Privacidade e Segurança > Acesso Total ao Disco, ligar o uv")
        raise SystemExit(1)
    itens = itens_do_grupo(grupo, midias)
    gravar_json(ENTRADA, {"gerado": momento.isoformat(), "itens": itens})
    novos = guardar(itens, estado, momento)
    gravar_json(ESTADO, estado)
    refs = sum(i["tipo"] == "referência" for i in itens)
    print(f"{momento:%d/%m %H:%M} {len(itens)} no grupo · {novos} novos na pilha · {refs} referências · {PILHA}")


def instalar(_: argparse.Namespace) -> None:
    """Liga o robô no Mac: roda a cada `intervalo_minutos` do radar.toml (padrão 30) e no login."""
    cfg = ler_config()
    uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
    DADOS.mkdir(parents=True, exist_ok=True)
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    with PLIST.open("wb") as arquivo:
        plistlib.dump({
            "Label": ROTULO,
            "ProgramArguments": [uv, "run", "--quiet", "--script", str(Path(__file__).resolve()), "rodar"],
            "RunAtLoad": True,
            "StartInterval": int(cfg.get("intervalo_minutos", 30)) * 60,
            "EnvironmentVariables": {"PATH": f"{Path(uv).parent}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
                                     "HOME": str(Path.home())},
            "StandardOutPath": str(DADOS / "radar.log"),
            "StandardErrorPath": str(DADOS / "radar.log"),
        }, arquivo)
    dominio = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{dominio}/{ROTULO}"], capture_output=True)
    subprocess.run(["launchctl", "bootstrap", dominio, str(PLIST)], check=True)
    print(f"ligado: a cada {cfg.get('intervalo_minutos', 30)} min · log em {DADOS / 'radar.log'}")


def desinstalar(_: argparse.Namespace) -> None:
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{ROTULO}"], capture_output=True)
    PLIST.unlink(missing_ok=True)
    print("desligado")


def estado(_: argparse.Namespace) -> None:
    ligado = PLIST.exists()
    print(f"robô: {'ligado' if ligado else 'desligado'} · pilha: {PILHA}")
    log = DADOS / "radar.log"
    if log.exists():
        print("últimas rodadas:\n  " + "\n  ".join(log.read_text().strip().splitlines()[-5:]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("rodar", help="uma rodada: lê o grupo e acrescenta na pilha").set_defaults(funcao=rodar)
    sub.add_parser("instalar", help="liga o robô (a cada 30 min)").set_defaults(funcao=instalar)
    sub.add_parser("desinstalar", help="desliga o robô").set_defaults(funcao=desinstalar)
    sub.add_parser("estado", help="ligado ou não, e as últimas rodadas").set_defaults(funcao=estado)
    args = parser.parse_args()
    args.funcao(args)


if __name__ == "__main__":
    main()
