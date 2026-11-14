---
name: entrevista
description: >
  A primeira coisa a rodar no kit: uma entrevista pra entender quem é a pessoa, o que ela posta, pra quem, como
  ela fala, a marca, como grava e onde guarda os vídeos, e o grupo do WhatsApp das ideias. Escreve o perfil
  (perfil/), o canal/config.json e o canal/radar.toml, ajusta os tipos de vídeo ao que ela faz, baixa a biblioteca
  de música, liga o robô do grupo e, se ela quiser, guarda a amostra da voz pro clone. Use quando chamarem
  /entrevista, ou disserem "começar", "configurar o kit", "primeira vez", "refaz a entrevista", "mudei de nicho",
  "muda minhas cores", "muda meu @". Também quando o canal/config.json não existir e pedirem qualquer outra skill.
---

# /entrevista · o kit aprende quem é você

Conversa leve, um bloco por mensagem, no máximo 4 perguntas por bloco, numeradas. A pessoa responde do jeito que
vier (pode ser por voz, ditado, frase solta). Não repetir pergunta que já foi respondida de passagem. Resposta
vaga: seguir com o padrão e dizer qual ficou. No fim de cada bloco, uma linha do que entendeu.

## Antes · O Mac está pronto?
`./instalar.sh --conferir`. Faltou alguma coisa: dizer o que, em uma linha, e pedir pra rodar `./instalar.sh` num
terminal (ele pede a senha do Mac e baixa uns GB; leva de 15 a 40 min). Dá pra fazer a entrevista enquanto instala.

## Bloco 1 · Quem é você
1. Seu nome do jeito que aparece no vídeo, e o @ principal
2. Onde você posta (YouTube, Instagram, TikTok...) e os links que vão em toda descrição
3. Em duas linhas: o que você faz da vida e o que o seu conteúdo mostra
4. Três a cinco temas, uma palavra cada (eles entram na abertura do canal: "treino · estudo · IA")

## Bloco 2 · O que você posta
1. Mostrar a tabela de tipos do `canal/formatos.md` (lifestyle, treino, fala, explicativo, produto), uma linha
   cada: quais você faz, quais não, e se tem algum outro
2. Quantos vídeos por semana (padrão: 1 no YouTube + 2 ou 3 reels) e o tamanho de cada um
3. Você já tem um vídeo que gostou do jeito que ficou? Manda o link (vira referência de ritmo)

## Bloco 3 · Quem assiste
1. Quem é a pessoa que assiste (idade, momento de vida, o que ela quer ter ou ser)
2. O que te perguntam nos comentários ou no direct
3. O que você não quer que seu conteúdo pareça

## Bloco 4 · Como você fala
1. Tu ou você, gírias e expressões suas, palavrão sim ou não
2. Emoji: quais e quantos
3. Cola 2 ou 3 legendas que você já escreveu e gostou (ou manda o link de um vídeo seu falando: o Claude
   transcreve e tira o jeito de falar)
4. Uma coisa que você nunca diria

## Bloco 5 · A marca
1. Cores: fundo, texto e uma cor de destaque (hex, ou descreve que o Claude acha). Sem marca ainda: o padrão do
   kit (fundo quase preto, texto off-white, destaque azul claro) funciona bem em vídeo
2. Fonte: o kit vem com a Manrope (grátis). Tem outra? Manda o arquivo .ttf (precisa poder usar em vídeo)
3. Sua foto de perfil (o arquivo, de preferência com o rosto bem iluminado): entra na abertura e no fim do canal
4. Dois ou três perfis ou canais que você admira, e o que gosta em cada um (o olhar, o ritmo, a thumb)

## Bloco 6 · Como você grava
1. Que celular, e se tem microfone de lapela
2. Onde guardar os vídeos (padrão: `~/Movies/<seu-nome>`; fora da Mesa e de pasta que sincroniza com o iCloud).
   Quanto espaço livre tem no Mac (`df -h ~`): precisa de uns 3x o tamanho do bruto da semana
3. A palavra que você fala quando erra e quer que o trecho saia (padrão: "pato amarelo")

## Bloco 7 · O grupo do WhatsApp
1. Você tem (ou cria agora) um grupo só seu, só com você, pra jogar ideia e referência durante a semana? O nome
   exato dele. Precisa do app WhatsApp instalado e logado no Mac
2. Liga o robô que lê esse grupo a cada 30 min e guarda tudo pro dia de gravar?

## Bloco 8 · A voz (opcional)
Quer que o Claude possa gerar frase na sua voz (uma fala que faltou, a narração de um motion)? Só a sua voz, com
marca d'água de IA, e você ouve antes de publicar. Sim: mandar um vídeo de 15 s falando solto num lugar quieto
(segue o `/voz`, "Guardar a amostra").

## Gravar (depois do último bloco)
Mostrar a lista do que vai ser escrito e esperar o ok:
- `perfil/quem-sou.md` (bloco 1 e 3: quem é, o que faz, onde posta, links, temas, público, o que não quer parecer)
- `perfil/como-falo.md` (bloco 4: o jeito de falar e de escrever, com exemplos nas palavras da pessoa, o que evitar)
- `perfil/marca.md` (bloco 5: cores, fonte, foto, o que pode e o que não pode)
- `perfil/referencias.md` (bloco 2 e 5: os vídeos e perfis de referência e o que pegar de cada um)
- `canal/config.json` (no formato do `canal/config.exemplo.json`: nome, arroba, temas, pasta_videos,
  palavra_erro, cores)
- `canal/radar.toml` (cópia do `canal/radar.exemplo.toml` com o nome do grupo)
- `canal/formatos.md`: tirar os tipos que a pessoa não faz, acrescentar os que ela faz, mudar o "O que sai de cada
  semana" pro número dela
- a foto em `perfil/foto.png` (convertida com o ffmpeg se vier em outro formato) e a fonte, se for outra, em
  `canal/templates/fontes/` (e o nome dela no `perfil/marca.md`; os modelos usam a Manrope por padrão)

## Ligar (depois de gravar)
1. `mkdir -p <pasta_videos>` e `uv run canal/scripts/canal.py espaco`
2. A biblioteca de música: `python3 canal/scripts/reel/biblioteca-musica.py baixar` (uns minutos)
3. O robô, se ela quis: `uv run canal/scripts/radar.py rodar` (uma rodada de teste: tem que achar o grupo) e, deu
   certo, `uv run canal/scripts/radar.py instalar`. Erro de permissão ao ler o WhatsApp: Ajustes do Sistema >
   Privacidade e Segurança > Acesso Total ao Disco, ligar o app do terminal (e o `uv`, se o robô agendado falhar)
4. A voz, se ela quis e já mandou a amostra: `/voz`, "Guardar a amostra"
5. O primeiro teste: pedir um vídeo de 30 s falando pra câmera (com um "pato amarelo" no meio, pra ver o corte) e
   rodar o `/editar-episodio` nele

## Fechar
Uma mensagem curta: o que ficou configurado, o que ficou de fora e como é a semana daqui pra frente (joga no grupo
durante a semana; no dia de gravar, `/semana`).
Refazer depois: `/entrevista` de novo reescreve só o bloco que mudar.
