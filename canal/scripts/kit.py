"""A configuração do kit: lê canal/config.json, que a /entrevista escreve. Sem ele, valem os exemplos.

Os scripts importam daqui a pasta dos vídeos (VIDEOS) e a marca (marca(), que troca nos modelos HTML
o nome, o @ e as três cores de exemplo pelas de quem usa o kit). Roda no Python 3.9 do Mac.
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CANAL = RAIZ / "canal"
ARQUIVO = CANAL / "config.json"

PADRAO = {
    "nome": "seu nome",
    "arroba": "@seuperfil",
    "pasta_videos": "~/Movies/edicao-com-claude",
    "palavra_erro": "pato amarelo",
    "temas": ["vida", "trabalho", "ideias"],
    "cores": {"fundo": "#0B0B0B", "texto": "#F6F5F2", "destaque": "#86B6EF"},
}


def config() -> dict:
    c = json.loads(json.dumps(PADRAO))
    if ARQUIVO.exists():
        for chave, valor in json.loads(ARQUIVO.read_text()).items():
            if isinstance(valor, dict) and isinstance(c.get(chave), dict):
                c[chave].update(valor)
            else:
                c[chave] = valor
    return c


CFG = config()
VIDEOS = Path(CFG["pasta_videos"]).expanduser()

# As cores de exemplo que os modelos trazem escritas, e a chave do config que entra no lugar de cada uma.
_CORES = {"#86B6EF": "destaque", "#86b6ef": "destaque", "#F6F5F2": "texto", "#f6f5f2": "texto",
          "#0B0B0B": "fundo", "#0b0b0b": "fundo"}


def marca(html: str) -> str:
    """O modelo HTML com o nome, o @ e as cores de quem usa o kit."""
    for hexa, chave in _CORES.items():
        html = html.replace(hexa, CFG["cores"][chave])
    arroba = CFG["arroba"] if CFG["arroba"].startswith("@") else "@" + CFG["arroba"]
    return (html.replace("__NOME__", CFG["nome"]).replace("__ARROBA_MAIUSC__", arroba.upper())
            .replace("__ARROBA__", arroba).replace("__TEMAS__", json.dumps(CFG["temas"], ensure_ascii=False)))


def node_bin() -> Path:
    """A pasta do node: a versão mais nova do nvm, senão o node do PATH, senão o do Homebrew."""
    import shutil
    nvm = sorted((Path.home() / ".nvm" / "versions" / "node").glob("v*/bin/node"),
                 key=lambda p: [int(x) for x in p.parts[-3][1:].split(".")])
    if nvm:
        return nvm[-1].parent
    achado = shutil.which("node")
    if achado:
        return Path(achado).parent
    for pasta in (Path("/opt/homebrew/bin"), Path("/usr/local/bin")):
        if (pasta / "node").exists():
            return pasta
    raise SystemExit("não achei o node (rode ./instalar.sh na raiz do kit)")


def playwright_core() -> Path:
    """O playwright-core que o ./instalar.sh deixou no cache do npx (a versão mais nova)."""
    achados = list((Path.home() / ".npm" / "_npx").glob("*/node_modules/playwright-core"))
    if not achados:
        raise SystemExit("não achei o playwright-core (rode ./instalar.sh na raiz do kit)")
    versao = lambda p: [int(x) for x in json.loads((p / "package.json").read_text())["version"].split(".")[:3]]
    return max(achados, key=versao)
