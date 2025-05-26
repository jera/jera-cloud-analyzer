"""
Agente de IA para análise de custos AWS.
"""

import sys
import os
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage

# Importar todas as ferramentas da pasta tools
from src.ia.tools import ALL_TOOLS
# Importar o prompt do sistema
from src.ia.system_prompt import SYSTEM_PROMPT


# Configurar o agente
cost_analyzer = Agent(
    chat_generator=OpenAIChatGenerator(model="gpt-4o-mini"),
    tools=ALL_TOOLS,
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


# Executar o agente com uma pergunta de exemplo
if __name__ == "__main__":
    query = f"Mostre recursos sem tags de governança"
    run_agent_query(query)