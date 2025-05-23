# Agente de IA para AWS Cloud Insights

Este módulo implementa um agente de IA para análise de custos da AWS utilizando o framework Haystack.

## Funcionamento

O agente utiliza um modelo LLM (Large Language Model) para:

1. **Analisar os dados de custo** obtidos diretamente do AWS Cost Explorer
2. **Interpretar as perguntas dos usuários** em linguagem natural
3. **Gerar recomendações personalizadas** baseadas no contexto específico da conta

## Ferramentas Disponíveis

O agente tem acesso a ferramentas que permitem obter dados concretos da AWS:

- `get_top_services`: Obtém os serviços mais caros em um determinado período
- `get_service_details`: Obtém detalhes específicos de um serviço

## Como Usar

```python
from src.ia.test import run_agent_query

# Execute uma consulta ao agente
run_agent_query("Quais são os serviços mais caros na minha conta AWS?")
run_agent_query("Como posso reduzir meus custos de EC2?")
run_agent_query("Qual a tendência de custo nos últimos meses?")
```

## Vantagens

- **Recomendações contextualizadas**: O agente analisa os dados reais da sua conta
- **Linguagem natural**: Comunicação mais intuitiva com o usuário
- **Conhecimento técnico embutido**: Entende conceitos de AWS e boas práticas
- **Explicações claras**: Fornece justificativas para as recomendações

## Personalização

O prompt do sistema pode ser ajustado para focar em aspectos específicos da análise de custos ou para incluir conhecimentos adicionais sobre práticas de otimização específicas da sua organização. 