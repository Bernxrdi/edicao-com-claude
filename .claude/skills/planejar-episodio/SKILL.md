---
name: planejar-episodio
description: >
  Cuida das ideias do canal, sem roteiro: guarda a ideia mandada no chat (ou na nota "canal" do iPhone) no inbox
  e, se pedirem, sugere assuntos pra falar na câmera durante a semana. Não escreve roteiro nem cria episódio (o
  episódio nasce quando os vídeos chegam, no /editar-episodio). Use quando chamarem /planejar-episodio, ou
  disserem "anota essa ideia pro canal", "ideia de vídeo", "o que eu falo essa semana", "sobre o que eu gravo",
  "puxa as ideias do canal", "o que chegou no grupo".
---

# /planejar-episodio · as ideias do canal (sem roteiro)

O canal não tem roteiro: a pessoa grava solto, falando pra câmera sobre o que está vivendo, e quem acha o fio, o
gancho e a frase-soco é o Claude, na edição. Esta skill só guarda ideia e, se pedirem, sugere assunto. Nunca
devolve roteiro, cena a gravar ou fala pronta.

## Guardar uma ideia
Mandaram uma ideia no chat: acrescentar uma linha datada em `canal/ideias/inbox.md`, nas palavras da pessoa, e
responder em uma linha que guardou.

## Puxar as ideias do iPhone
`uv run canal/scripts/canal.py ideias` lê a nota "canal" do app Notas (a que sincroniza com o iPhone). Não existe:
`canal.py ideias --criar`. Se o Notas negar permissão: Ajustes do Sistema > Privacidade e Segurança > Automação,
liberar o Notas pro app que roda o Claude.

## O grupo do WhatsApp
O robô (`canal/scripts/radar.py`) acrescenta em `canal/semanas/do-grupo.md` o que chegou no grupo, com o título
dos links. Ler a parte que ainda não foi usada (o `/semana` marca o que já virou pauta). Assunto escolhido vira
linha datada no inbox, com o link.

## "O que eu falo essa semana?"
Ler `canal/ideias/inbox.md`, o `do-grupo.md`, o `perfil/quem-sou.md` e as `transcricao.md` dos episódios que já
saíram (pra não repetir). Devolver de 3 a 5 assuntos, uma linha cada: o assunto e por que agora. Só fato que a
pessoa viveu; número, horário ou valor só com origem.

## Lembrete de gravação (só quando perguntarem como gravar)
iPhone na horizontal pro YouTube e em pé pro reel, 4K a 30 qps, formato Alta Eficiência, Vídeo HDR desligado.
Errou e quer fora: fala a palavra de erro (padrão "pato amarelo") e repete. Tropeço pequeno fica. Vai falar de
duas coisas (antes e depois, duas ferramentas): ficar no centro do quadro, pra caber uma animação de cada lado.
