---
name: motion
description: >
  Vídeo com animação (motion graphics) escrito em código: o Claude escreve a animação em HTML e ela vira vídeo
  pelo HyperFrames (peça com vídeo dentro) ou pelo motor próprio (uma página que pinta cada quadro, pra peça só de
  desenho, print e texto), com lista de estados antes do código, molas, som na batida e crítica com nota antes de
  entregar. Três modos: (A) animação dentro do vídeo falado (número, frase, fechamento, na palavra certa); (B)
  vídeo de produto com o app ou site em movimento; (C) reel curto de marca, abertura, apresentação. Use quando
  chamarem /motion, ou disserem "motion", "anima isso", "animação no vídeo", "motion graphics", "vídeo do app",
  "vídeo de anúncio", "abertura do vídeo", "apresentação em motion", "HyperFrames".
---

# /motion · vídeo com animação em código

*(Método a partir das aulas do Felipe Borges no canal Fala IA! ("Opus Mudou a Edição de Vídeo Para Sempre",
01/10/2026, e "Como Fazer Motion Graphics INSANOS", 06/10/2026) e do artigo que a segunda segue, "How to build
motion design studio", do @0xMovez no X.)*

**A ideia que manda em tudo:** o prompt é 10% do vídeo. Os outros 90% são o estúdio em volta dele: as regras
(esta skill), a marca (`perfil/marca.md` e `canal/config.json`), a referência, a lista de estados antes do código
e a crítica do próprio quadro. O Claude não gera vídeo: escreve um programa, e o programa vira vídeo.

## Os dois motores

| motor | quando | por quê |
|---|---|---|
| **HyperFrames** | animação dentro do vídeo falado (modo A) e qualquer peça com **vídeo dentro** (o rosto, gravação de tela) | cuida da mídia (vídeo, legenda, fundo transparente) e já está ligado ao `canal.py` e ao reel |
| **Motor próprio** (`canal/templates/motion/motor/`) | peça **só de desenho, print e texto**: modo B com prints, modo C | mola de verdade e desfoque de movimento nativos; sem as armadilhas do HyperFrames |

- **HyperFrames** (HeyGen, código aberto, Apache 2.0, grátis, sem conta): uma composição é um HTML com GSAP, os
  atributos `data-*` dizem quando cada coisa aparece, e o render é local (Chrome sem janela + ffmpeg). Entra como
  plugin do Claude Code (o `./instalar.sh` liga). As skills dele são a referência técnica, lidas sob demanda:
  `/hyperframes-core` (o contrato da composição, ler antes de escrever HTML), `/hyperframes-animation`,
  `/hyperframes-keyframes` (zoom, punch-in, câmera), `/hyperframes-cli` (check, render)
- **Motor próprio:** o filme é um `index.html` que pinta o quadro `t` (`window.seek(t)`), o `render.mjs` anda no
  tempo pelo Playwright e o ffmpeg junta, com subquadros pro desfoque de movimento. Junto: `motion.js` (molas),
  `beats.py` (grade de batidas), `sfx.mjs` (sons de interface), `motor.py` (folhas, mixagem, saída pra web),
  `critica.md` e `briefs.md`. Como usar: o `README.md` da pasta. **Com o motor próprio, não carregar as skills
  do HyperFrames** (elas se dizem obrigatórias pra qualquer vídeo; aqui não são)
- Node e Playwright: `PATH="$(python3 -c 'import sys;sys.path.insert(0,"canal/scripts");import kit;print(kit.node_bin())'):$PATH"`
  e `PLAYWRIGHT_CORE=$(ls -d ~/.npm/_npx/*/node_modules/playwright-core | head -1)`. No canal, o `canal.py motion` já resolve

## Onde mora
O projeto (HTML, roteiro, beats) em `canal/episodios/<ep>/motion-fonte/` (peça do canal) ou
`canal/conteudo/<tipo>-<tema>-<AAAA-MM-DD>/` (peça solta); render e vídeo em `<pasta dos vídeos>/`, nunca no repositório.

## As regras do método
1. **Transcrição primeiro, palavra por palavra.** É ela que diz onde cada animação entra (no canal,
   `versoes/vN.json` já tem o tempo de cada palavra; narração gerada pelo `/voz`, o Whisper com `--word-timestamps`).
   Animação entra na palavra, nunca "mais ou menos"
2. **Entrega é o definitivo.** Corte, legenda e motion saem juntos numa versão só
3. **A lista de estados antes do código:** uma tabela com tempo (ou batida), fala, o estado da tela, o que muda,
   o toque e o som, o texto, onde na tela e por quê. Mudar uma linha da tabela custa nada; mudar depois do render
   custa um render. Peça que sai pra fora (página, anúncio): mostrar a tabela e esperar o ok antes do código. Os
   modelos estão no `motor/briefs.md`
4. **Limpo, estilo Apple.** Uma ideia por cartela, muito respiro, nenhum efeito por efeito. Quando entra é a receita
   do tipo (`canal/formatos.md`). **Proibido, porque é a cara de vídeo feito por IA:** título centralizado em cima
   de degradê, tudo entrando com fade, ficha ou rótulo solto no canto, moldura, brilho na interface, explosão de
   partícula, quique. Uma fonte, uma cor de destaque. Modo B e C: algo novo a cada 2 a 4 s; modo A segue a fala
5. **O acabamento que parece de verdade:** aparelho com moldura fiel, reflexo leve e sombra de contato; movimento
   com mola, entrada com desfoque que some, saída mais rápida que a entrada; fundo neutro com um degradê de luz no
   mesmo tom e grão leve
6. **Nada de caixa de texto por cima do rosto.** Motion sobre vídeo falado é **cena cheia**: a tela inteira vira a
   animação e volta pro rosto. Por cima do rosto, só a legenda
7. **Mola de verdade, não curva pronta.** As quatro molas do `motion.js`: `ui` (botão, toggle), `padrao` (cartão,
   contêiner, câmera), `pesada` (tipografia grande, logo, sem rebote), `brinca` (quase nunca). Valor que muda de alvo
   várias vezes é a soma de uma mola por mudança (`M.track`), nunca a mola reiniciada. Texto dentro de forma que se
   transforma entra depois que ela cresceu e sai antes da próxima mudança
8. **Da referência sai a gramática, nunca o conteúdo.** Com um vídeo de referência: `yt-dlp` baixa, o ffmpeg tira
   um quadro a cada 0,5 s e, antes do código, o Claude escreve `docs/guia-de-estilo.md` (paleta em hex, tipo,
   duração dos planos, transições, câmera, como o texto entra e sai) e `docs/lista-de-planos.md`. Sem referência:
   as do `perfil/referencias.md`, whatships.com (vídeos de lançamento), Dribbble motion
9. **Crítica com nota antes de mostrar** (`motor/critica.md`). Antes do render inteiro, um still por batida numa
   folha; depois do render, a folha de contato e a tira da ação mais rápida. Nota de 1 a 10 em gancho, leitura,
   movimento, variedade, composição, marca e sincronia; corrige os 3 piores (com o tempo de cada um) e re-renderiza.
   No máximo 3 rodadas. Cada rodada vira linha no `docs/revisao.md`. Olhar como diretor exigente, não como autor
   orgulhoso: a folha a cada 2 s mostra o buraco que o still não mostra (cena que abre vazia esperando uma palavra)
10. **Som na batida.** Música só a que a pessoa escolher (`/musica`), medida antes da animação (`motor/beats.py`):
    troca de estado na batida, momento grande no tempo forte. Sem música, a grade é um BPM fixo (120). Os sons de
    interface (clique, whoosh, baque) saem sintetizados (`motor/sfx.mjs`), baixinhos. Tudo em −14 LUFS
11. **Todos os formatos de uma linha do tempo.** As cenas se desenham contra o layout do formato (`L`), nunca
    contra pixel fixo, e cada formato sai no seu render (9:16, 4:5, 16:9)
12. **Peça longa tem portões** (mais de 45 s): guia de estilo e lista de planos → stills com crítica → rascunho em
    30 qps → animação inteira → som → render final. Não pular portão: o acerto que vem depois do render custa horas
13. **Leve.** Sem um subagente por cena: o Claude escreve as cenas ele mesmo. Folha de quadros só as necessárias
14. **Nunca dado real de terceiros.** App com dado de demonstração; número só com origem

## Modo A · Animação dentro do vídeo falado
Reel 9:16: cenas cheias pelo modelo `canal/templates/motion/reel-base.template.html`, com o vídeo dentro da
composição e a legenda junto (passo a passo no `/editar-episodio`, "Reel gravado em pé").
Vídeo 16:9 com cartela: `canal/templates/motion/` tem `numero.html` (rótulo + número grande + traço),
`frase-lateral.html` (frase de arte em até 3 linhas, de um lado) e `fechamento.html` (véu no quadro inteiro, frase
no centro). Cada cartela em `canal/episodios/<ep>/motion/NN-nome.html`; o `canal/episodios/<ep>/motion.json`
(`{"base": "vN", "cartelas": [{"cartela": "01-nome", "inicio": 0.70, "fala": "..."}]}`) e `canal.py motion <ep>`
renderiza com fundo transparente, cola cada uma no seu tempo e gera a próxima vN. Antes, ver onde a pessoa está no
quadro (`canal.py frame`): a cartela vai no lado livre; sem lado livre, fechamento.

## Modo B · Vídeo do produto (app, site, ferramenta)
1. **Briefing curto:** pra onde vai (página, anúncio 9:16 e 4:5), duração (página: 15 a 30 s em loop, sem som;
   anúncio: até 30 s, gancho nos 2 primeiros), qual recurso mostra e qual frase leva
2. **A lista de estados na grade de batidas:** de 8 a 12 estados que contam a história, numa tabela
   `batida | tempo | estado | o que muda | toque e som | texto`. Um conceito que rende: **uma forma que nunca
   corta** (um elemento muda de tamanho, raio e cor de estado em estado, um cursor conduz cada mudança)
3. **A tela real é a fonte:** capturar com o Playwright no app rodando local (celular 390×844 com escala 3), com
   dado de demonstração. Um print por estado (motor próprio) ou vídeo da sessão (HyperFrames). Nunca redesenhar a
   tela de cabeça: em código se refaz só o pedaço que mexe (o número rolando, o campo se preenchendo)
4. **Montar:** celular desenhado em código, app grande (o celular na altura toda, zoom no bloco que importa),
   frase de arte em volta, som de interface no toque
5. Crítica (regra 9), render por formato, `python3 motor/motor.py web final.mp4 web.mp4` pra página

## Modo C · Reel de marca, abertura, apresentação
Curto, o movimento é a mensagem. **Motor próprio**, com uma referência e a lista de planos antes do código. Uma
apresentação narrada (a pessoa contando o processo dela, por exemplo) segue o mesmo caminho: narração pelo `/voz`
(voz clonada) ou gravada, Whisper com o tempo de cada palavra, cada cena presa à palavra, janela de app recriada
em código com o conteúdo de verdade. Variações que funcionam: contar uma história (de onde veio até hoje); "como
um estúdio", cada plano uma técnica, uma cor de destaque.

## Armadilhas do HyperFrames
- **`fromTo` esconde o que está na tela antes da hora:** o estado de partida vale desde o início. Estado inicial
  com `tl.set` no 0; entrada com `set` + `to`
- **O `snapshot` não é o render:** conferir o MP4 final com quadros tirados pelo ffmpeg (`fps=1/5,tile`)
- **Nada de `left/top` animado** (treme no render): posição por `x/y`
- **Vídeo de câmera dentro da composição:** `--video-frame-format jpg` (png enche o disco) e o vídeo regravado
  com quadro-chave a cada 30 quadros
- **Mac com 8 GB:** entra sozinho no modo de pouca memória; com `HF_SEGMENTED_CAPTURE=true` e `--resume`, retoma
  se travar. Fechar o resto antes
- **Modelo e projeto em pastas separadas** (dois HTML com `data-composition-id` na pasta viram duas composições)
- As do motor próprio (fonte no canvas, `will-change`, texto vazando da forma, faixa no degradê): `motor/README.md`

## Não fazer
- `hyperframes publish`, `cloud render` ou `auth login`: sobem o projeto pra HeyGen. Só se a pessoa pedir
- Vídeo dentro do repositório: aqui só HTML, JSON e PNG leve
- Trocar a versão do HyperFrames no meio de um vídeo
