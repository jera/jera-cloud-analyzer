#!/usr/bin/env python3
"""
Exemplo de uso da análise de tags com serviços associados.
"""
import json
import sys
import os
from datetime import datetime, timedelta

# Adicionando o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
# Carregar variáveis de ambiente
load_dotenv()

from src.main import analyze_all_tags_with_services, analyze_tag_costs
from clouds.aws.utils import DecimalEncoder

def main():
    """
    Demonstração da análise de custos por tag e serviços associados.
    """
    # Definir período para a análise (últimos 30 dias)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print("=" * 80)
    print("ANÁLISE DE CUSTOS POR TAG E SERVIÇOS ASSOCIADOS")
    print("=" * 80)
    print(f"Período: {start_date} a {end_date}")
    print()
    
    # Obter análise de todas as tags com serviços
    print("Obtendo análise de todas as tags...")
    resultado = analyze_all_tags_with_services(start_date, end_date)
    
    # Verificar se há tags disponíveis
    if not resultado.get('tags'):
        print(resultado.get('message', 'Nenhuma tag encontrada ou erro na consulta.'))
        return
    
    # Exibir resultado para cada tag
    for tag_info in resultado['tags']:
        tag_key = tag_info['tag_key']
        total_cost = tag_info['total_cost']
        
        print(f"\n\n{'=' * 40}")
        print(f"TAG: {tag_key}")
        print(f"{'=' * 40}")
        print(f"Custo total: ${total_cost:.2f}")
        print(f"Custo não tagueado: ${tag_info['untagged_cost']:.2f} ({tag_info['untagged_percentage']:.2f}%)")
        print("\nVALORES DA TAG:")
        
        # Exibir os valores da tag
        for i, valor in enumerate(tag_info['values']):
            tag_value = valor['tag_value']
            valor_cost = valor['cost']
            percentual = valor['percentage']
            
            print(f"\n{i+1}. {tag_value}")
            print(f"   Custo: ${valor_cost:.2f} ({percentual:.2f}%)")
            
            # Exibir os serviços associados a este valor de tag
            if valor.get('services'):
                print("   Serviços:")
                for service in valor['services']:
                    service_name = service['service']
                    service_cost = service['cost']
                    print(f"     - {service_name}: ${service_cost:.2f}")
            else:
                print("   Nenhum serviço encontrado para este valor de tag.")
    
    print("\n\n" + "=" * 80)
    print("Para análise detalhada de uma tag específica, use:")
    print("analyze_tag_costs('nome_da_tag')")
    print("=" * 80)


if __name__ == "__main__":
    main() 