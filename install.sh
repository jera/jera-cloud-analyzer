#!/bin/bash
# =================================================================
# Jera Cloud Analyzer CLI - Installation Script
# =================================================================

set -e  # Exit on any error

echo "🔍 Jera Cloud Analyzer CLI - Installation Script"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Get current directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python version
print_step "Verificando versão do Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    print_success "Python $PYTHON_VERSION encontrado"
    
    # Check if version is >= 3.8
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
        print_success "Versão do Python compatível (>= 3.8)"
    else
        print_error "Python 3.8+ é obrigatório. Versão atual: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python3 não encontrado. Instale Python 3.8+ primeiro."
    exit 1
fi

# Check pip
print_step "Verificando pip..."
if command -v pip3 &> /dev/null; then
    print_success "pip3 encontrado"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    print_success "pip encontrado"
    PIP_CMD="pip"
else
    print_error "pip não encontrado. Instale pip primeiro."
    exit 1
fi

# Create virtual environment (optional but recommended)
if [ "$1" = "--venv" ] || [ "$1" = "-v" ]; then
    print_step "Criando ambiente virtual..."
    python3 -m venv .venv
    print_success "Ambiente virtual criado em .venv"
    
    print_step "Ativando ambiente virtual..."
    source .venv/bin/activate
    print_success "Ambiente virtual ativado"
fi

# Clean previous installation
print_step "Limpando instalação anterior..."
$PIP_CMD uninstall -y cloud-insights 2>/dev/null || true
print_success "Instalação anterior removida"

# Update pip, setuptools and wheel
print_step "Atualizando ferramentas de instalação..."
$PIP_CMD install --upgrade pip setuptools wheel
print_success "Ferramentas atualizadas"

# Install dependencies
print_step "Instalando dependências..."
$PIP_CMD install -r requirements.txt
print_success "Dependências instaladas"

# Install package in editable mode
print_step "Instalando Jera Cloud Analyzer CLI..."
$PIP_CMD install -e .
print_success "Jera Cloud Analyzer CLI instalado"

# Verify installation and create fallback if needed
print_step "Verificando instalação..."

# Test if command is available
if command -v cloud-analyzer &> /dev/null; then
    print_success "Comando cloud-analyzer instalado com sucesso"
else
    print_warning "Entry point não funcionou, criando wrapper alternativo..."
    
    # Find the appropriate bin directory
    PYTHON_SCRIPTS_DIR=""
    if [ -n "$VIRTUAL_ENV" ]; then
        PYTHON_SCRIPTS_DIR="$VIRTUAL_ENV/bin"
    elif [ -d "$HOME/.local/bin" ]; then
        PYTHON_SCRIPTS_DIR="$HOME/.local/bin"
    else
        PYTHON_SCRIPTS_DIR=$(python3 -c "import site; print(site.USER_BASE + '/bin')" 2>/dev/null || echo "$HOME/.local/bin")
    fi
    
    # Create the scripts directory if it doesn't exist
    mkdir -p "$PYTHON_SCRIPTS_DIR"
    
    # Create a wrapper script
    cat > "$PYTHON_SCRIPTS_DIR/cloud-analyzer" << EOF
#!/bin/bash
# Jera Cloud Analyzer CLI Wrapper
cd "$INSTALL_DIR"
python3 "$INSTALL_DIR/cli.py" "\$@"
EOF
    
    chmod +x "$PYTHON_SCRIPTS_DIR/cloud-analyzer"
    print_success "Wrapper script criado em $PYTHON_SCRIPTS_DIR/cloud-analyzer"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$PYTHON_SCRIPTS_DIR:"* ]]; then
        print_warning "Adicionando $PYTHON_SCRIPTS_DIR ao PATH..."
        
        # Add to shell profile
        SHELL_PROFILE=""
        if [ -f "$HOME/.zshrc" ]; then
            SHELL_PROFILE="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_PROFILE="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            SHELL_PROFILE="$HOME/.bash_profile"
        fi
        
        if [ -n "$SHELL_PROFILE" ]; then
            echo "export PATH=\"$PYTHON_SCRIPTS_DIR:\$PATH\"" >> "$SHELL_PROFILE"
            print_success "PATH atualizado em $SHELL_PROFILE"
            print_warning "Execute: source $SHELL_PROFILE ou reinicie o terminal"
        fi
    fi
fi

# Setup configuration
print_step "Configurando arquivos de ambiente..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        print_success "Arquivo .env criado a partir do env.example"
        print_warning "IMPORTANTE: Edite o arquivo .env com suas credenciais antes de usar!"
    else
        print_warning "Arquivo env.example não encontrado"
    fi
else
    print_warning "Arquivo .env já existe, não será sobrescrito"
fi

# Test installation
print_step "Testando instalação..."

# Test direct execution first
if python3 "$INSTALL_DIR/cli.py" --version >/dev/null 2>&1; then
    print_success "CLI funcional via execução direta"
else
    print_error "Falha na execução direta do CLI"
    exit 1
fi

# Test command availability and show version
if command -v cloud-analyzer &> /dev/null; then
    print_success "Comando cloud-analyzer disponível globalmente"
    echo
    cloud-analyzer --version
elif [ -x "$PYTHON_SCRIPTS_DIR/cloud-analyzer" ]; then
    print_success "Comando cloud-analyzer disponível via wrapper"
    echo
    "$PYTHON_SCRIPTS_DIR/cloud-analyzer" --version
else
    print_warning "Comando global não disponível, mas CLI funcional"
    echo
    python3 "$INSTALL_DIR/cli.py" --version
fi

echo
echo "🎉 Instalação concluída com sucesso!"
echo "=========================="
echo

# Provide usage instructions based on what works
if command -v cloud-analyzer &> /dev/null; then
    echo "✅ Use: cloud-analyzer -q \"sua pergunta\""
elif [ -x "$PYTHON_SCRIPTS_DIR/cloud-analyzer" ]; then
    echo "✅ Use: cloud-analyzer -q \"sua pergunta\" (após reiniciar terminal)"
    echo "   Ou: $PYTHON_SCRIPTS_DIR/cloud-analyzer -q \"sua pergunta\""
else
    echo "✅ Use: python3 $INSTALL_DIR/cli.py -q \"sua pergunta\""
fi

echo
echo "📋 Próximos passos:"
echo "1. Configure suas credenciais no arquivo .env"
echo "2. Teste: cloud-analyzer --examples"
echo "3. Execute: cloud-analyzer -q \"Olá, você está funcionando?\""
echo

if [ "$1" = "--venv" ] || [ "$1" = "-v" ]; then
    echo "💡 Para usar o ambiente virtual no futuro:"
    echo "   source .venv/bin/activate"
    echo
fi

echo "📚 Documentação completa: README.md"
echo "🆘 Suporte: https://github.com/your-org/cloud-analyzer/issues"
echo
echo "🔧 Se houver problemas, tente:"
echo "   1. Reiniciar o terminal"
echo "   2. source ~/.zshrc (ou ~/.bashrc)"
echo "   3. python3 cli.py como alternativa" 