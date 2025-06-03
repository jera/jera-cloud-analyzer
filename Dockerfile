# Dockerfile para Cloud Insights MCP Server
FROM python:3.12-slim

# Metadata
LABEL maintainer="Jera Team <contato@jera.com.br>"
LABEL description="Cloud Insights MCP Server - Análise avançada de custos AWS"
LABEL version="2.0.0"

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Instalar uv para gerenciamento de dependências
RUN pip install --no-cache-dir uv

# Copiar arquivos de configuração primeiro (para cache do Docker)
COPY pyproject.toml ./
COPY README.md ./

# Copiar código fonte
COPY src/ src/

# Instalar dependências do projeto no sistema Python
RUN uv pip install --system --no-cache-dir -e .

# Criar usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Configurar variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expor porta (se necessário para modo HTTP)
EXPOSE 8000
EXPOSE 6277
EXPOSE 6274

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.mcp.server; print('OK')" || exit 1

CMD ["fastmcp", "run", "src/mcp/server.py", "-t", "streamable-http"]