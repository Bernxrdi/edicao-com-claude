# Os briefings (o Claude escreve pra si mesmo antes do código)

> Fonte: artigo do @0xMovez (passos 04, 05, 06 e 10) e os prompts que o Felipe Borges usou na aula
> de 06/10/2026, adaptados à casa. **O prompt é 10% do vídeo; os outros 90% são o estúdio em volta:**
> regra, marca, referência, lista de estados e crítica. Uma linha ("faz um showreel, vai com tudo")
> testa o motor, nunca a ideia: não tem ideia dentro.

## 1. Referência → guia de estilo + lista de planos

Quando ele manda um vídeo ou um quadro de referência. Nomear um estilo vence descrever um estilo.

1. `yt-dlp` baixa pra `refs/`; ffmpeg tira **um quadro a cada 0,5 s** pra `refs/quadros/`. Estuda.
2. `docs/guia-de-estilo.md`: paleta (hex), tipo (família, peso, espaçamento), duração dos planos,
   tipos de transição, movimento de câmera, textura e grão, como o texto entra e sai.
3. `docs/lista-de-planos.md`: o vídeo de [duração] sobre [assunto] **naquele** estilo, com a marca
   da BASE. Pega a gramática da referência, nunca o conteúdo, o logo ou os personagens.
4. Mostra os dois e espera o ok antes de qualquer código.

Quadro único: diz o que tirar dele (paleta, tipo, grão) e o que não tirar (o assunto). Pasta de
imagens dele: primeiro o guia de estilo a partir dela. Com referência, o Claude escolhe a técnica;
o briefing fixa o visual e as travas, não a biblioteca.

## 2. A lista de estados (filme de produto, modo B)

A tela do produto é um cenário onde cada elemento tem um estado conhecido. O conceito que mais
rendeu na semana do lançamento do Opus 5.5 (e é o mesmo do ícone que se transforma, aprovado na
primeiro vídeo de produto feito por este método): **uma forma que nunca corta**. Um único elemento muda de tamanho, raio e cor de um
estado pro outro (botão, campo, carregando, check, cartão, gráfico), o conteúdo troca atrás de um
desfoque curto, um cursor conduz cada mudança com um toque de verdade, e o último quadro é igual
ao primeiro (loop).

```
<entradas>
Produto e o que mostra (o recurso, a frase do /copywriter, aprovada pelo revisor-copy).
De 8 a 12 estados que contam a história, cada um com o dado da casa de demonstração.
Marca da BASE: cores, fonte, uma cor de destaque. Música que ele escolheu (ou sem música).
Formatos (página 16:9 ou 4:5; anúncio 9:16 e 4:5).
</entradas>

<direcao>
Filme de produto com a interface em movimento. Um contêiner que nunca corta. Fundo papel com
luz no mesmo tom, uma cor de destaque. Molas com no máximo um fio de rebote.
Proibido: quique, brilho, degradê na interface, partícula, tempo morto, tela inventada.
</direcao>

<estrutura>
BPM da música (ou 120), N compassos, alguma coisa acontece em toda batida.
estado 1 → estado 2 → ... → estado 1 (loop)
</estrutura>

<construcao>
Motor próprio: index.html com window.seek(t), motion.js (molas), render.mjs.
Valor com vários alvos = M.track. Texto dentro do contêiner entra depois que ele cresce e sai antes
da próxima mudança. Indicador de aba: bordas em molas diferentes pra esticar.
Troca de estado na batida, momento grande no tempo forte, som de interface no toque.
A tela real é a fonte: print do app local recortado e animado; nunca redesenhar de cabeça.
</construcao>

<comeco>
Mostra a lista de estados na grade de batidas, em tabela, antes do código.
</comeco>
```

A tabela que ele aprova: `batida | tempo | estado | o que muda | toque e som | texto`.

## 3. Peça longa (VSL, filme de mais de 45 s): o briefing de diretor, com portões

Quem dirige é o Claude, mas como produção de várias etapas, sem correr pro render final.

- **O filme numa linha:** o que a pessoa sente no fim. Toda decisão confere contra ela.
- **Referências e entradas:** `refs/`, a música dele, as telas do app, o que manter e o que puxar.
- **Visual:** de 3 a 5 linhas (paleta, tipo, textura, câmera) e o que é proibido.
- **Roteiro de batidas:** atos com tempo, gancho nos 2 primeiros segundos, uma recompensa visual a
  cada 3 a 5 s, o último quadro preparando o primeiro.
- **Texto na tela:** quando vai grande, quando fica como legenda; a composição deixa o lugar dele.
- **Portões (não pular):** guia de estilo e lista de planos → stills de cada plano + crítica →
  animatic em 960x540 com o áudio provisório (o ritmo se acerta aqui, antes do acabamento) →
  animação inteira → acabamento → som → render final.
- **Entrega:** final.mp4, poster, folha de contato e a fonte limpa com o README do projeto.

Sem subagente por capítulo (gasta muito): o Claude faz as cenas ele mesmo, uma por uma.
