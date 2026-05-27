#!/bin/bash
# ============================================================
#  APACN - Nota Parana  |  Instalador Linux
# ============================================================

set -e  # Para imediatamente se qualquer comando falhar

# Cores
VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
AMARELO='\033[1;33m'
AZUL='\033[0;34m'
NC='\033[0m'

ok()    { echo -e "${VERDE}[OK]${NC} $1"; }
erro()  { echo -e "${VERMELHO}[ERRO]${NC} $1"; exit 1; }
info()  { echo -e "${AZUL}[...]${NC} $1"; }
aviso() { echo -e "${AMARELO}[!]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/apacn"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/apacn"

echo ""
echo "============================================================"
echo "  APACN - Nota Parana - Instalador Linux"
echo "============================================================"
echo ""

# ── 1. Verifica e instala Python 3 ───────────────────────────────────────────
info "Verificando Python 3..."
if ! command -v python3 &>/dev/null; then
    aviso "Python 3 nao encontrado. Instalando..."
    if   command -v apt-get &>/dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python python-pip
    else
        erro "Gerenciador de pacotes nao reconhecido. Instale o Python 3 manualmente e rode o script novamente."
    fi
fi
PY_VER=$(python3 --version 2>&1)
ok "$PY_VER"

# ── 2. Copia os arquivos do programa ─────────────────────────────────────────
info "Instalando arquivos em $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
for arq in main.py qr_collector.py notaparana_bot.py requirements.txt; do
    if [ ! -f "$SCRIPT_DIR/$arq" ]; then
        erro "Arquivo '$arq' nao encontrado. Certifique-se de que o install.sh esta na mesma pasta que os arquivos do programa."
    fi
    cp -f "$SCRIPT_DIR/$arq" "$INSTALL_DIR/"
done
ok "Arquivos copiados."

# ── 3. Cria o ambiente virtual Python ────────────────────────────────────────
info "Criando ambiente virtual Python..."
python3 -m venv "$INSTALL_DIR/venv"
ok "Ambiente virtual criado."

# ── 4. Instala dependencias Python ───────────────────────────────────────────
info "Instalando dependencias Python (pip)..."
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"
ok "Dependencias instaladas."

# ── 5. Baixa o Chromium ───────────────────────────────────────────────────────
info "Baixando Chromium para automacao (pode demorar ~5 minutos)..."
"$INSTALL_DIR/venv/bin/playwright" install chromium
ok "Chromium instalado."

# ── 6. Instala bibliotecas do sistema para o Chromium (requer sudo) ──────────
info "Instalando bibliotecas do sistema necessarias (requer senha de administrador)..."
sudo "$INSTALL_DIR/venv/bin/playwright" install-deps chromium
ok "Bibliotecas do sistema instaladas."

# ── 7. Cria o comando 'apacn' ─────────────────────────────────────────────────
info "Criando atalho de terminal 'apacn'..."
mkdir -p "$BIN_DIR"
cat > "$LAUNCHER" << LAUNCHER_EOF
#!/bin/bash
cd "\$HOME/.local/share/apacn"
exec "\$HOME/.local/share/apacn/venv/bin/python" "\$HOME/.local/share/apacn/main.py" "\$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"

# Garante que ~/.local/bin esta no PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    for RC in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$RC" ]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
            aviso "PATH atualizado em $RC."
            break
        fi
    done
fi
ok "Comando 'apacn' criado."

# ── 8. Atalho na area de trabalho (opcional) ─────────────────────────────────
for DESKTOP in "$HOME/Desktop" "$HOME/Área de Trabalho" "$HOME/Ambiente de trabalho"; do
    if [ -d "$DESKTOP" ]; then
        cat > "$DESKTOP/APACN.desktop" << DESKTOP_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=APACN - Nota Parana
Comment=Doacao automatica de notas fiscais no Nota Parana
Exec=bash -c 'cd \$HOME/.local/share/apacn && \$HOME/.local/share/apacn/venv/bin/python main.py; read -p "Pressione Enter para fechar..."'
Terminal=true
StartupNotify=false
DESKTOP_EOF
        chmod +x "$DESKTOP/APACN.desktop"
        ok "Atalho criado em: $DESKTOP"
        break
    fi
done

# ── Conclusao ─────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  INSTALACAO CONCLUIDA COM SUCESSO!"
echo "============================================================"
echo ""
echo "  Para iniciar o programa:"
echo ""
echo "    Opcao 1 — Digite no terminal:   apacn"
echo "    Opcao 2 — Use o atalho na area de trabalho"
echo ""
echo "  Se o comando 'apacn' nao funcionar, feche e abra"
echo "  o terminal novamente e tente outra vez."
echo ""
