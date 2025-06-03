#!/usr/bin/env python3
"""
Script de inicialização do servidor MCP Cloud Insights.
"""

import sys
import os
import asyncio

# Garantir que o projeto está no path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    """Função principal para iniciar o servidor MCP."""
    print("🚀 Iniciando Cloud Insights MCP Server...")
    
    try:
        # Importar e executar o servidor
        from src.mcp.server import run_server
        asyncio.run(run_server())
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Certifique-se de que todas as dependências estão instaladas:")
        print("   uv add mcp")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao iniciar o servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 