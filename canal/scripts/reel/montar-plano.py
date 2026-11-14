# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy"]
# ///
# Monta o plano-de-edicao.json de um reel a partir de episodios/<ep>/trechos.json: os trechos escolhidos
# (fora de ordem, quando a ideia pede), com as pontas e as pausas achadas pela energia do áudio (janelas de
# 20 ms), não pelo tempo do Whisper, e as gaguejadas e repetições tiradas de dentro ("tirar").
# Uso (da raiz): uv run canal/scripts/reel/montar-plano.py <ep>
#
# trechos.json: {"clipe": "IMG_0000.MOV", "trechos": [{"inicio": [a, b], "fim": [a, b], "tirar": [[x, y]], "nota": "..."}]}
#   inicio/fim = janela da emenda (do fim da palavra de antes ao começo da palavra de depois, no bruto);
#   tirar = pedaços de dentro do trecho que saem (gaguejada, "é...", palavra repetida), no tempo do bruto;
#   comeco = início fixo, no lugar da janela (pra deixar respiro de silêncio antes da fala).
# Sala com ruído perto de −35 dB (09/10/2026): o corte de silêncio do canal.py não acha pausa; o limiar daqui é −30 dB.
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "canal/scripts"))
import canal  # noqa: E402

DT = 0.01          # passo da energia
LIMIAR = -30.0     # dB: abaixo disso é pausa
PAUSA_MAX = 0.35   # pausa maior que isso dentro de um trecho encolhe
SOBRA = 0.10       # quanto de cada lado da pausa fica (a pausa vira 0,2 s)
ANTES, DEPOIS = 0.08, 0.12  # respiro antes da primeira palavra e depois da última


def energia(trab: Path, clipe: Path, m: dict) -> np.ndarray:
    """dB em janelas de 20 ms (passo de 10 ms) do áudio do clipe, guardado em trabalho/."""
    raw = trab / f"{clipe.stem}.16k.f32"
    if not raw.exists():
        subprocess.run([canal.ferramenta("ffmpeg"), "-v", "error", "-y", "-i", clipe, "-map", f"0:{m['audio']}",
                        "-ac", "1", "-ar", "16000", "-f", "f32le", raw], check=True)
    x = np.fromfile(raw, dtype=np.float32)
    jan = np.lib.stride_tricks.sliding_window_view(x, 320)[::160]
    return 20 * np.log10(np.sqrt((jan.astype(np.float64) ** 2).mean(1)) + 1e-9)


def idx(t: float) -> int:
    return int(round(t / DT))


def vale(db: np.ndarray, a: float, b: float) -> int:
    i, j = idx(a), max(idx(b), idx(a) + 1)
    return i + int(np.argmin(db[i:j]))


def inicio(db: np.ndarray, a: float, b: float) -> float:
    """Onde a fala começa: do ponto mais baixo da janela, o primeiro acima do limiar (por 60 ms)."""
    v = i = vale(db, a, b)
    while i < idx(b + 0.4) and not (db[i:i + 6] > LIMIAR).all():
        i += 1
    return round(max(v * DT, i * DT - ANTES), 3)


def fim(db: np.ndarray, a: float, b: float) -> float:
    """Onde a fala acaba: o primeiro ponto abaixo do limiar (por 150 ms) depois da palavra.
    Sem pausa clara na janela, o ponto mais baixo dela."""
    i = idx(a - 0.1)
    while i < idx(b):
        if (db[i:i + 15] < LIMIAR).all():
            return round(min(b, i * DT + DEPOIS), 3)
        i += 1
    return round(vale(db, a, b) * DT, 3)


def sem_pausas(db: np.ndarray, a: float, b: float) -> list[list[float]]:
    """Divide [a, b] tirando o miolo das pausas longas."""
    partes, ini, i, fim_i = [], a, idx(a + 0.15), idx(b - 0.15)
    while i < fim_i:
        if db[i] < LIMIAR:
            j = i
            while j < fim_i and db[j] < LIMIAR:
                j += 1
            if (j - i) * DT > PAUSA_MAX:
                partes.append([ini, round(i * DT + SOBRA, 3)])
                ini = round(j * DT - SOBRA, 3)
            i = j
        i += 1
    partes.append([ini, b])
    return [[round(x, 3), round(y, 3)] for x, y in partes if y - x >= 0.12]


def tira(partes: list[list[float]], fora: list[list[float]]) -> list[list[float]]:
    for x0, y0 in fora:
        novas = []
        for x, y in partes:
            if y <= x0 or x >= y0:
                novas.append([x, y])
                continue
            if x < x0:
                novas.append([x, x0])
            if y > y0:
                novas.append([y0, y])
        partes = novas
    return [[round(x, 3), round(y, 3)] for x, y in partes if y - x >= 0.12]


def main():
    ep = sys.argv[1]
    texto, video = canal.episodio(ep)
    cfg = json.loads((texto / "trechos.json").read_text())
    clipe_nome = cfg["clipe"]
    trab = video / "trabalho"
    meta = json.loads((trab / "clipes.json").read_text())
    m = meta[clipe_nome]
    db = energia(trab, video / "bruto" / clipe_nome, m)
    clipes = []
    for t in cfg["trechos"]:
        # "comeco": início fixo (pra deixar um respiro de silêncio da própria sala antes da fala)
        a, b = (t["comeco"] if "comeco" in t else inicio(db, *t["inicio"])), fim(db, *t["fim"])
        clipes.append({"arquivo": clipe_nome, "tipo": "fala", "usar": True, "duracao": m["duracao"],
                       "trechos": tira(sem_pausas(db, a, b), t.get("tirar", [])), "erros": [], "nota": t["nota"]})
    plano = {"episodio": ep, "gerado": canal.agora(), "parametros": dict(canal.PARAMETROS_PADRAO),
             # 1224x2176: folga pro punch-in no reel de 1080x1920 sem perder nitidez
             "saida": {"largura": 1224, "altura": 2176, "fps": 30}, "musica": cfg.get("musica"), "clipes": clipes,
             "nota": "Reel 9:16. Montado por scripts/reel/montar-plano.py a partir de trechos.json"}
    (texto / "plano-de-edicao.json").write_text(json.dumps(plano, indent=2, ensure_ascii=False))
    total = sum(y - x for c in clipes for x, y in c["trechos"])
    print(f"{len(clipes)} blocos, {sum(len(c['trechos']) for c in clipes)} trechos, {canal.hms(total, True)} no total")
    for c in clipes:
        t = c["trechos"]
        print(f"  {sum(y - x for x, y in t):5.1f} s  {t[0][0]:7.2f}-{t[-1][1]:7.2f}  {len(t)} parte(s)  {c['nota'][:60]}")


if __name__ == "__main__":
    main()
