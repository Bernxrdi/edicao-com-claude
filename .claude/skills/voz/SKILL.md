---
name: voz
description: >
  A voz dos vídeos: limpa a voz como o "melhorar voz" do CapCut (Sidon, código aberto, local: tira ruído e eco da
  sala) e, se a pessoa quiser, gera fala nova na voz dela (clone local, Qwen3-TTS) pra uma frase que faltou ou pra
  narrar um motion, sempre com marca d'água de IA. Use quando chamarem /voz, ou disserem "melhora a voz", "a voz
  tá ruim", "tira o eco", "tira o ruído", "voz de estúdio", "narra isso na minha voz", "clona minha voz",
  "grava a amostra da minha voz", "faltou uma frase".
---

# /voz · a voz limpa e a voz clonada

Tudo local e grátis, instalado pelo `./instalar.sh` em `~/.local/share/edicao-com-claude/voz/` (dois ambientes:
`mlx/` gera a voz, `torch/` limpa e marca). Os scripts moram em `voz/` na raiz do kit.

## A voz limpa (Sidon)
Os reels já passam por ela no fim (`canal/scripts/reel/finalizar.py`). Pra um vídeo longo ou um áudio solto:
1. Extrair: `ffmpeg -i video.mp4 -vn -ac 1 -ar 48000 -c:a pcm_s16le entrada.wav`
2. Limpar: `~/.local/share/edicao-com-claude/voz/torch/bin/python voz/sidon.py entrada.wav limpa.wav`
   (uns 3 s por segundo de áudio no M1; o primeiro uso baixa o modelo, ~1 GB)
3. Só corpo e controle: `ffmpeg -i limpa.wav -af "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=10:release=150:makeup=2" saida.wav`
4. Conferir: o Whisper tem que ler as mesmas palavras na saída (o Sidon refaz a voz e pode inventar som)
5. −14 LUFS no fim (`loudnorm=I=-14:TP=-1.5:LRA=11`)
Gravar melhor ajuda mais que qualquer modelo: celular perto da boca, sala com cortina ou tapete.

## A voz clonada (Qwen3-TTS)
**Só a voz da própria pessoa, com ela sabendo.** Nunca a voz de outra pessoa, nunca pra se passar por alguém.
Toda fala gerada sai com a marca d'água de IA (Perth). A pessoa ouve antes de publicar, sempre.

### Guardar a amostra (uma vez)
1. Pedir um vídeo ou áudio de 15 s da pessoa falando sozinha, solta, num lugar quieto (AirDrop cai em `~/Downloads`)
2. Extrair e limpar como acima (passos 1 a 3), cortando 10 a 15 s de fala contínua, sem música
3. Guardar em `~/.local/share/edicao-com-claude/voz/referencia.wav`
4. Transcrever (`mlx_whisper referencia.wav --language pt --output-format txt`) e guardar o texto exato em
   `~/.local/share/edicao-com-claude/voz/referencia.txt`

### Gerar fala
Escrever a frase como a pessoa fala (`perfil/como-falo.md`): de 6 a 8 s, com as expressões dela, sem palavra que
ela não usaria. Número por extenso ("vinte e sete"). Palavra estrangeira que o clone pronuncia errado: trocar por
outra (ex.: "reels" sai "rios"; "cortes" funciona).
```
cd voz
~/.local/share/edicao-com-claude/voz/mlx/bin/python -I falar.py "texto" saida.wav
~/.local/share/edicao-com-claude/voz/mlx/bin/python -I falar.py --lista falas.txt <pasta>     # "id|texto" por linha
```
Gera 2 tomadas por fala, o Whisper ouve cada uma e fica a que errou menos palavras (`escolhas.json` na pasta).
Caiu no meio: rodar o mesmo comando de novo, ele retoma. Aviso de "CONFERIR" em número por extenso é falso
alarme (o Whisper escreve "27"); palavra trocada de verdade: gerar de novo ou mudar a frase.
No M1 com 8 GB: rodar sozinho, sem render ao mesmo tempo.
