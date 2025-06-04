"""
Agente de IA para análise de custos AWS.
"""

import sys
import os
import argparse
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage

from src.adapters.haystack_tools import HAYSTACK_TOOLS
from src.ia.system_prompt import SYSTEM_PROMPT

cost_analyzer = Agent(
    chat_generator=OpenAIChatGenerator(model=os.getenv("OPENAI_MODEL"), generation_kwargs={"max_tokens": 10000}),
    tools=HAYSTACK_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    exit_conditions=["text"],
    max_agent_steps=10,
    raise_on_tool_invocation_failure=False
)


def run_agent_query(query: str):
    """
    Executa uma consulta no agente.
    
    Args:
        query: Pergunta do usuário
        
    Returns:
        Resposta do agente
    """
    try:
        # Aquecer o agente (inicialização)
        cost_analyzer.warm_up()
        
        # Executar a consulta
        response = cost_analyzer.run(messages=[ChatMessage.from_user(query)])
        
        # Exibir a resposta
        print("\n" + "=" * 80)
        print("RESPOSTA DO AGENTE:")
        print("=" * 80)
        
        print(response["messages"][-1].text)
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\nErro ao executar o agente: {str(e)}")
        import traceback
        traceback.print_exc()


def interactive_mode():
    """Modo interativo para múltiplas consultas."""
    print("🤖 " + "=" * 70)
    print("   Jera Cloud Analyzer - AGENTE DE IA INTERATIVO")
    print("=" * 74)
    print()
    print("💡 Digite suas perguntas sobre custos e performance AWS")
    print("   Comandos especiais:")
    print("   • 'help' - Mostra exemplos de consultas")
    print("   • 'exit' ou 'quit' - Sair do modo interativo")
    print("   • 'clear' - Limpar a tela")
    print()
    
    while True:
        try:
            query = input("🔍 Sua pergunta: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['exit', 'quit', 'sair']:
                print("\n👋 Encerrando agente. Até mais!")
                break
                
            elif query.lower() == 'clear':
                os.system('clear' if os.name == 'posix' else 'cls')
                continue
                
            elif query.lower() == 'help':
                show_help_examples()
                continue
                
            # Executar a consulta
            run_agent_query(query)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrompido pelo usuário. Até mais!")
            break
        except EOFError:
            print("\n\n👋 Encerrando agente. Até mais!")
            break


def show_help_examples():
    """Mostra exemplos de consultas para o usuário."""
    print("\n📚 " + "=" * 60)
    print("   EXEMPLOS DE CONSULTAS")
    print("=" * 64)
    print()
    
    examples = {
        "💰 Análise de Custos": [
            "Quais são os 10 serviços mais caros do último mês?",
            "Compare os custos de janeiro vs fevereiro",
            "Mostre custos por tag Environment",
            "Identifique anomalias nos gastos de EC2"
        ],
        "⚡ Performance e Tráfego": [
            "Analise a performance de todas instâncias EC2 running",
            "Qual instância tem maior tráfego de rede?",
            "Identifique instâncias subutilizadas",
            "Compare performance do ambiente production"
        ],
        "🔍 Descoberta e Governança": [
            "Descubra recursos sem tags de governança",
            "Liste todas as instâncias por projeto",
            "Encontre instâncias taggeadas como Environment=dev",
            "Analise cobertura de recursos da conta"
        ],
        "🎯 Otimização": [
            "Como posso reduzir custos de S3?",
            "Recomende otimizações para RDS",
            "Projete gastos para os próximos 3 meses",
            "Analise oportunidades de rightsizing"
        ]
    }
    
    for category, queries in examples.items():
        print(f"{category}:")
        for query in queries:
            print(f"   • \"{query}\"")
        print()
    
    print("💡 Dica: Seja específico sobre períodos, serviços ou tags!")
    print()


def main():
    """Função principal com suporte a argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="🤖 Jera Cloud Analyzer - Agente de IA para análise de custos e performance AWS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Consulta direta
  python3 src/ia/agent.py "Quais são os 5 serviços mais caros?"
  
  # Análise de performance
  python3 src/ia/agent.py "Analise performance das instâncias EC2 running"
  
  # Modo interativo
  python3 src/ia/agent.py --interactive
  
  # Consulta com aspas simples
  python3 src/ia/agent.py 'Compare custos por tag Environment'

🌩️ Para mais informações: https://github.com/seu-repo/cloud-insights
        """
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Pergunta para o agente de IA (use aspas para perguntas com espaços)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Iniciar modo interativo para múltiplas consultas"
    )
    
    parser.add_argument(
        "--examples", "-e",
        action="store_true", 
        help="Mostrar exemplos de consultas"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Mostrar versão do Jera Cloud Analyzer"
    )
    
    args = parser.parse_args()
    
    # Mostrar versão
    if args.version:
        print("🌩️ Jera Cloud Analyzer v2.0.0")
        print("   Agente de IA para análise de custos e performance AWS")
        print("   Ferramentas disponíveis: 28")
        print("   Suporte: Custos + Performance + Tráfego EC2 + CloudWatch + Serviços")
        return
    
    # Mostrar exemplos
    if args.examples:
        show_help_examples()
        return
    
    # Modo interativo
    if args.interactive:
        interactive_mode()
        return
    
    # Executar consulta direta
    if args.query:
        print(f"🤖 Processando: \"{args.query}\"")
        run_agent_query(args.query)
        return
    
    # Se nenhum argumento foi fornecido, mostrar ajuda
    print("🌩️ Jera Cloud Analyzer - Agente de IA para AWS")
    print()
    print("❌ Nenhuma consulta fornecida.")
    print()
    print("📖 Para ver opções disponíveis:")
    print("   python3 src/ia/agent.py --help")
    print()
    print("💡 Exemplos rápidos:")
    print("   python3 src/ia/agent.py \"Mostre os 5 serviços mais caros\"")
    print("   python3 src/ia/agent.py --interactive")
    print("   python3 src/ia/agent.py --examples")


if __name__ == "__main__":
    main()