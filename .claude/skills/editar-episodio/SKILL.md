---
name: editar-episodio
description: >
  Edita o vídeo do YouTube e os reels: puxa os vídeos do AirDrop pro bruto, transcreve, monta o plano (corta
  silêncio, gaguejada, repetição e a palavra de erro, o "pato amarelo"), escolhe o trecho bom olhando quadros e
  entrega direto o vídeo definitivo (corte, legenda, voz limpa, música e, quando o trecho pede, motion em cena
  cheia pelo /motion), sem versão intermediária. Também refaz com os ajustes pedidos por texto. Use quando
  chamarem /editar-episodio, ou disserem "edita o vídeo", "mandei os vídeos", "já mandei por AirDrop", "faz a
  v1", "corta o vídeo", "ajusta a v1", "tira o trecho", "refaz o vídeo", "aprovei a versão".
---

# /editar-episodio · do bruto ao definitivo

O fluxo inteiro está no `CLAUDE.md` da raiz. Comandos rodam da raiz do kit com
`uv run canal/scripts/canal.py <comando>` (abaixo, só `canal.py`). Antes de tudo, ler
`canal/contexto/aprendizados.md`, a receita dos tipos (`canal/formatos.md`) e o `perfil/como-falo.md`.

**O que sai por semana:** o que a lista de gravação do `/semana` mandar (padrão: 1 vídeo do YouTube + 2 ou 3
reels). Cada peça tem um tipo (lifestyle, treino, fala, explicativo, produto) e o tipo decide motion, mockup e música.

**Como o Claude edita:** não assiste nem ouve. Corta pela transcrição (palavra por palavra) e pelo silêncio do
áudio, e "vê" por folhas de quadros (`canal.py folha`), que ele lê como imagem. Folha gasta uso: uma por cena
de rotina e uma da versão pronta, não mais.

## Passo 1 · Achar o episódio e o espaço
**Quem diz qual vídeo é qual peça é a lista de gravação** (`canal/semanas/<data>/pauta.md`). O editor segue a
lista e não escolhe tema sozinho. Chegaram vídeos sem lista: antes de cortar, transcrever e mostrar **o mapa**
numa mensagem só (cada clipe: o que se fala em meia linha, o tema, o tipo e a peça proposta: YouTube, reel 1,
reel 2, fora) e esperar o ok, que pode ser de uma palavra.

Sem roteiro, o episódio nasce aqui: `canal.py novo <assunto>` (sem assunto, `semana`). `canal.py estado <ep>`
(o mais recente em `canal/episodios/`, se não disserem) e `canal.py espaco`. Bruto novo precisa de uns 3x o
tamanho dele livre. Faltou: dizer quais episódios antigos ocupam espaço e perguntar se pode apagar o bruto deles.

## Passo 2 · Importar
`canal.py importar <ep>` lista os vídeos de `~/Downloads` (onde o AirDrop cai). Os que forem claramente do
episódio: mover com `canal.py importar <ep> <arquivo> ...` e dizer quais foram. Ficou dúvida: perguntar.

## Passo 3 · Transcrever e planejar
1. `canal.py transcrever <ep>`. Se avisar HDR, dizer uma vez pra desligar o Vídeo HDR na câmera do iPhone.
2. `canal.py plano <ep>` gera `plano-de-edicao.json` e `lista-de-cortes.md`.
3. Refinar o plano (editar o JSON):
   - **o fio (não tem roteiro):** ler a transcrição de todos os clipes e montar a ordem. Abre com o gancho (a
     frase mais forte dita, nos primeiros 5 s), agrupa por assunto, tira o que não leva a lugar nenhum (volta,
     repetição, assunto que morreu no meio) e fecha numa frase-soco dita pela pessoa. Assunto bom que não cabe
     no fio: marcar na lista de cortes como corte pro Instagram ou começo do próximo episódio
   - **erros:** conferir na lista se o texto apagado antes da palavra de erro é mesmo o take errado
   - **take repetido inteiro:** fica o melhor (em geral o último); no outro, `"usar": false`
   - **rotina:** `canal.py folha <ep> <clipe>`, ler a imagem e escolher o trecho bom (estável, com luz, a ação
     visível; sem o começo e o fim tremidos), 3 a 8 s por cena. Pôr em `trechos` e tirar o `revisar`
   - **gaguejada e repetição saem todas.** A transcrição comum esconde ("limpa" o "ele ele", o "né", o "hã").
     Pra achar: Whisper de novo com prompt de hesitação (`--initial-prompt "Então, é... né? hã... tipo, ele ele
     vai, o o cliente, tá?"`), palavra esticada (mais de 0,6 s numa palavra curta) e a energia do áudio. Trecho
     que tem muita: escolher outro. Recomeço ("ele vai ter... hã... ele vai ter esquecido"): fica só o recomeço.
     Depois de cortar, a mesma transcrição literal sobre a versão é a prova: tem que sair limpa
   - **palavra perdida:** o Whisper às vezes some com uma palavra no começo da frase, e o corte por transcrição
     levaria ela junto. Corte que cai colado numa fala: conferir a energia do áudio antes
   - **tipo:** `"tipo"` no topo do plano (da lista de gravação ou do mapa). A receita do tipo vale pro resto
   - **música, automática pelo tipo:** `python3 canal/scripts/reel/biblioteca-musica.py escolher <tipo> --ep <ep>`
     devolve o JSON que vai em `"musica"` no plano (faixa liberada da Mixkit, sem repetir na semana). A pessoa
     troca se quiser (`/musica`). Pediu música famosa: sai sem música e o calendário diz qual pôr pelo app
   - **voz:** o reel passa pelo Sidon no `finalizar.py`. No longo, rodar o `/voz` no áudio antes do definitivo
4. `canal.py plano <ep> --so-lista` reescreve a lista com os ajustes.

## Passo 4 · Renderizar o definitivo e conferir
**Uma entrega só: o vídeo definitivo.** Nada de versão só com corte, só com legenda ou só com motion pra
aprovar por partes: corte, legenda, motion (quando cabe) e áudio saem juntos na mesma vN. Base interna pro
acabamento (`canal.py render <ep> --versao base`) pode existir, mas não é entregue.
`canal.py render <ep>` gera `<pasta dos vídeos>/<ep>/editado/vN.mp4` e o retrato da versão em
`canal/episodios/<ep>/versoes/vN.json`. Conferir com `canal.py folha <ep> vN` antes de entregar: ordem certa,
nenhum quadro preto, nada cortado no meio de uma ação.

## Passo 5 · Entregar
Caminho do vídeo, duração e o resumo da lista de cortes (erros tirados, quanto saiu, o que olhar com atenção).
Abrir no QuickTime (`open -a "QuickTime Player" <arquivo>`). Pedir os ajustes por texto, com o tempo da versão.

## Passo 6 · Ajustes
- O tempo citado é da versão vN. Pra achar no bruto: em `versoes/vN.json`, o segmento com `saida_inicio <= t`;
  tempo no clipe = `inicio + (t - saida_inicio)`.
- Ajustar o plano e renderizar a próxima versão (`canal.py render <ep>` cria v2, v3...). **A versão nova apaga a
  anterior na hora**: no disco fica só a última entregue, o bruto e a base interna.
- **Todo ajuste vira linha** em `canal/contexto/aprendizados.md`: `AAAA-MM-DD · <ep> · o que pediu → o que muda`.
- Ajuste que se repete (corte seco demais, pausa curta demais) vira parâmetro: mudar em `parametros` do plano e
  propor mudar o `PARAMETROS_PADRAO` do `canal.py`.

## Passo 7 · Motion (dentro do definitivo, quando o tipo pede)
Pelo tipo (`canal/formatos.md`): lifestyle, treino e fala vão sem motion (no máximo o fecho); explicativo leva
motion só nos picos; produto leva o modo B. Mockup só quando a fala é sobre uma tela. Quando entra, é **cena
cheia** (a tela inteira vira a animação e volta pro rosto), nunca caixa de texto por cima do rosto. Por cima do
rosto, só a legenda. Seguir a skill `/motion` com os tempos das palavras da base interna; o vídeo sai junto, no
passo 4. Ajuste depois: refazer a base, recalcular os tempos e renderizar o definitivo de novo.
Peças prontas do canal: `scripts/cartelas-hora.py` (a tela da hora do vlog), `scripts/motion-sobre.py` (a
abertura e o fim do canal por cima de uma cena: `--arquivo perfil/foto.png:assets/perfil.png`), `scripts/cartela.py`.

## Reel gravado em pé
Vídeo vertical passa pela mesma máquina: um episódio por reel (`canal.py novo <assunto>`); vários reels do mesmo
bruto, o bruto entra por link (`ln`, sem cópia). Scripts em `canal/scripts/reel/`:
1. `canal/episodios/<ep>/trechos.json` (janela de cada emenda e o que "tirar" de dentro) →
   `uv run canal/scripts/reel/montar-plano.py <ep>` (emenda e pausa pela energia do áudio, limiar −30 dB) →
   `canal.py render <ep> --versao base`
2. `canal/episodios/<ep>/motion-fonte/`: `reel.json` (deixas, correções da legenda, destaques) e, se tiver
   motion, `cenas.html`, `cenas.css` e `roteiro.js` → `python3 canal/scripts/reel/montar-motion.py <ep> reel base`
   (Whisper literal sobre a base, legenda e cenas no modelo `canal/templates/motion/reel-base.template.html`)
3. `npx hyperframes render` no projeto (`trabalho/reel/`) → `python3 canal/scripts/reel/finalizar.py <ep> reel vN base`
   (voz restaurada pelo Sidon, música só se escolhida e calibrada, −14 LUFS): sai o definitivo `editado/vN.mp4`
Legenda a 620 px do pé, no peito. **Final em motion:** `"outro": {"segundos": 2.6, "linhas": [...]}` no
`reel.json` liga a cena final de curtir e compartilhar, com o @ do `config.json`.
**Gravação longa (aula, conversa):** antes de cortar, fazer o mapa do vídeo inteiro (horário, o que se fala,
limpo ou com gaguejada, o que não pode entrar) e deixar a pessoa escolher os trechos.

## Passo 8 · Aprovou
1. Gravar `"aprovada": "vN"` no topo do `plano-de-edicao.json`.
2. Na mesma hora: `canal.py apagar-bruto <ep> --sim --manter vN`. Sai o bruto, o `trabalho/` e as outras
   versões; fica a aprovada (e a base dela, se tiver motion), os cortes e o texto do episódio. Dizer quantos GB liberou.
3. Vídeo do YouTube: seguir pro `/pos-episodio`. Reel: entregar o arquivo final.

## Regras
- A lista de gravação manda; sem lista, o mapa antes do corte
- O tipo de cada peça decide motion, mockup e música (`canal/formatos.md`)
- O bruto só sai na aprovação, e aí sai sozinho. Antes dela, nunca. "Aprovei" que vale é o da pessoa, com a versão
- Só dizer que está pronto depois de renderizar e olhar a folha da versão
- Nada acumula: versão nova apaga a anterior; quando o definitivo sai, sai também o arquivo de trabalho
- Nada de caixa de texto por cima do rosto; motion é cena cheia, e só onde o trecho pede
- Nunca dado de cliente, da empresa onde a pessoa trabalha ou de terceiros em vídeo, corte ou legenda
