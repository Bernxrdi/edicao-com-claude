---
name: multiplicar
description: >
  Transforma o vídeo do YouTube aprovado na semana do Instagram (ou TikTok, ou Shorts): escolhe os cortes que
  faltam pra fechar os reels da semana (e diz por quê), gera os verticais 9:16 com legenda queimada, faz o story
  e monta o calendário da semana com as legendas. Use quando chamarem /multiplicar, ou disserem "faz os cortes",
  "cortes pro instagram", "reels do vídeo", "semana do instagram", "calendário da semana", "fecha a semana".
---

# /multiplicar · do vídeo longo pra semana

Comandos da raiz com `uv run canal/scripts/canal.py <comando>` (abaixo, só `canal.py`). Antes de tudo, ler
`canal/contexto/padroes-cortes.md`, `canal/contexto/aprendizados.md` e `perfil/como-falo.md`. Precisa da
`transcricao.json` do `/pos-episodio`.

## Passo 1 · Escolher os cortes
**O teto da semana conta os reels que vieram da lista de gravação** (padrão: 3 no total). Já tem: nenhum corte,
segue pro story. Vlog de lifestyle não gera corte (o vlog vale inteiro). Senão, ler `transcricao.md` e escolher
só os que faltam:
- **até 90 s**, uma ideia só
- **começa no gancho**, sem precisar de contexto do vídeo longo
- **termina na frase-soco**

Escrever `canal/episodios/<ep>/cortes.json`, com os tempos tirados de `transcricao.json` (início da primeira
palavra menos 0,1 s; fim da última mais 0,3 s):
```json
[{"id": 1, "inicio": 12.4, "fim": 71.9, "gancho": "<primeira frase>",
  "porque": "<por que se sustenta sozinho>", "destaques": ["<palavra-chave>"],
  "legenda": "<texto do post>"}]
```
Uma palavra-chave por corte (no máximo duas), que aparece na cor de destaque na legenda queimada.

## Passo 2 · Gerar e conferir
`canal.py vertical <ep>` gera `<pasta dos vídeos>/<ep>/cortes-instagram/corte-NN.mp4` com o rosto centralizado
sozinho. Juntar as prévias (`trabalho/vertical/cNN/previa.jpg`) numa imagem e ler: rosto inteiro no quadro,
legenda legível. Rosto fora: pôr `"centro_x": 0.0 a 1.0` no corte e rodar `canal.py vertical <ep> --so <id>`.

## Passo 3 · Story
Um quadro do vídeo (`canal.py frame <ep> vN <tempo>`) com uma frase convidando pro vídeo novo, 1080x1920, tema
escuro, nas cores do `config.json`. Dá pra montar no motor do `/motion` (um still) ou no app da pessoa. O link do
YouTube entra pelo adesivo de link, que a pessoa põe no próprio Instagram.

## Passo 4 · Legendas e calendário
- Legenda de cada post na voz da pessoa (`perfil/como-falo.md`), com convite pro vídeo completo. Reler contra o
  perfil: sem cara de IA
- `canal/episodios/<ep>/calendario.md`: tabela com dia, hora, rede, peça, arquivo e legenda pronta (ritmo no
  `padroes-cortes.md`). No `/semana`, esta tabela entra no calendário único da semana. Hora só se confirmada;
  senão, "a definir"

## Passo 5 · Entregar
Lista do que saiu e como postar: AirDrop dos cortes de `cortes-instagram/` pro iPhone, agendar no próprio app
(conta profissional) colando a legenda do `calendario.md`.

## Passo 6 · Fechar
O bruto e as versões já saíram na aprovação (`/editar-episodio`, passo 8). O vídeo final só sai se pedirem
(`canal.py apagar-bruto <ep> --sim --tambem-editado`). Os cortes e o texto do episódio ficam.
