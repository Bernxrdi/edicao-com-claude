---
name: semana
description: >
  O maestro do dia de gravar: puxa o que chegou no grupo do WhatsApp (temas e referências) e no inbox, lê o que
  as referências novas fazem pra chamar atenção, faz a pauta (de 5 a 7 perguntas, respondidas por voz), a lista
  do que gravar (o vídeo do YouTube e os reels, cada um com o tipo e as perguntas pra câmera) e, com tudo gravado,
  encadeia a máquina sem parar: /editar-episodio, /pos-episodio, /multiplicar, até o calendário da semana
  seguinte, e mostra tudo pronto. Use quando chamarem /semana, ou disserem "bora a semana de conteúdo", "faz a
  pauta", "o que a gente grava hoje", "perguntas pra gravar", "fecha o conteúdo da semana", "calendário da semana".
---

# /semana · do grupo do WhatsApp ao calendário

Uma pasta por semana: `canal/semanas/<AAAA-MM-DD>/` (a data da segunda-feira), com `pauta.md` e `calendario.md`.
Antes de tudo: `perfil/quem-sou.md`, `perfil/como-falo.md`, `canal/formatos.md`.

## 1. Abrir a semana
Criar a pasta da semana. Tem `pauta.md` com `**Onde parou:**`: retomar dali.

## 2. Juntar (o robô já fez a maior parte)
- `canal/semanas/do-grupo.md`: o que chegou no grupo desde a última semana (o robô acrescenta a cada 30 min;
  se ele estiver desligado, `uv run canal/scripts/radar.py rodar` antes). O que já virou pauta tem `✓` na frente
- `canal/ideias/inbox.md` e, se a pessoa usa, `uv run canal/scripts/canal.py ideias` (a nota do iPhone)
Uma mensagem curta: quantos temas, quantas referências, o que se destaca.

## 3. As referências
Pra cada referência nova em vídeo (reel, short, vídeo do YouTube), no máximo 5 por semana: `yt-dlp` baixa
(Instagram pode pedir login: sem login, fica o título do link), o ffmpeg tira um quadro a cada 0,5 s dos 3
primeiros segundos e um a cada 2 s do resto, e o Claude escreve em `canal/semanas/<data>/referencias.md` o que faz
ela chamar atenção: o gancho dos 3 primeiros segundos, o ritmo dos cortes, como o texto entra, a câmera, a música.
É a gramática que dá pra usar, nunca o conteúdo pra copiar.

## 4. A pauta
Uma mensagem só, com **de 5 a 7 perguntas** curtas, numeradas, uma linha cada:
- **os temas do grupo:** a opinião da pessoa, o que viveu com aquilo, por que mandou
- **as ideias do inbox** que ainda não viraram vídeo
- **takes da semana** (vídeos que já chegaram no AirDrop): um questionário dirigido sobre eles (o que era, onde,
  por que gravou, o que quer contar). Antes, importar e transcrever pelo `/editar-episodio` e olhar uma folha por take
A pessoa responde por voz, do jeito que vier. Gravar em `pauta.md`: perguntas e respostas **nas palavras dela**,
sem polir. A `pauta.md` é a origem de todo fato da semana: número, horário e resultado só entram se estiverem lá.

## 5. A lista de gravação
Das respostas sai **o que gravar hoje** (padrão: 1 vídeo do YouTube + 2 ou 3 reels; o número que a pessoa
escolheu na entrevista manda). Cada item:
> **Peça** (YouTube ou reel) · **tipo** (`canal/formatos.md`) · **perguntas pra câmera** (de 3 a 5 no longo, 1
> por reel) · **como gravar** (cenário e enquadramento, tirados de uma referência do passo 3) · **tela** (se é
> explicativo sobre uma tela: gravar a tela também, sem senha nem dado de terceiros à vista)

Pergunta, nunca roteiro. Lembrete em uma linha: horizontal pro YouTube e em pé pro reel, 4K, olhando pra lente,
começa pela resposta, errou: a palavra de erro e repete. Guardar a lista na `pauta.md`. A pessoa grava e manda
por AirDrop. Marcar com `✓` no `do-grupo.md` os itens que viraram pauta.

## 6. A máquina (sem parar entre os passos)
Com os vídeos no AirDrop, encadear sem perguntar de novo. A lista de gravação vai junto: é ela que diz qual vídeo
é qual peça e de que tipo.
1. `/editar-episodio`: o YouTube e os reels da lista, cada um pela receita do tipo
2. `/pos-episodio`: 3 títulos, descrição, capítulos e as 3 thumbs
3. `/multiplicar`: completa os reels com cortes do longo, o story e as legendas
4. O calendário (passo 8)
Sessão que acabou no meio: escrever na `pauta.md` em que passo parou (`**Onde parou:**`).

## 7. A mesa (mostrar tudo pronto)
Uma mensagem só, com o caminho de cada coisa: o vídeo do YouTube (vN), os reels, as 3 thumbs numa imagem só, o
story e o calendário. A pessoa assiste e aprova, ou pede ajuste por texto (com o tempo da versão).

## 8. O calendário
A tabela do que posta em que dia na semana seguinte, YouTube e Instagram juntos, em `canal/semanas/<data>/calendario.md`:

| dia | hora | rede | peça | arquivo | legenda | status |
|---|---|---|---|---|---|---|

Legenda na voz da pessoa. Ritmo de partida: o vídeo e o story no mesmo dia, os reels em dias alternados. O que é
dela no fim, em lista curta: subir o YouTube com o pacote do `/pos-episodio` e agendar o Instagram.
