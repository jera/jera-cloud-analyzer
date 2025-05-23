"""
Módulo principal para análise de custos AWS.
"""
import json
import sys
import os
from typing import Dict, Any

# Ajustar o caminho do sistema para poder importar os módulos corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clouds.aws.client import AWSClient
from clouds.aws.cost_explorer import CostExplorer
from clouds.aws.cost_analyzer import CostAnalyzer
from clouds.aws.utils import DecimalEncoder
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env se existir
load_dotenv()

def get_cost_overview(start_date=None, end_date=None) -> Dict[str, Any]:
    """
    Obtém uma visão geral dos custos da AWS.
    
    Args:
        start_date: Data inicial opcional (formato YYYY-MM-DD)
        end_date: Data final opcional (formato YYYY-MM-DD)
        
    Returns:
        Dicionário com informações de custo
    """
    cost_explorer = CostExplorer()
    analyzer = CostAnalyzer(cost_explorer)
    
    # Obter os serviços mais caros
    top_services = analyzer.get_top_services(limit=20, start_date=start_date, end_date=end_date)
    
    # Obter tendências de custo
    cost_trends = analyzer.get_cost_trends(months=6)
    
    # Comentado temporariamente para evitar problemas com datas
    # anomalies = analyzer.get_cost_anomalies(threshold_percent=20.0)
    
    return {
        "top_services": top_services,
        "cost_trends": cost_trends,
        "anomalies": []  # Lista vazia temporariamente
    }





def analyze_tag_costs(tag_key: str, start_date=None, end_date=None) -> Dict[str, Any]:
    """
    Analisa custos com base em uma tag específica.
    
    Args:
        tag_key: Chave da tag para análise
        start_date: Data inicial opcional (formato YYYY-MM-DD)
        end_date: Data final opcional (formato YYYY-MM-DD)
        
    Returns:
        Análise detalhada dos custos por tag
    """
    cost_explorer = CostExplorer()
    analyzer = CostAnalyzer(cost_explorer)
    
    return analyzer.get_cost_by_tag_analysis(tag_key, start_date, end_date)


def analyze_all_tags_with_services(start_date=None, end_date=None) -> Dict[str, Any]:
    """
    Analisa todas as tags disponíveis, mostrando custos e serviços associados.
    
    Args:
        start_date: Data inicial opcional (formato YYYY-MM-DD)
        end_date: Data final opcional (formato YYYY-MM-DD)
        
    Returns:
        Análise detalhada de todas as tags com serviços associados
    """
    cost_explorer = CostExplorer()
    analyzer = CostAnalyzer(cost_explorer)
    
    return analyzer.analyze_all_tags_with_services(start_date, end_date)

def get_available_tags() -> Dict[str, Any]:
    """
    Obtém todas as tags disponíveis para análise.
    
    Returns:
        Lista de tags disponíveis
    """
    cost_explorer = CostExplorer()
    return cost_explorer.get_tags()


def get_service_details(service_name: str, start_date=None, end_date=None) -> Dict[str, Any]:
    """
    Obtém detalhes de custos para um serviço específico.
    
    Args:
        service_name: Nome do serviço AWS
        start_date: Data inicial opcional (formato YYYY-MM-DD)
        end_date: Data final opcional (formato YYYY-MM-DD)
        
    Returns:
        Detalhes de custo do serviço
    """
    cost_explorer = CostExplorer()
    return cost_explorer.get_service_details(service_name, start_date, end_date)


def main():
    """
    Função principal de exemplo.
    """
    print("AWS Cloud Insights - Análise de Custos")
    print("-" * 50)
    
    try:
        # Exemplo: Obter visão geral de custos
        print("\nObtendo análise de custos...")
        cost_overview = get_cost_overview()
        # print(cost_overview)
        print("\nTop 5 Serviços (por custo):")
        for service in cost_overview.get("top_services", []):
            print(f"  - {service['service']}: ${service['cost']:.2f} {service['unit']}")
        

        # # Exemplo: Tendência de custos
        # trends = cost_overview.get("cost_trends", {})
        # print(f"\nTendência geral: {trends.get('total_change', 0):.2f}% nos últimos 6 meses")
        
        # # As recomendações agora são geradas automaticamente pelo agente de IA
        # # com base nos dados específicos da conta
        
        # # Exemplo: Analisar custos por tag com serviços
        # print("\nPara análise detalhada de tags e serviços associados, use:")
        # print("  analyze_all_tags_with_services()")
        
    except Exception as e:
        print(f"\nErro durante a execução: {str(e)}")
        import traceback
        traceback.print_exc()
        
    print("\nUse as funções específicas para análises mais detalhadas.")


if __name__ == "__main__":
    main() 