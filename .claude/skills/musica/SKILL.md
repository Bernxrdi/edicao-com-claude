---
name: musica
description: >
  Música dos vídeos e reels: escolhe pela biblioteca liberada (Mixkit) no clima do tipo do vídeo, faz prévias no
  próprio vídeo pra pessoa escolher de ouvido, pesquisa o áudio em alta no Reels pro assunto e diz qual pôr pelo
  app e em que volume. Nunca baixa música protegida pra colar no vídeo. Use quando chamarem /musica, ou disserem
  "música pro reel", "qual música eu ponho", "áudio em alta", "trend de áudio", "põe uma música", "troca a
  música", "música de fundo", "trilha do vídeo".
---

# /musica · a música dos vídeos

O que pode e o que não pode, com as fontes: `canal/contexto/musicas.md`. Ler antes.

## Os dois caminhos
- **Dentro do arquivo:** só música liberada (Mixkit, Incompetech com crédito). É o padrão: o editor já escolhe
  sozinho pelo clima do tipo (`canal/formatos.md`)
- **Pelo app do Instagram:** o áudio em alta ou a música famosa que a pessoa quer. O reel sai sem música e o
  calendário diz qual áudio pôr e em que volume (voz 100, música de 5 a 15)

## A biblioteca liberada
`python3 canal/scripts/reel/biblioteca-musica.py`:
- `baixar [--por-clima 10]`: baixa a biblioteca (a `/entrevista` roda uma vez; rodar de novo pra renovar)
- `lista`: o que tem, por clima (animada, energia, discreta, lofi, corporativa)
- `escolher <clima|tipo> --ep <ep>`: devolve o JSON pro `"musica"` do `plano-de-edicao.json` e marca a faixa como
  usada (não repete na semana)

## Trocar a música de um vídeo pronto
1. Prévias no próprio vídeo, com a voz: `python3 canal/scripts/reel/previas-musica.py <ep> <vN> <musica1.mp3> [...]`
   (cada uma calibrada abaixo da voz). Mandar os caminhos e a pessoa escolhe de ouvido
2. A escolhida vai pro `"musica"` do plano e o definitivo sai de novo (`/editar-episodio`, passo 4)
3. Registrar em `canal/contexto/musicas.md`, "Usadas"

## Áudio em alta (quando pedirem)
Pesquisar na web o que está em alta no Reels pro assunto do vídeo, com a data e a fonte de cada um (lista com
mais de 2 semanas está velha). Devolver 3 opções, cada uma com por que combina e como usar no app.

## Regras
- Música protegida nunca entra no arquivo do reel. No YouTube, só se a pessoa pedir e aceitar o Content ID
- Nunca gerar trilha por IA no lugar da escolha da pessoa
- Instrumental por baixo de fala; música com vocal só em cena sem fala
