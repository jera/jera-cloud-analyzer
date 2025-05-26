#!/usr/bin/env python3
"""
Exemplo prático: Análise de Performance e Tráfego EC2
Demonstra o uso das novas ferramentas CloudWatch do Cloud Insights
"""

import sys
import os
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Carregar variáveis de ambiente
load_dotenv()

from src.ia.agent import run_agent_query


def demonstrate_performance_analysis():
    """Demonstra análises de performance usando o agente IA."""
    print("🚀 " + "="*80)
    print("   ANÁLISE DE PERFORMANCE E TRÁFEGO EC2 - CLOUD INSIGHTS")
    print("="*84)
    print()
    
    # Cenários de demonstração
    scenarios = [
        {
            "title": "📈 Análise de Performance de Instância Específica",
            "description": "Analise métricas completas de CPU, rede e disco",
            "query": "Analise a performance de todas as instâncias EC2 nas últimas 24 horas"
        },
        {
            "title": "🏭 Análise de Frota (Fleet Analysis)", 
            "description": "Compare performance entre múltiplas instâncias",
            "query": "Compare a performance de todas as instâncias EC2 do ambiente production nas últimas 48 horas"
        },
        {
            "title": "🌐 Análise de Tráfego de Rede",
            "description": "Examine bandwidth e custos de transferência de dados",
            "query": "Analise o tráfego de rede das instâncias EC2 dos últimos 7 dias e identifique oportunidades de otimização"
        },
        {
            "title": "💰 Rightsizing e Otimização de Custos",
            "description": "Identifique instâncias subutilizadas para reduzir custos",
            "query": "Identifique instâncias EC2 subutilizadas que posso reduzir para economizar custos"
        },
        {
            "title": "🚨 Detecção de Problemas de Performance",
            "description": "Encontre gargalos e anomalias de performance",
            "query": "Identifique instâncias EC2 com problemas de performance ou utilização anômala"
        }
    ]
    
    print("🎯 CENÁRIOS DE ANÁLISE DISPONÍVEIS:")
    print("-" * 50)
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['title']}")
        print(f"   {scenario['description']}")
        print()
    
    try:
        # Permitir escolha do usuário
        while True:
            choice = input("Escolha um cenário (1-5) ou 'q' para sair: ").strip()
            
            if choice.lower() == 'q':
                print("\n👋 Encerrando demonstração...")
                break
                
            try:
                scenario_idx = int(choice) - 1
                if 0 <= scenario_idx < len(scenarios):
                    scenario = scenarios[scenario_idx]
                    
                    print(f"\n🔄 Executando: {scenario['title']}")
                    print("=" * 60)
                    print(f"Query: {scenario['query']}")
                    print("-" * 60)
                    
                    # Executar a análise
                    run_agent_query(scenario['query'])
                    
                    print("\n" + "="*60)
                    input("Pressione Enter para continuar...")
                    print()
                    
                else:
                    print("❌ Escolha inválida. Digite um número de 1 a 5.")
                    
            except ValueError:
                print("❌ Por favor, digite um número válido.")
                
    except KeyboardInterrupt:
        print("\n\n👋 Demonstração interrompida pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro durante a demonstração: {e}")


def demonstrate_custom_queries():
    """Permite consultas customizadas do usuário."""
    print("\n🎨 " + "="*60)
    print("   CONSULTAS PERSONALIZADAS")
    print("="*64)
    print()
    print("💡 Exemplos de consultas que você pode fazer:")
    print("   • 'Analise a CPU das instâncias taggeadas como Environment=dev'")
    print("   • 'Qual instância tem maior tráfego de rede?'")
    print("   • 'Mostre alertas de performance das últimas 72 horas'")
    print("   • 'Compare custos vs performance das instâncias t3.medium'")
    print()
    
    try:
        while True:
            query = input("🤖 Digite sua consulta (ou 'voltar' para menu anterior): ").strip()
            
            if query.lower() in ['voltar', 'back', 'q']:
                break
                
            if query:
                print("\n🔄 Processando sua consulta...")
                print("-" * 50)
                run_agent_query(query)
                print("\n" + "="*50)
                input("Pressione Enter para nova consulta...")
                print()
            else:
                print("❌ Por favor, digite uma consulta válida.")
                
    except KeyboardInterrupt:
        print("\n\n👋 Voltando ao menu principal...")


def show_capabilities_summary():
    """Mostra resumo das capacidades de análise de performance."""
    print("\n📊 " + "="*60)
    print("   CAPACIDADES DE ANÁLISE DE PERFORMANCE")
    print("="*64)
    print()
    
    capabilities = {
        "🔍 Métricas Coletadas": [
            "CPUUtilization - Utilização de CPU (%)",
            "NetworkIn/Out - Tráfego de rede (bytes)",
            "NetworkPacketsIn/Out - Pacotes de rede",
            "DiskReadOps/WriteOps - Operações de disco",
            "DiskReadBytes/WriteBytes - Throughput de disco",
            "StatusCheckFailed - Falhas de health check"
        ],
        "🚨 Alertas Automáticos": [
            "CPU > 80% - Recomenda upgrade ou otimização", 
            "CPU < 10% - Identifica subutilização",
            "Tráfego > 100 Mbps - Alerta para custos de transferência",
            "Instâncias com comportamento anômalo"
        ],
        "💰 Análises de Custo": [
            "Correlação custo x performance",
            "Rightsizing baseado em dados reais",
            "Estimativa de custos de transferência de dados",
            "Identificação de oportunidades de economia"
        ],
        "🏭 Fleet Analysis": [
            "Comparação entre múltiplas instâncias",
            "Estatísticas da frota (média, mediana, outliers)",
            "Distribuição por tipo de instância",
            "Recomendações de otimização global"
        ]
    }
    
    for category, items in capabilities.items():
        print(f"{category}:")
        for item in items:
            print(f"   ✓ {item}")
        print()
    
    print("🎯 BENEFÍCIOS:")
    print("   • Decisões baseadas em dados reais de performance")
    print("   • Otimização proativa vs reativa")
    print("   • Redução de custos com rightsizing inteligente")
    print("   • Troubleshooting acelerado de problemas")
    print("   • Planejamento de capacidade preciso")
    print()


def main():
    """Função principal da demonstração."""
    print("🌩️ " + "="*80)
    print("   CLOUD INSIGHTS - ANÁLISE DE PERFORMANCE E TRÁFEGO EC2")
    print("="*84)
    print()
    print("Este exemplo demonstra as novas capacidades de análise de performance")
    print("e tráfego das instâncias EC2 usando CloudWatch e Inteligência Artificial.")
    print()
    
    while True:
        print("📋 MENU PRINCIPAL:")
        print("1. 🚀 Demonstrações Guiadas")
        print("2. 🎨 Consultas Personalizadas") 
        print("3. 📊 Resumo de Capacidades")
        print("4. 🚪 Sair")
        print()
        
        choice = input("Escolha uma opção (1-4): ").strip()
        
        if choice == '1':
            demonstrate_performance_analysis()
        elif choice == '2':
            demonstrate_custom_queries()
        elif choice == '3':
            show_capabilities_summary()
            input("\nPressione Enter para voltar ao menu...")
        elif choice == '4':
            print("\n👋 Obrigado por usar o Cloud Insights!")
            print("💡 Para mais informações, consulte:")
            print("   • README.md - Documentação completa")
            print("   • src/ia/tools/README_CLOUDWATCH.md - Docs específicas")
            break
        else:
            print("❌ Opção inválida. Escolha 1, 2, 3 ou 4.")
        
        print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc() 