#!/bin/bash
# Instala o que o kit precisa num Mac com chip Apple (M1 ou mais novo). Da raiz do kit:
#   ./instalar.sh             instala o que falta (pode rodar de novo: o que já tem, pula)
#   ./instalar.sh --conferir  só diz o que falta, sem instalar nada
# Tudo grátis e local. Baixa uns GB (o Python da voz e o Chromium); os modelos de IA baixam no primeiro uso.
set -u

KIT="$(cd "$(dirname "$0")" && pwd)"
DADOS="$HOME/.local/share/edicao-com-claude"
BIN="$HOME/.local/bin"
PLAYWRIGHT="1.62.1"
export PATH="$BIN:/opt/homebrew/bin:/usr/local/bin:$PATH"
CONFERIR=0; [ "${1:-}" = "--conferir" ] && CONFERIR=1
FALTOU=0

ok()    { printf "  \033[32m✓\033[0m %s\n" "$1"; }
falta() { printf "  \033[33m✗\033[0m %s\n" "$1"; FALTOU=1; }
passo() { printf "\n\033[1m%s\033[0m\n" "$1"; }
pare()  { printf "\n\033[31m%s\033[0m\n" "$1"; exit 1; }

if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
  pare "O kit roda em Mac com chip Apple (M1 ou mais novo)."
fi
mkdir -p "$BIN" "$DADOS/voz"

node_dir() {  # a mesma busca do canal/scripts/kit.py: nvm, depois o PATH, depois o Homebrew
  local n; n=$(ls -d "$HOME"/.nvm/versions/node/v*/bin 2>/dev/null | sort -V | tail -1)
  if [ -n "$n" ]; then echo "$n"; return; fi
  command -v node >/dev/null 2>&1 && dirname "$(command -v node)"
}

passo "1. Ferramentas do Mac"
if xcode-select -p >/dev/null 2>&1; then ok "ferramentas de linha de comando da Apple"
else
  falta "ferramentas de linha de comando da Apple (pra ver rosto no vídeo)"
  if [ $CONFERIR = 0 ]; then xcode-select --install 2>/dev/null; pare "Aceite a janela da Apple, espere terminar e rode ./instalar.sh de novo."; fi
fi
if command -v claude >/dev/null 2>&1; then ok "Claude Code"; else falta "Claude Code (claude.ai/download ou docs.claude.com/claude-code)"; fi
if [ -d /Applications/WhatsApp.app ]; then ok "WhatsApp no Mac (pro robô do grupo)"; else falta "WhatsApp no Mac (só pro robô do grupo: App Store)"; fi

passo "2. uv (roda os scripts em Python)"
if command -v uv >/dev/null 2>&1; then ok "uv"
else
  falta "uv"
  [ $CONFERIR = 0 ] && curl -LsSf https://astral.sh/uv/install.sh | sh && ok "uv instalado"
fi

passo "3. ffmpeg (corta, junta, legenda)"
if [ -x "$BIN/ffmpeg" ] && [ -x "$BIN/ffprobe" ]; then ok "ffmpeg e ffprobe"
else
  falta "ffmpeg e ffprobe"
  if [ $CONFERIR = 0 ]; then
    if command -v brew >/dev/null 2>&1; then
      brew install ffmpeg && ln -sf "$(brew --prefix)/bin/ffmpeg" "$BIN/ffmpeg" && ln -sf "$(brew --prefix)/bin/ffprobe" "$BIN/ffprobe"
    else
      for f in ffmpeg ffprobe; do  # build estático pra Apple Silicon, com libass (legenda queimada)
        curl -fsSL "https://ffmpeg.martin-riedl.de/redirect/latest/macos/arm64/release/$f.zip" -o "/tmp/$f.zip" \
          && unzip -o -q "/tmp/$f.zip" -d "$BIN" && chmod +x "$BIN/$f" && rm -f "/tmp/$f.zip"
      done
    fi
    [ -x "$BIN/ffmpeg" ] && ok "ffmpeg instalado" || pare "Não consegui instalar o ffmpeg."
  fi
fi

passo "4. Node e o Chromium (renderizam as animações e as thumbs)"
NODE="$(node_dir)"
if [ -n "$NODE" ]; then ok "node ($("$NODE/node" -v))"
else
  falta "node"
  if [ $CONFERIR = 0 ]; then
    if command -v brew >/dev/null 2>&1; then brew install node
    else curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash \
           && . "$HOME/.nvm/nvm.sh" && nvm install 24; fi
    NODE="$(node_dir)"; [ -n "$NODE" ] && ok "node instalado" || pare "Não consegui instalar o Node."
  fi
fi
if ls -d "$HOME"/.npm/_npx/*/node_modules/playwright-core >/dev/null 2>&1; then ok "playwright"
else
  falta "playwright e o Chromium"
  [ $CONFERIR = 0 ] && [ -n "$NODE" ] && PATH="$NODE:$PATH" "$NODE/npx" -y "playwright@$PLAYWRIGHT" install chromium && ok "playwright instalado"
fi

passo "5. Whisper (transcreve na placa do Mac) e yt-dlp (baixa referência)"
for t in mlx-whisper yt-dlp; do
  if uv tool list 2>/dev/null | grep -q "^$t "; then ok "$t"
  else falta "$t"; [ $CONFERIR = 0 ] && uv tool install "$t" && ok "$t instalado"; fi
done

passo "6. A voz (Sidon limpa; Qwen3-TTS clona; Perth marca como IA)"
for amb in mlx torch; do
  if [ -x "$DADOS/voz/$amb/bin/python" ]; then ok "ambiente $amb"
  else
    falta "ambiente $amb da voz"
    if [ $CONFERIR = 0 ]; then
      uv venv -q --python 3.12 "$DADOS/voz/$amb" \
        && uv pip install -q --python "$DADOS/voz/$amb/bin/python" -r "$KIT/voz/requisitos-$amb.txt" \
        && ok "ambiente $amb instalado" || falta "ambiente $amb (veja o erro acima)"
    fi
  fi
done

passo "7. HyperFrames (plugin de animação do Claude Code)"
if command -v claude >/dev/null 2>&1; then
  if claude plugin list 2>/dev/null | grep -qi hyperframes; then ok "HyperFrames"
  else
    falta "HyperFrames"
    [ $CONFERIR = 0 ] && claude plugin marketplace add heygen-com/hyperframes \
      && claude plugin install hyperframes@hyperframes && ok "HyperFrames instalado"
  fi
fi

passo "8. A visão do Mac (acha o rosto pra enquadrar)"
if [ -x "$BIN/canal-visao" ]; then ok "canal-visao"
else
  falta "canal-visao"
  [ $CONFERIR = 0 ] && swiftc -O "$KIT/canal/scripts/visao.swift" -o "$BIN/canal-visao" && ok "canal-visao compilado"
fi

if [ $CONFERIR = 1 ]; then
  [ $FALTOU = 0 ] && printf "\nTudo pronto.\n" || printf "\nFalta o que está com ✗: rode ./instalar.sh\n"
  exit $FALTOU
fi
printf "\n\033[1mPronto.\033[0m Abra o Claude Code nesta pasta (claude) e rode /entrevista.\n"
printf "Os modelos de IA (Whisper, voz, recorte) baixam no primeiro uso: deixe o Mac na tomada e na internet.\n"
