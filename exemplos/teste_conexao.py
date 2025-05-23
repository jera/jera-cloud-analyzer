#!/usr/bin/env python3
"""
Script para testar a conexão básica com a AWS.
"""
import sys
import os
import boto3
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
# Carregar variáveis de ambiente
load_dotenv()

def main():
    """
    Função principal para teste de conexão.
    """
    print("=" * 50)
    print("TESTE DE CONEXÃO COM AWS")
    print("=" * 50)
    
    # Definir datas para consulta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Formatar datas
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"Período: {start_str} a {end_str}")
    
    try:
        # 1. Testar sessão AWS
        print("\n1. Criando sessão AWS...")
        session = boto3.Session()
        print(f"   Região: {session.region_name}")
        
        # 2. Testar acesso ao Cost Explorer
        print("\n2. Conectando ao Cost Explorer...")
        ce_client = session.client('ce')
        
        # 3. Fazer uma consulta simples
        print("\n3. Fazendo consulta simples de custo...")
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_str,
                'End': end_str
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        # 4. Exibir resultados
        print("\n4. Resultados da consulta:")
        
        if 'ResultsByTime' in response:
            for period in response['ResultsByTime']:
                period_start = period['TimePeriod']['Start']
                cost = period['Total']['UnblendedCost']['Amount']
                unit = period['Total']['UnblendedCost']['Unit']
                print(f"   {period_start}: {float(cost):.2f} {unit}")
        else:
            print("   Nenhum resultado encontrado")
            
        print("\nConexão com AWS testada com sucesso!")
        
    except Exception as e:
        print(f"\nErro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main() 