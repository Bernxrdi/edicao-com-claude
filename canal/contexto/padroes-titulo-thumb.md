# Padrões · título e thumb

> Ponto de partida. As cores e o @ vêm do `canal/config.json`; a voz, do `perfil/como-falo.md`; as
> referências de olhar, do `perfil/referencias.md` (inspiração, nunca cópia). O que a pessoa ajustar vai
> pra `aprendizados.md` e volta pra cá.

## Título (3 opções por episódio, em `episodios/<ep>/titulos.md`)
- Cada opção num ângulo diferente: **curiosidade** (o que acontece), **oposição de dois conceitos**,
  **concreto da rotina** (o que a pessoa fez, viveu, montou)
- Até uns 60 caracteres, pra não cortar no celular (o limite do YouTube é 100)
- Promete só o que o vídeo entrega. Número só com origem confirmada
- Sem emoji, sem caixa alta inteira. Caixa alta numa palavra, se precisar
- Junto de cada opção: uma linha dizendo por que ela funciona e pra quem
- O título e a thumb se completam: a thumb não repete o título

## Thumb (3 variações por episódio, em `episodios/<ep>/thumbs/`)
- **Tamanho:** 1280x720 (16:9), PNG, até 2 MB
- **Cores:** fundo, texto e destaque do `config.json`. Uma cor de destaque só
- **Rosto:** quadro do próprio vídeo, com o fundo recortado (BiRefNet, local). Rosto grande, olho aberto,
  expressão que combine com a frase. Nenhum quadro repetido entre episódios próximos
- **Frase:** 2 a 4 palavras, caixa baixa, peso fino, com a palavra-chave em peso forte na cor de destaque
- **Assinatura:** o @ em rótulo pequeno
- **Nunca:** sombra pesada, seta vermelha, segunda cor de destaque, foto de banco
- **Teste de leitura:** renderizar também em 320x180 (o tamanho na lista do celular). Se a frase não lê ali, encurta
- **As 3 variações** mudam uma coisa por vez (frase, quadro ou layout), pro "Testar e comparar" do YouTube
  Studio dizer qual venceu
- **Layouts** (`templates/thumb.html`):
  - A · pessoa recortada sobre fundo liso, do lado em que o rosto está; frase do outro lado. A foto nunca
    invade a área da frase
  - B · o quadro inteiro com zoom, o rosto de um lado e um painel sólido com a frase do outro
- Texto nunca atrás da pessoa: o rosto cobrindo uma letra deixa a palavra ilegível
