# edicao-com-claude · a máquina de vídeo

Kit pra criar e editar vídeo do YouTube e reels com o Claude Code, no Mac: a pessoa grava solto, sem roteiro, e
manda por AirDrop; o Claude edita lendo a transcrição (não assiste), entrega a versão definitiva, faz títulos,
thumbs e cortes e monta o calendário da semana. Tudo local e grátis (ffmpeg, Whisper, HyperFrames, Sidon, Qwen3-TTS).

## Começo de toda conversa
1. Sem `canal/config.json`: a pessoa ainda não fez a entrevista. Antes de qualquer outra coisa, `/entrevista`
2. Com ele: ler `perfil/quem-sou.md` e `perfil/como-falo.md` (quem é e como fala). Usar naturalmente, sem listar
3. O resto se lê quando a tarefa pedir: a receita dos tipos em `canal/formatos.md`, a marca em `perfil/marca.md`,
   os padrões em `canal/contexto/`, os ajustes já pedidos em `canal/contexto/aprendizados.md`

## O fluxo de uma semana
| passo | quem | como | sai em |
|---|---|---|---|
| 1. Ideias | a pessoa | joga tema e referência no grupo do WhatsApp dela durante a semana (ou no chat, ou na nota "canal" do iPhone) | `canal/semanas/do-grupo.md` (o robô) · `canal/ideias/inbox.md` |
| 2. Pauta | Claude | `/semana`: lê o grupo e as referências, faz de 5 a 7 perguntas, a pessoa responde por voz | `canal/semanas/<data>/pauta.md` |
| 3. Lista | Claude | `/semana`: o que gravar (YouTube + reels), cada um com o tipo e as perguntas pra câmera. Pergunta, nunca roteiro | `pauta.md` |
| 4. Gravar | a pessoa | iPhone, 4K 30 qps, HDR desligado; errou: a palavra de erro ("pato amarelo") e repete | iPhone |
| 5. Mandar | a pessoa | AirDrop (cai em `~/Downloads`; o Claude move) | `<pasta dos vídeos>/<ep>/bruto/` |
| 6. Editar | Claude | `/editar-episodio`: o fio, o gancho, sem silêncio, gaguejada e erro; legenda, voz limpa, música e motion pela receita do tipo; uma versão definitiva | `<pasta dos vídeos>/<ep>/editado/vN.mp4` |
| 7. Revisar | a pessoa | assiste e pede ajuste por texto, com o tempo ("no 3:40 tira isso"); aprovou, o bruto sai sozinho | `v2`, `v3`... |
| 8. Pós | Claude | `/pos-episodio`: 3 títulos, descrição com capítulos, 3 thumbs e o pacote do Studio | `canal/episodios/<ep>/` |
| 9. YouTube | a pessoa | sobe à mão com o `publicar-youtube.md` | YouTube |
| 10. Multiplicar | Claude | `/multiplicar`: os cortes que faltam, o story, as legendas e o calendário | `<pasta dos vídeos>/<ep>/cortes-instagram/` |
| 11. Instagram | a pessoa | agenda no app com as legendas do calendário | Instagram |

O `/semana` puxa do passo 2 ao 10 em sequência. `<ep>` = `AAAA-MM-DD-assunto`; `<pasta dos vídeos>` = a
`pasta_videos` do `canal/config.json`.

## As skills
| skill | o que faz |
|---|---|
| `/entrevista` | a primeira vez: perfil, marca, config, robô do grupo, voz |
| `/semana` | o dia de gravar: grupo, referências, pauta, lista de gravação, a máquina e o calendário |
| `/planejar-episodio` | guarda ideia e sugere assunto (sem roteiro) |
| `/editar-episodio` | do bruto ao definitivo, e os ajustes |
| `/motion` | animação em código (cena cheia, padrão Apple, na palavra certa) |
| `/voz` | voz limpa (Sidon) e voz clonada (só a própria, com marca d'água de IA) |
| `/musica` | música liberada pelo clima do tipo; áudio em alta pelo app |
| `/pos-episodio` | títulos, descrição, capítulos, thumbs, pacote do YouTube |
| `/multiplicar` | cortes verticais, story, legendas, calendário |

## A máquina (scripts)
- `canal/scripts/canal.py` (`uv run canal/scripts/canal.py --help`): novo, ideias, importar, transcrever, plano,
  render, transcricao, folha, frame, recorte, thumbs, vertical, motion, estado, espaco, apagar-bruto. Os
  ajustáveis da edição estão em `PARAMETROS_PADRAO`
- `canal/scripts/kit.py`: lê o `config.json` (pasta dos vídeos, nome, @, temas, cores) e troca nos modelos
- `canal/scripts/radar.py`: o robô do grupo do WhatsApp (rodar, instalar, desinstalar, estado). Só script, sem IA
- `canal/scripts/reel/`: o reel gravado em pé (montar-plano, montar-motion, finalizar) e a música (biblioteca-musica, previas-musica)
- `canal/scripts/`: cartelas-hora (a tela da hora do vlog), motion-sobre (abertura e fim do canal), cartela, inscreva, movimento
- `canal/templates/`: thumb, fontes (Manrope, OFL), motion (cartelas, abertura, fim, reel-base) e `motion/motor/` (o motor próprio)
- `voz/`: falar (clone), ouvir, escolhe, sidon. Ambientes em `~/.local/share/edicao-com-claude/voz/`
- `./instalar.sh` instala o que falta; `./instalar.sh --conferir` só diz

## Regras
- **Vídeo nunca dentro do repositório.** Aqui só texto, JSON e PNG leve; vídeo na pasta dos vídeos (fora da Mesa e do iCloud)
- **Disco:** `canal.py espaco` antes de puxar bruto novo; bruto precisa de uns 3x o tamanho livre
- **Grátis primeiro.** Ferramenta paga só com o ok da pessoa, mostrando o custo e a alternativa grátis
- **Testar com arquivo real** antes de dizer que funciona. Só dizer "pronto" depois de olhar a folha da versão
- **O que é da pessoa vira lista** (gravar, subir, permissão, senha); o que o Claude consegue, faz na hora
- **Robô não usa IA:** o que precisa de IA acontece na sessão, com a pessoa
- **Nunca dado de terceiros** (cliente, empresa, gente que não autorizou) em vídeo, corte, thumb ou legenda
- **Voz clonada só a da própria pessoa,** com marca d'água de IA; ela ouve antes de publicar
- **Número só com origem confirmada** (está na pauta ou a pessoa disse)
- Texto que sai pra fora (título, descrição, legenda) soa como a pessoa (`perfil/como-falo.md`), sem cara de IA
- Todo ajuste que a pessoa pedir entra em `canal/contexto/aprendizados.md`, datado
