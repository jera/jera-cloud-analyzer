# 🛠️ Ferramentas do Agente de IA

Este diretório contém todas as ferramentas especializadas utilizadas pelo agente de IA para análise de custos AWS, organizadas de forma modular para melhor manutenibilidade e extensibilidade.

## 📁 **Estrutura dos Arquivos**

```
tools/
├── __init__.py              # Importações centralizadas e lista ALL_TOOLS
├── aws_data_tools.py        # Ferramentas de coleta de dados AWS
├── utility_tools.py         # Ferramentas utilitárias (datas, formatação)
└── README.md               # Esta documentação
```

## 🔧 **Categorias de Ferramentas**

### **1. Ferramentas de Dados AWS (`aws_data_tools.py`)**

Ferramentas especializadas para interação com APIs AWS e coleta de dados de custos:

| **Ferramenta** | **Descrição** | **Uso Principal** |
|----------------|---------------|-------------------|
| `get_top_services` | Obtém serviços mais caros | Identificação de maiores custos |
| `get_service_details` | Detalhes de um serviço específico | Drill-down em serviços |
| `get_aws_tags` | Lista tags disponíveis | Análise de governança |
| `get_dimension_values` | Valores de dimensões específicas | Exploração de dimensões |
| `discover_account_resources` | Discovery completo da conta | Mapeamento de infraestrutura |
| `validate_and_analyze_service` | Validação e análise de serviços | Verificação de existência |
| `analyze_account_coverage` | Cobertura da conta por dimensões | Análise de padrões |
| `get_account_context_data` | Dados contextuais abrangentes | Contexto para análises |

### **2. Ferramentas Utilitárias (`utility_tools.py`)**

Ferramentas para processamento e formatação de dados:

| **Ferramenta** | **Descrição** | **Uso Principal** |
|----------------|---------------|-------------------|
| `format_currency` | Conversão USD→BRL em tempo real | Formatação monetária |
| `get_current_date` | Data atual no formato YYYY-MM-DD | Cálculos temporais |
| `get_date_from_period` | Data específica por dia/mês/ano | Construção de períodos |
| `all_dimensions` | Lista todas dimensões disponíveis | Referência de dimensões |

## 🔄 **Fluxo de Importação**

```python
# 1. Arquivo __init__.py importa de ambos os módulos
from .aws_data_tools import (...)
from .utility_tools import (...)

# 2. Cria a lista ALL_TOOLS com todas as ferramentas
ALL_TOOLS = [todas_as_ferramentas...]

# 3. Agent.py importa apenas ALL_TOOLS
from .tools import ALL_TOOLS
```

## 🎯 **Padrões de Implementação**

### **Estrutura Padrão de uma Tool**

```python
@tool
def nome_da_ferramenta(param1: tipo, param2: Optional[tipo] = None) -> str:
    """
    Descrição clara da funcionalidade.
    
    Args:
        param1: Descrição do parâmetro obrigatório
        param2: Descrição do parâmetro opcional
        
    Returns:
        Descrição do retorno (sempre string para compatibilidade)
    """
    try:
        # Lógica da ferramenta
        result = fazer_algo()
        return json.dumps(result, cls=JsonEncoder, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Erro: {str(e)}"
```

### **Convenções de Nomenclatura**

- **Prefixos funcionais**: `get_`, `analyze_`, `discover_`, `validate_`
- **Nomes descritivos**: indicam claramente a funcionalidade
- **Snake_case**: padrão Python para funções

### **Tratamento de Erros**

- **Try/except** obrigatório em todas as tools
- **Retorno sempre string** para compatibilidade com Haystack
- **Logs informativos** para debugging (prints estratégicos)

## 🔄 **Adicionando Novas Ferramentas**

### **1. Para ferramentas AWS:**
1. Adicione a função em `aws_data_tools.py`
2. Use o decorator `@tool`
3. Importe a ferramenta em `__init__.py`
4. Adicione à lista `ALL_TOOLS`

### **2. Para ferramentas utilitárias:**
1. Adicione a função em `utility_tools.py`
2. Siga o mesmo processo de importação

### **3. Para nova categoria:**
1. Crie novo arquivo `categoria_tools.py`
2. Adicione importação em `__init__.py`
3. Inclua ferramentas em `ALL_TOOLS`

## 📊 **Monitoramento e Debug**

### **Logs Implementados**
- Todas as ferramentas AWS incluem prints informativos
- Parâmetros de entrada são logados
- Erros são capturados e reportados

### **Exemplo de Log**
```
GET TOP SERVICES DATE 2024-01-01 2024-01-31
CHAMANDO DISCOVER_ACCOUNT_RESOURCES
GET DIMENSION VALUES SERVICE
```

## 🚀 **Benefícios da Modularização**

1. **Manutenibilidade**: Cada categoria em arquivo separado
2. **Testabilidade**: Ferramentas podem ser testadas independentemente
3. **Reutilização**: Tools podem ser importadas individualmente
4. **Escalabilidade**: Fácil adição de novas ferramentas
5. **Organização**: Separação clara de responsabilidades

## 📝 **Dependências**

### **Internas**
- `src.clouds.aws.cost_explorer`
- `src.clouds.aws.cost_analyzer`

### **Externas**
- `haystack.tools` (decorator @tool)
- `requests` (para API de cotação)
- `json`, `datetime` (built-ins Python)

---

**💡 Esta estrutura modular facilita a manutenção e extensão das capacidades do agente de IA.** 