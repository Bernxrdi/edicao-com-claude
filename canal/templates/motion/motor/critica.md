# A crítica (o loop antes de mostrar qualquer coisa)

> Regra 6 do `/motion`. Vale pros dois motores. Fonte: artigo do @0xMovez (passo 11) e a aula do
> Felipe Borges de 06/10/2026, com o que ele já rejeitou nesta casa. O Claude lê imagem: olha o que
> renderizou antes de entregar. É isso que separa o vídeo bom do "ficou meio assim".

## Quando

1. **Antes do render inteiro:** um still por batida (`node render.mjs --stills beats`, ou a lista
   de tempos da lista de estados), juntado numa folha pequena. Crítica. Corrige.
2. **Depois do render:** `python3 motor.py folhas out/silent.mp4 --tira <t da ação mais rápida>`.
   Crítica de novo, agora com o movimento (a tira pega salto e sobreposição que o still não mostra).
3. No HyperFrames, o mesmo, com quadros tirados do MP4 final (o `snapshot` não é o render).

Até todas as notas chegarem a 8. **No máximo 3 rodadas** (pra não gastar à toa: folha
pequena, só as necessárias). Na terceira sem chegar, entrega dizendo o que ficou abaixo e por quê.

## O texto que o Claude segue

Abre a folha e olha direito. Diretor de motion exigente, não autor orgulhoso.

Nota de 1 a 10 em cada um:

| critério | o que é 10 |
|---|---|
| gancho | os 2 primeiros segundos param o dedo (modo A: o primeiro motion entra na palavra) |
| leitura no celular | tudo lê com 360 px de largura (`celular.png`); app grande, nunca "muito pequeno" |
| movimento | mola em tudo, saída mais rápida que a entrada, nenhum quadro morto |
| variedade | algo novo a cada 2 a 4 s (modo A: no pico da fala, não a cada 2 s) |
| composição | uma ideia por cena, respiro, nada encostando na borda nem na área da legenda |
| marca | cor, fonte e regra da BASE (caixa baixa, palavra-chave em 800 no destaque) |
| sincronia | entra na palavra (fala) ou na batida (música); som de interface no toque |

Lista os **3 piores problemas com o tempo** (`2,85 s: o número aparece antes do cartão crescer`).
Caça de propósito:

- texto se sobrepondo na troca, ou maior que o contêiner durante a transformação
- coisa deslizando reto, sem mola; tudo entrando com fade
- ficha solta no canto, moldura, rótulo de canto (ele: "ficou perdida")
- título centralizado em cima de degradê; brilho na interface; explosão de partícula
- texto escalado e borrado (nada de `will-change` no que a câmera aproxima)
- cursor parado em cima do que a pessoa precisa ler
- batida morta, sem nada acontecendo
- salto na emenda do loop (vídeo de página: último quadro igual ao primeiro)
- caixa de texto por cima do rosto dele; legenda em pílula escura com a palavra em azul
- dado que não é da casa de demonstração; número sem origem

Corrige os 3, re-renderiza **só os segundos afetados** (`--de 2 --ate 4`), mostra a folha nova e as
notas novas. Cada rodada vira uma linha em `docs/revisao.md` do projeto (data, notas, os 3
problemas, o que mudou). Ajuste que ele pedir depois vai pro aprendizados da BASE (regra 7).
