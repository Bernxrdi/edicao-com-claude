# Motor próprio (11/10/2026)

O caminho que o Opus 5.5 escolhe sozinho quando ninguém manda framework: **o filme é uma página que
pinta o quadro `t`** (`window.seek(t)`), o Playwright anda no tempo tirando print de cada quadro e o
ffmpeg junta. Sem dependência, sem conta, grátis, local. Fonte: aula do Felipe Borges ("Como Fazer
Motion Graphics INSANOS com Opus 5.5", Fala IA!, 06/10/2026, youtube.com/watch?v=4wk7nTZler4) e o
artigo que ela segue ("How to build motion design studio with Opus 5.5", @0xMovez, X).

Quando usar este motor e quando o HyperFrames: skill `/motion`, "Os dois motores".

| arquivo | o que é |
|---|---|
| `index.template.html` | modelo do filme: marca no topo, layout por formato, cenas como lista, prévia em loop no navegador |
| `motion.js` | molas em forma fechada (`M.mola`, `M.track`, `M.indicador`, `M.troca`, `M.entra`, `M.sai`), ruído com semente, loop, grade de batidas |
| `render.mjs` | render: subquadros pro desfoque de movimento, trecho (`--de/--ate`), stills por batida, formatos |
| `beats.py` | grade de batidas da música que ele escolheu (librosa, pelo `uv run`, sem instalar nada) |
| `sfx.mjs` | sons de interface sintetizados (clique, pop, baque, whoosh, tique) num WAV |
| `motor.py` | folhas da crítica, mixagem em -14 LUFS e saída pra web com poster |
| `critica.md` | o loop de crítica com nota (regra 6) |
| `briefs.md` | referência → guia de estilo, lista de estados (modo B) e briefing de diretor (peça longa) |

## Começar um vídeo

Modelo e projeto em pastas separadas. O projeto mora onde a skill manda (modo B e C:
`canal/episodios/<ep>/motion-fonte/` ou `canal/conteudo/<tipo>-<tema>-<data>/`, só texto); o render vai pra `~/Movies/...`.

```sh
P=<pasta do projeto>; M=<raiz do kit>/canal/templates/motion/motor
mkdir -p $P/fontes $P/docs && cp $M/index.template.html $P/index.html && cp $M/motion.js $P/
cp $M/../../fontes/*.ttf $P/fontes/      # ou a fonte da marca do vídeo
export PATH="$HOME/.nvm/versions/node/v24.19.0/bin:$HOME/.local/bin:$PATH"
export PLAYWRIGHT_CORE=$(ls -d ~/.npm/_npx/*/node_modules/playwright-core | head -1)
```

Prévia: abrir o `index.html` no navegador (toca em loop). Depois, da pasta do projeto:

```sh
node $M/render.mjs --stills beats --out ~/Movies/.../stills   # um still por batida → crítica
node $M/render.mjs --fps 30 --sub 2 --out ~/Movies/.../silent.mp4   # rascunho rápido
python3 $M/motor.py folhas ~/Movies/.../silent.mp4 --tira 2.8      # crítica de novo
node $M/render.mjs --fps 60 --sub 4 --formato 9x16 --out ~/Movies/.../silent-9x16.mp4   # final
```

## Som

- Música só a que ele escolher (`/musica`). Com música: `uv run $M/beats.py musica.wav > beats.json`;
  a página lê a grade (`M.batida(n, grade)`): troca de estado na batida, momento grande no tempo
  forte (`downbeats`), som de interface nos picos (`hits`). Sem música: BPM fixo, 120
- Sons de interface: `sons.json` com `{t, tipo, vol}` → `node $M/sfx.mjs sons.json sfx.wav`
- Juntar: `python3 $M/motor.py mixar silent.mp4 final.mp4 --sfx sfx.wav --musica musica.wav`
- Página (sem som): `python3 $M/motor.py web final.mp4 web.mp4` (H.264, faststart, poster)

## Medido no M1 de 8 GB (11/10/2026)

Uns 108 ms por subquadro em 1080x1920: 6 s em 30 qps com 2 subquadros saíram em 39 s. Um filme de
15 s em 60 qps com 4 subquadros leva uns 6,5 min: rascunho em 30x2, final em 60x4. A grade de
batidas achou 119,7 BPM num clique de 120. Mixagem e folhas: segundos.

## Armadilhas

- Texto em canvas não espera a fonte: o modelo carrega antes (`window.pronto`) e o render espera
- Nunca `Math.random`, timer, transição de CSS ou estado guardado entre quadros: o quadro tem que
  sair igual em qualquer ordem (é o que deixa re-renderizar só um trecho)
- Nunca `will-change` no que a câmera aproxima (texto borrado)
- Texto dentro de forma que cresce: entra depois que ela cresceu (o ensaio mostrou o número
  vazando do botão em 2,85 s)
- Degradê de luz grande mostra faixas depois da compressão: o grão leve do modelo disfarça
