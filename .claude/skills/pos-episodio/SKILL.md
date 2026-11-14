---
name: pos-episodio
description: >
  Depois que a versão do vídeo do YouTube foi aprovada: transcrição do vídeo final, 3 títulos, descrição com
  capítulos e links, tags, 3 thumbs e o pacote pronto pra subir à mão no YouTube Studio. Use quando chamarem
  /pos-episodio, ou disserem "aprovei a v2", "faz os títulos", "thumb do vídeo", "descrição do vídeo",
  "capítulos", "pacote do youtube", "vou subir o vídeo".
---

# /pos-episodio · títulos, descrição, thumbs e o pacote

Comandos da raiz com `uv run canal/scripts/canal.py <comando>` (abaixo, só `canal.py`). Antes de tudo, ler
`canal/contexto/padroes-titulo-thumb.md`, `canal/contexto/padroes-descricao.md`, `canal/contexto/aprendizados.md`,
`perfil/como-falo.md` e `perfil/quem-sou.md` (os links de sempre).

## Passo 1 · Transcrição final
A versão aprovada está em `"aprovada"` no `plano-de-edicao.json` (ou a pessoa diz).
`canal.py transcricao <ep> --versao vN` gera `transcricao.md`, `.srt` e `.json` em `canal/episodios/<ep>/`.
Ler o `transcricao.md` inteiro: é a base de tudo daqui pra frente.

## Passo 2 · Títulos e descrição
- `titulos.md`: 3 opções, cada uma num ângulo, com uma linha de por que funciona
- `descricao.md`: no modelo de `padroes-descricao.md`. Capítulos tirados dos tempos da transcrição (o primeiro é
  `00:00`, pelo menos 3, cada um com 10 s ou mais). Link só confirmado. Tags no fim do arquivo
- Reler os dois contra o `perfil/como-falo.md`: tem que soar como a pessoa, sem cara de IA (nada de "mergulhe",
  "descubra", lista de três adjetivos, frase de efeito vazia)

## Passo 3 · Thumbs
Roda sozinho logo depois dos títulos, sem perguntar: as 3 thumbs saem prontas e a pessoa vê no fim, numa imagem só.
1. `canal.py folha <ep> vN` e ler a imagem: escolher quadros com o rosto nítido, olho aberto e expressão que
   combine com a frase.
2. `canal.py frame <ep> vN <tempo> --nome t1` (um por quadro escolhido).
3. Escrever `canal/episodios/<ep>/thumbs/thumbs.json`:
   ```json
   {"variacoes": [
     {"id": 1, "layout": "A", "imagem": "t1.png", "frase": "palavras em caixa baixa com *destaque*"},
     {"id": 2, "layout": "A", "imagem": "t2.png", "frase": "..."},
     {"id": 3, "layout": "B", "imagem": "t1.png", "frase": "..."}
   ]}
   ```
   As 3 mudam uma coisa por vez (frase, quadro ou layout). A frase completa o título, não repete. Opcionais por
   variação: `"lado"` (`direita`/`esquerda`, onde fica a pessoa), `"tamanho"` (fonte), `"altura_recorte"` (%),
   `"zoom"` (layout B).
4. `canal.py thumbs <ep>` (o primeiro uso baixa o modelo de recorte, uns minutos). Juntar as 3 e uma mini numa
   imagem só (ffmpeg `hstack`/`vstack`) e ler: frase legível na mini de 320x180, nada encostando, recorte limpo.
   Ajustar e renderizar de novo se precisar.

## Passo 4 · O pacote do YouTube
Escrever `canal/episodios/<ep>/publicar-youtube.md`, na ordem em que se faz no Studio:
1. Arquivo: `<pasta dos vídeos>/<ep>/editado/vN.mp4`
2. Título (o escolhido; sem escolha, o 1)
3. Descrição: colar a de `descricao.md` (sem as tags)
4. Thumb: subir a escolhida; com as 3, usar "Testar e comparar"
5. Legendas: enviar `transcricao.srt` (Legendas > Adicionar > Enviar arquivo > Com sincronização)
6. Tags: as do fim de `descricao.md`
7. Visibilidade e agendamento: dia e hora combinados (se não tem, perguntar)

## Passo 5 · Entregar
Os 3 títulos, a imagem com as thumbs e o caminho do pacote. A pessoa escolhe ou veta. O upload é dela
(sem API do YouTube). Próximo: `/multiplicar`.
