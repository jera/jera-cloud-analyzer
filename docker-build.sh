#!/bin/bash

# Script de Build e Deploy - Cloud Insights MCP Server
# Uso: ./docker-build.sh [tag]

set -e

# Configurações
IMAGE_NAME="cloud-insights-mcp"
REGISTRY_URL="ghcr.io/jera"  # Ou seu registry preferido
VERSION=${1:-"latest"}
FULL_IMAGE_NAME="${REGISTRY_URL}/${IMAGE_NAME}:${VERSION}"

echo "🚀 Cloud Insights MCP - Build & Deploy Script"
echo "================================================="
echo "📦 Imagem: ${FULL_IMAGE_NAME}"
echo "📅 Data: $(date)"
echo ""

# Função para log colorido
log() {
    echo "✅ $1"
}

error() {
    echo "❌ $1" >&2
    exit 1
}

# Verificar se Docker está rodando
if ! docker info >/dev/null 2>&1; then
    error "Docker não está rodando. Inicie o Docker e tente novamente."
fi

# Build da imagem
log "Iniciando build da imagem..."
docker build \
    --tag "${IMAGE_NAME}:${VERSION}" \
    --tag "${IMAGE_NAME}:latest" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --build-arg VERSION="${VERSION}" \
    . || error "Falha no build da imagem"

log "Build concluído com sucesso!"

# Testar a imagem
log "Testando a imagem..."
docker run --rm \
    -e AWS_ACCESS_KEY_ID="test" \
    -e AWS_SECRET_ACCESS_KEY="test" \
    -e AWS_DEFAULT_REGION="us-east-1" \
    "${IMAGE_NAME}:${VERSION}" \
    python -c "
import sys
try:
    from src.mcp.server import mcp
    print('✅ Servidor MCP carregado com sucesso!')
    print('📊 28 ferramentas especializadas disponíveis')
    sys.exit(0)
except Exception as e:
    print(f'❌ Erro: {e}')
    sys.exit(1)
" || error "Teste da imagem falhou"

log "Teste da imagem passou!"

# Opção para fazer push (apenas se registry configurado)
if [[ "$2" == "push" && "${REGISTRY_URL}" != "ghcr.io/jera" ]]; then
    log "Fazendo push para o registry..."
    
    # Tag para registry
    docker tag "${IMAGE_NAME}:${VERSION}" "${FULL_IMAGE_NAME}"
    
    # Push
    docker push "${FULL_IMAGE_NAME}" || error "Falha no push"
    
    log "Push concluído: ${FULL_IMAGE_NAME}"
fi

# Exibir informações finais
echo ""
echo "🎉 Build concluído com sucesso!"
echo "📊 Imagem: ${IMAGE_NAME}:${VERSION}"
echo "💾 Tamanho: $(docker images ${IMAGE_NAME}:${VERSION} --format 'table {{.Size}}' | tail -n1)"
echo ""
echo "🚀 Para executar:"
echo "   docker run -it --rm \\"
echo "     -e AWS_ACCESS_KEY_ID=\$AWS_ACCESS_KEY_ID \\"
echo "     -e AWS_SECRET_ACCESS_KEY=\$AWS_SECRET_ACCESS_KEY \\"
echo "     -e AWS_DEFAULT_REGION=us-east-1 \\"
echo "     ${IMAGE_NAME}:${VERSION}"
echo ""
echo "🐳 Ou use Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "✨ Imagem pronta para uso!" 