# edição com claude

Uma máquina de vídeo pro Claude Code. Você grava solto, sem roteiro, e manda por AirDrop. O Claude edita lendo a
transcrição, entrega o vídeo pronto (corte, legenda, voz limpa, música e animação), faz os títulos, as thumbs, os
cortes pro Instagram e o calendário da semana. Você assiste, pede ajuste por texto e posta.

Tudo roda no seu Mac, de graça: ffmpeg, Whisper, HyperFrames, Sidon e Qwen3-TTS. O único custo é o uso do seu
plano do Claude.

## Como funciona

1. **Durante a semana**, você joga ideia e referência num grupo do WhatsApp só seu. Um robô lê esse grupo a cada
   30 minutos e guarda tudo pro dia de gravar.
2. **No dia de gravar**, `/semana`: o Claude te faz de 5 a 7 perguntas, você responde falando, e sai a lista do
   que gravar (um vídeo pro YouTube e dois ou três reels), só com perguntas, sem roteiro.
3. **Você grava no iPhone.** Errou? Fala "pato amarelo" e repete: o corte acha e tira.
4. **AirDrop**, e o `/editar-episodio` assume. Ele não assiste o vídeo: lê a transcrição palavra por palavra,
   mede o silêncio e olha folhas de quadros. Acha o gancho, tira gaguejada e repetição, monta o fio da história.
5. **O tipo do vídeo decide o resto:** explicativo ganha animação, vlog ganha música animada, produto ganha a
   tela do app no celular.
6. **Chega uma versão só, pronta.** Você pede ajuste por texto ("no 3:40 tira isso") e sai a v2.
7. **Aprovou:** `/pos-episodio` faz 3 títulos, a descrição com capítulos e 3 thumbs; `/multiplicar` faz os cortes,
   o story e o calendário. Você sobe no YouTube e agenda no Instagram.

## O que precisa

- **Mac com chip Apple** (M1 ou mais novo), macOS recente, uns 20 GB livres pro kit e os modelos, e espaço pros
  vídeos da semana (o bruto em 4K ocupa; o kit apaga sozinho o que não serve depois que você aprova)
- **Claude Code** (claude.ai/download) num plano pago do Claude
- **iPhone** pra gravar (AirDrop pro Mac)
- **WhatsApp no Mac**, só se quiser o robô do grupo

## Instalar

No Terminal:

```sh
git clone https://github.com/Bernxrdi/edicao-com-claude.git ~/edicao-com-claude
cd ~/edicao-com-claude
./instalar.sh
```

O instalador confere o que você já tem e instala o resto (uv, ffmpeg, Node, Chromium, Whisper, os dois ambientes
da voz e o plugin HyperFrames). Leva de 15 a 40 minutos. Pode rodar de novo quando quiser: o que já tem, ele pula.
`./instalar.sh --conferir` só diz o que falta.

Guarde a pasta fora da Mesa (Desktop) e do iCloud: a sincronização cria cópias e atrapalha.

## Primeira vez

```sh
cd ~/edicao-com-claude
claude
```

E dentro do Claude Code: **`/entrevista`**. São 8 blocos curtos de perguntas (quem você é, o que posta, pra quem,
como você fala, sua marca, como grava, o grupo do WhatsApp e a voz). No fim, o kit sabe seu nome, seu @, suas
cores, seus tipos de vídeo e o seu jeito de falar, liga o robô e baixa a biblioteca de música. O primeiro teste é
um vídeo de 30 s falando pra câmera.

## As skills

| skill | o que faz |
|---|---|
| `/entrevista` | configura o kit pra você (a primeira coisa a rodar) |
| `/semana` | o dia de gravar: grupo, referências, pauta, lista de gravação, a edição inteira e o calendário |
| `/planejar-episodio` | guarda uma ideia ou sugere sobre o que falar |
| `/editar-episodio` | do bruto ao vídeo definitivo, e os ajustes |
| `/motion` | animação em código (número, frase, abertura, vídeo de produto) |
| `/voz` | limpa a voz como o "melhorar voz" do CapCut e, se quiser, gera frase na sua voz |
| `/musica` | música liberada no clima do vídeo, ou o áudio em alta pelo app |
| `/pos-episodio` | títulos, descrição com capítulos, thumbs e o pacote pro YouTube Studio |
| `/multiplicar` | cortes verticais com legenda, story, legendas dos posts e calendário |

## A voz clonada

Opcional. Com uma amostra de 15 s da sua voz, o kit gera frases novas nela (uma fala que faltou, a narração de
uma animação). **Só a sua voz, nunca a de outra pessoa.** Toda fala gerada leva uma marca d'água de IA (Perth) e
você ouve antes de publicar.

## Problemas comuns

- **O robô não acha o grupo:** o nome no `canal/radar.toml` tem que ser igual ao do WhatsApp. Erro de permissão:
  Ajustes do Sistema > Privacidade e Segurança > Acesso Total ao Disco, ligar o Terminal (e o `uv`)
- **"vídeo em HDR":** na câmera do iPhone, desligar o Vídeo HDR (Ajustes > Câmera > Gravar Vídeo)
- **Sem espaço:** `uv run canal/scripts/canal.py espaco` mostra o que ocupa; o bruto sai sozinho quando você aprova a versão
- **O primeiro uso de cada coisa demora:** o Whisper, a voz e o recorte da thumb baixam o modelo na primeira vez

## Créditos e licenças

- Código do kit: licença MIT (`LICENSE`)
- [HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen, Apache 2.0) · [mlx-whisper](https://github.com/ml-explore/mlx-examples)
  (MIT) · [mlx-audio](https://github.com/Blaizzy/mlx-audio) (MIT) com o Qwen3-TTS (Alibaba, Apache 2.0) ·
  [Sidon](https://github.com/sarulab-speech/Sidon) (MIT) · [Perth](https://github.com/resemble-ai/Perth) (Resemble AI, MIT) ·
  [rembg](https://github.com/danielgatis/rembg) com o BiRefNet (MIT) · [Manrope](https://fonts.google.com/specimen/Manrope) (OFL) ·
  músicas da [Mixkit](https://mixkit.co/license/) (licença da Mixkit, sem crédito)
- O método do motion vem das aulas do Felipe Borges no canal Fala IA! e do artigo "How to build motion design
  studio", do @0xMovez. O fluxo de conteúdo foi inspirado no do Edu, do Ratos de IA

Feito por [@oleobernardi](https://instagram.com/oleobernardi).
