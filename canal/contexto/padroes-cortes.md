# Padrões · cortes e calendário

> O que sai de cada episódio pro Instagram (ou TikTok, ou Shorts).

## Cortes verticais (o que faltar pra chegar a 3 reels na semana)
- **Formato:** 9:16, 1080x1920, MP4 H.264 com áudio AAC
- **Duração:** até 90 s, uma ideia só
- **Recorte:** de dentro do quadro horizontal, rosto no centro (o `canal.py vertical` acha o rosto sozinho).
  O Claude confere o enquadramento olhando quadros, não o vídeo inteiro
- **Começa no gancho,** sem contexto antes. **Termina na frase-soco**
- **Legenda queimada sempre** (a maioria assiste sem som), saída da transcrição: até 3 palavras e 15
  caracteres por vez, caixa baixa, sem pontuação, peso forte em 100 px, cor do texto com contorno escuro,
  palavra-chave na cor de destaque. Fica a uns 620 px do pé do quadro, acima da faixa que a interface do Reels tapa
- **Escolha justificada:** cada corte vem com o trecho (início e fim), o gancho e por que ele se sustenta sozinho
- Arquivo: `<pasta dos vídeos>/<ep>/cortes-instagram/corte-01.mp4`; legenda do post em `episodios/<ep>/calendario.md`

## Story
- 1080x1920, tema escuro. Um quadro do vídeo (`canal.py frame`) e uma frase convidando pro vídeo novo
- O link do YouTube entra pelo adesivo de link, que a pessoa põe no próprio Instagram

## Calendário (`episodios/<ep>/calendario.md` e o da semana em `semanas/<data>/calendario.md`)
Uma tabela com dia, hora, rede, peça, arquivo e legenda pronta. Ritmo de partida: o vídeo e o story no mesmo
dia, os reels em dias alternados. Hora só se a pessoa tiver uma preferida. Nenhum dia com duas peças no mesmo formato.
