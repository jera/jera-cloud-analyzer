"""
Script para testar importações.
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    print("Tentando importar AWSClient...")
    from src.clouds.aws.client import AWSClient
    print("✅ Importação do AWSClient bem-sucedida")
    
    print("\nTentando importar CostExplorer...")
    from src.clouds.aws.cost_explorer import CostExplorer
    print("✅ Importação do CostExplorer bem-sucedida")
    
    print("\nTentando importar CostAnalyzer...")
    from src.clouds.aws.cost_analyzer import CostAnalyzer
    print("✅ Importação do CostAnalyzer bem-sucedida")
    
    print("\nTentando importar módulos do agente...")
    from ia.agent import run_agent_query
    print("✅ Importação do agente bem-sucedida")
    
    print("\nTodas as importações funcionaram corretamente! ✨")
    
except Exception as e:
    print(f"\n❌ Erro de importação: {e}")
    print(f"Python path: {sys.path}")
    import traceback
    traceback.print_exc() 