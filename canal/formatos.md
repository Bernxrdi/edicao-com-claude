<!-- quem lê: /editar-episodio (antes do plano), /motion, /musica, /multiplicar e /semana (na lista de gravação).
     A /entrevista ajusta os tipos ao que a pessoa posta. Ajuste que ela pedir entra aqui, datado, e em contexto/aprendizados.md. -->
# Formatos · a receita de cada tipo de vídeo

> Antes de cortar, o editor dá um tipo a cada peça, e a receita do tipo decide motion, mockup, música e
> legenda. A pessoa troca com uma palavra ("esse é explicativo"). Os tipos abaixo são o ponto de partida:
> a `/entrevista` tira o que ela não faz e acrescenta o que faz.

## Os tipos

| tipo | como reconhecer (pauta e transcrição) | motion | mockup | música (clima) | legenda |
|---|---|---|---|---|---|
| **lifestyle** | rotina, casa, rua, viagem, comida; mais cena que fala | só a tela de hora entre as cenas e o "se inscreve" da abertura | não | **animada** nas cenas e na abertura; nunca por baixo de fala longa | no YouTube, o .srt (sem legenda queimada) |
| **treino** | academia, luta, esporte; o corpo em ação | não | não | **energia** | só onde tem fala |
| **fala** | opinião, aprendizado, uma ideia dita pra câmera, sem passo a passo | não (no máximo o fecho) | não | **discreta**: instrumental baixo | queimada, palavra-chave na cor de destaque |
| **explicativo** | como faz, passo a passo, número, comparação, ferramenta | **sim, nos picos** | só se a fala é sobre uma tela | **lofi** baixo | queimada, palavra-chave na cor de destaque |
| **produto** | um app, serviço ou produto da pessoa em uso | sim (modo B do `/motion`) | **sim, sempre**: a tela real num celular ou notebook | **corporativa** leve | queimada |

Peça que mistura vale pelo tipo da maior parte; um trecho explicativo dentro de um vlog ganha motion só nele.
O tipo vai escrito no `plano-de-edicao.json` (`"tipo"`) e na lista de gravação do `/semana`.

## O vlog (lifestyle longo): a receita que já funcionou

- **Duração:** o que dá o tempo é a fala (todo o material gravado), não esticar o edit
- **Ordem:** a ordem do dia, com a tela preta da hora entre as cenas (`templates/motion/hora.html`,
  `scripts/cartelas-hora.py`)
- **Abertura (~13 s):** cenas do dia em ordem, o corte acelerando (4, 2 e 1 batida) até o drop da música; no
  drop, o motion do canal por cima de uma cena desfocada (`templates/motion/intro-canal.html`,
  `scripts/motion-sobre.py`): foto, nome, @, os temas e o "se inscreve" virando "inscrito"
- **Falas:** tomada longa. Sai só pausa de 0,9 s ou mais, recomeço, o que a pessoa mandou cortar e dado que
  não pode aparecer; punch-in só na emenda de um pedaço tirado. Nada de imagem por cima da fala
- **Treino dentro do vlog:** um bloco por exercício (15 a 20 s), abrindo com uma rajada de cortes de 1 batida
  e seguindo com tomadas de 4 a 8 batidas e câmera lenta de 0,5x; só take com movimento (`scripts/movimento.py`
  mede antes); barras 2,39:1; nada de take parado olhando pra câmera
- **Fim:** o motion do canal e do Instagram (`templates/motion/fim-canal.html`), com o lado direito livre pra
  tela final do YouTube
- **Cor:** a de cinema leve (`"acabamento"` no plano)

## Motion: quando entra

- Só nos picos: o número, a lista, o antes e depois, o passo que precisa ser visto. De 1 a 3 cenas por reel;
  no longo, de 3 a 6 no episódio inteiro
- Não entra no gancho falado (o rosto segura), em opinião, em história, em cena de rotina
- Sempre **cena cheia**: a tela inteira vira a animação e volta pro rosto. Nunca caixa de texto por cima do rosto

## Mockup: quando entra

- Só quando a fala é **sobre uma tela**: um app, um site, o Claude Code. O mockup mostra a tela de verdade
  (gravação de tela ou print real) num celular ou notebook
- Explicação de ideia, número ou conceito não leva mockup: leva tipografia e número em cena cheia
- Tela com dado de outra pessoa, de cliente ou da empresa onde a pessoa trabalha: não entra. Chave, token,
  senha e e-mail borrados antes de entrar; não deu pra borrar, grava de novo

## O acabamento (padrão Apple, sem copiar a Apple)

- **Aparelho realista:** moldura fiel, reflexo leve no vidro, sombra de contato suave, inclinação 3D pequena
- **Movimento com mola**, sem quique de desenho animado; entrada com desfoque que some; saída mais rápida que a entrada
- **Respiro:** uma ideia por cena, tipografia grande, peso fino contra grosso, muito espaço vazio
- **Luz e profundidade:** fundo neutro com um degradê de luz no mesmo tom (nunca colorido), grão leve
- **Uma cor de destaque**, a da marca (`canal/config.json`)
- **No tempo da fala:** cada elemento entra na palavra

## Música

- **Entra sozinha**, pelo clima do tipo, da biblioteca liberada (`scripts/reel/biblioteca-musica.py`, Mixkit:
  redes e anúncio, sem crédito). Não repete faixa na mesma semana; a escolhida fica no `musica` do plano
- **Música famosa não vai dentro do arquivo** do Reels: o Rights Manager da Meta corta o som ou derruba o
  post. Se a pessoa quiser uma, o reel sai sem música e o calendário diz qual pôr pelo app do Instagram e em
  que volume. No YouTube, só se ela pedir e aceitar o Content ID
- A voz passa pelo `/voz` antes da música

## O que sai de cada semana

- **1 vídeo do YouTube + 2 ou 3 reels**, não mais (a `/entrevista` pode mudar). O total já conta os cortes do
  longo: o `/multiplicar` só corta o que faltar
- Cada reel: uma ideia, de 30 s a 90 s, começa no gancho, fecha na frase-soco
- Thumbs do YouTube saem sozinhas (3, pelo `/pos-episodio`)
