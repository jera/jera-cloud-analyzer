import sys
import os
import json
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Carregar variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv()

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.builders.chat_prompt_builder import ChatPromptBuilder
from haystack.core.pipeline import Pipeline
from haystack.tools import tool
from haystack.document_stores.in_memory import InMemoryDocumentStore
from typing import Optional, Dict, List, Any
from haystack.dataclasses import ChatMessage, Document

document_store = InMemoryDocumentStore()

# Importações usando o caminho completo
from src.clouds.aws.cost_explorer import CostExplorer
from src.clouds.aws.cost_analyzer import CostAnalyzer
from src.clouds.aws.utils import DecimalEncoder

class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        from decimal import Decimal
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)
    
@tool
def all_dimensions() -> str:
    """
    Obtém todas as dimensões disponíveis.
    """
    ALL_VALID_DIMENSIONS = {
        'COST_AND_USAGE': [
            'AZ', 'INSTANCE_TYPE', 'LINKED_ACCOUNT', 'LINKED_ACCOUNT_NAME',
            'OPERATION', 'PURCHASE_TYPE', 'REGION', 'SERVICE', 'SERVICE_CODE',
            'USAGE_TYPE', 'USAGE_TYPE_GROUP', 'RECORD_TYPE', 'OPERATING_SYSTEM',
            'TENANCY', 'SCOPE', 'PLATFORM', 'SUBSCRIPTION_ID', 'LEGAL_ENTITY_NAME',
            'DEPLOYMENT_OPTION', 'DATABASE_ENGINE', 'CACHE_ENGINE',
            'INSTANCE_TYPE_FAMILY', 'BILLING_ENTITY', 'RESERVATION_ID',
            'RESOURCE_ID', 'RIGHTSIZING_TYPE', 'SAVINGS_PLANS_TYPE',
            'SAVINGS_PLAN_ARN', 'PAYMENT_OPTION', 'AGREEMENT_END_DATE_TIME_AFTER',
            'AGREEMENT_END_DATE_TIME_BEFORE', 'INVOICING_ENTITY',
            'ANOMALY_TOTAL_IMPACT_ABSOLUTE', 'ANOMALY_TOTAL_IMPACT_PERCENTAGE'
        ],
        'RESERVATIONS': [
            'AZ', 'CACHE_ENGINE', 'DEPLOYMENT_OPTION', 'INSTANCE_TYPE',
            'LINKED_ACCOUNT', 'PLATFORM', 'REGION', 'SCOPE', 'TAG', 'TENANCY'
        ],
        'SAVINGS_PLANS': [
            'SAVINGS_PLANS_TYPE', 'PAYMENT_OPTION', 'REGION',
            'INSTANCE_TYPE_FAMILY', 'LINKED_ACCOUNT', 'SAVINGS_PLAN_ARN'
        ]
    }
    return ALL_VALID_DIMENSIONS

@tool
def format_currency(value: float) -> str:
    """
    Formata um valor float para uma string no formato de moeda,
    convertendo de dólar para real usando a cotação atual.
    """
    try:
        import requests
        # Buscar cotação atual do dólar
        response = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL")
        data = response.json()
        cotacao = float(data["USDBRL"]["bid"])
        
        # Converter valor de dólar para real
        valor_em_reais = value * cotacao
        return f"R$ {valor_em_reais:.2f}"
    except Exception as e:
        # Em caso de erro na API, usa o valor de fallback de 6 reais por dólar
        valor_em_reais = value * 6.0
        return f"R$ {valor_em_reais:.2f}"

@tool
def get_current_date() -> str:
    """
    Obtém a data atual no formato YYYY-MM-DD.
    """
    print("GET CURRENT DATE")
    return datetime.now().strftime('%Y-%m-%d')

@tool
def get_date_from_period(dia: int = None, mes: int = None, ano: int = None) -> str:
    """
    Obtém uma data específica a partir de dia, mês e ano fornecidos.
    Se algum parâmetro não for fornecido, usa o valor atual.
    
    Args:
        dia: Dia do mês (1-31)
        mes: Mês do ano (1-12)
        ano: Ano (ex: 2023)
        
    Returns:
        Data no formato YYYY-MM-DD
    """
    print("GET DATE FROM PERIOD", dia, mes, ano)
    data_atual = datetime.now()
    
    # Usar valores atuais para parâmetros não fornecidos
    dia_final = dia if dia is not None else data_atual.day
    mes_final = mes if mes is not None else data_atual.month
    ano_final = ano if ano is not None else data_atual.year
    
    try:
        # Criar objeto datetime com os valores fornecidos
        data = datetime(ano_final, mes_final, dia_final)
        return data.strftime('%Y-%m-%d')
    except ValueError as e:
        # Tratar erros como datas inválidas (ex: 31 de fevereiro)
        return f"Erro: Data inválida - {str(e)}"

@tool
def get_top_services(start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 5) -> str:
    """
    Obtém os serviços mais caros da AWS no período especificado.
    
    Args:
        start_date: Data inicial no formato YYYY-MM-DD. Se não fornecido, será considerado 30 dias atrás.
        end_date: Data final no formato YYYY-MM-DD. Se não fornecido, será considerada a data atual.
        limit: Número máximo de serviços a retornar (padrão: 5)
        
    Returns:
        Lista dos serviços mais caros, ordenados por custo (do maior para o menor)
    """
    try:
        print("GET TOP SERVICES DATE", start_date, end_date)
        # Definir datas padrão se não fornecidas
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        # Obter os serviços mais caros
        print("GET TOP SERVICES DATE", start_date, end_date)
        cost_explorer = CostExplorer()
        analyzer = CostAnalyzer(cost_explorer)
        top_services = analyzer.get_top_services(limit=limit, start_date=start_date, end_date=end_date)
        
        # Formatar a resposta como string
        result = json.dumps(top_services, cls=JsonEncoder, ensure_ascii=False, indent=2)
        print("GET TOP SERVICES", result)
        return result
        
    except Exception as e:
        return f"Erro ao obter serviços: {str(e)}"

@tool
def get_service_details(service_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Obtém detalhes de custo de um serviço específico.
    
    Args:
        service_name: Nome do serviço AWS (ex: 'Amazon EC2', 'Amazon S3')
        start_date: Data inicial no formato YYYY-MM-DD
        end_date: Data final no formato YYYY-MM-DD
        
    Returns:
        Detalhes de custo do serviço especificado
    """
    print("GET SERVICE DETAILS DATE", service_name, start_date, end_date)
    try:
        # Definir datas padrão se não fornecidas
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        # Obter detalhes do serviço
        cost_explorer = CostExplorer()
        service_details = cost_explorer.get_service_details(service_name, start_date, end_date)
        
        # Formatar a resposta como string
        result = json.dumps(service_details, cls=JsonEncoder, ensure_ascii=False, indent=2)
        # print("GET SERVICE DETAILS", result)
        return result
        
    except Exception as e:
        print("GET SERVICE DETAILS ERROR", e)
        return f"Erro ao obter detalhes do serviço: {str(e)}"

@tool
def get_aws_tags() -> str:
    """
    Obtém as tags da AWS.
    """
    cost_explorer = CostExplorer()
    tags = cost_explorer.get_tags()
    print("GET AWS TAGS", tags)
    try:
        return tags
    except Exception as e:
        return f"Erro ao obter tags: {str(e)}"

@tool
def get_dimension_values(dimension_name: str) -> str:
    """
    Obtém os valores de uma dimensão específica.
    Args:
        dimension_name: Dimensão desejada ('SERVICE', 'USAGE_TYPE', 'INSTANCE_TYPE', etc.)
    """
    cost_explorer = CostExplorer()
    print("GET DIMENSION VALUES", dimension_name)
    try:
        dimension_values = cost_explorer.get_dimension_values(dimension_name)
        return dimension_values
    except Exception as e:
        return f"Erro ao obter valores da dimensão: {str(e)}"

@tool
def discover_account_resources() -> str:
    """
    Descobre todos os recursos ativos na conta AWS.
    
    Returns:
        JSON com dados sobre serviços, regiões, tipos de instância e contas descobertos
    """
    print("CHAMANDO DISCOVER_ACCOUNT_RESOURCES")
    try:
        cost_explorer = CostExplorer()
        
        # Descoberta de serviços ativos
        services_response = cost_explorer.get_dimension_values(dimension='SERVICE')
        active_services = [item['Value'] for item in services_response['DimensionValues']]
        
        # Descoberta de regiões em uso
        regions_response = cost_explorer.get_dimension_values(dimension='REGION')
        active_regions = [item['Value'] for item in regions_response['DimensionValues']]
        
        # Descoberta de tipos de instância
        instances_response = cost_explorer.get_dimension_values(dimension='INSTANCE_TYPE')
        instance_types = [item['Value'] for item in instances_response['DimensionValues']]
        
        # Descoberta de contas vinculadas
        try:
            accounts_response = cost_explorer.get_dimension_values(dimension='LINKED_ACCOUNT')
            linked_accounts = [item['Value'] for item in accounts_response['DimensionValues']]
        except:
            linked_accounts = []
        
        # Descoberta de tipos de compra
        try:
            purchase_response = cost_explorer.get_dimension_values(dimension='PURCHASE_TYPE')
            purchase_types = [item['Value'] for item in purchase_response['DimensionValues']]
        except:
            purchase_types = []
        
        # Descoberta de sistemas operacionais
        try:
            os_response = cost_explorer.get_dimension_values(dimension='OPERATING_SYSTEM')
            operating_systems = [item['Value'] for item in os_response['DimensionValues']]
        except:
            operating_systems = []
        
        discovery_data = {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "total_count": len(active_services),
                "list": active_services
            },
            "regions": {
                "total_count": len(active_regions),
                "list": active_regions
            },
            "instance_types": {
                "total_count": len(instance_types),
                "list": instance_types
            },
            "linked_accounts": {
                "total_count": len(linked_accounts),
                "list": linked_accounts,
                "is_multi_account": len(linked_accounts) > 1
            },
            "purchase_types": {
                "total_count": len(purchase_types),
                "list": purchase_types
            },
            "operating_systems": {
                "total_count": len(operating_systems),
                "list": operating_systems
            }
        }
        
        return json.dumps(discovery_data, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Erro na descoberta de recursos: {str(e)}"}, ensure_ascii=False)

@tool
def validate_and_analyze_service(service_name: str) -> str:
    """
    Valida se um serviço existe na conta e retorna análise detalhada.
    
    Args:
        service_name: Nome do serviço AWS a validar e analisar
        
    Returns:
        JSON com status de validação e dados do serviço (se encontrado)
    """
    print("CHAMANDO VALIDATE_AND_ANALYZE_SERVICE", service_name)
    try:
        cost_explorer = CostExplorer()
        
        # Descobre serviços disponíveis
        services_response = cost_explorer.get_dimension_values(dimension='SERVICE')
        available_services = [item['Value'] for item in services_response['DimensionValues']]
        
        # Validação
        service_exists = service_name in available_services
        
        if not service_exists:
            # Busca serviços similares
            similar_services = [s for s in available_services if service_name.lower() in s.lower()]
            
            return json.dumps({
                "service_name": service_name,
                "exists": False,
                "similar_services": similar_services,
                "all_available_services": available_services
            }, ensure_ascii=False, indent=2)
        
        # Se existe, coleta dados detalhados
        service_details = cost_explorer.get_service_details(service_name)
        
        # Descobre usage types relacionados
        usage_types_response = cost_explorer.get_dimension_values(dimension='USAGE_TYPE')
        all_usage_types = [item['Value'] for item in usage_types_response['DimensionValues']]
        
        # Filtra usage types que realmente têm custos para este serviço
        service_usage_types = []
        for usage_type in all_usage_types[:50]:  # Limita para evitar muitas calls
            try:
                test_response = cost_explorer.client.get_cost_and_usage(
                    TimePeriod={
                        'Start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                        'End': datetime.now().strftime('%Y-%m-%d')
                    },
                    Granularity='DAILY',
                    Metrics=['UnblendedCost'],
                    Filter={
                        'And': [
                            {'Dimensions': {'Key': 'SERVICE', 'Values': [service_name]}},
                            {'Dimensions': {'Key': 'USAGE_TYPE', 'Values': [usage_type]}}
                        ]
                    }
                )
                
                # Verifica se há dados reais
                has_costs = any(
                    any(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0') != '0' 
                        for group in period.get('Groups', []))
                    for period in test_response.get('ResultsByTime', [])
                )
                
                if has_costs:
                    service_usage_types.append(usage_type)
                    
            except:
                continue
        
        # Descobre regiões onde o serviço tem custos
        service_regions = []
        try:
            regions_response = cost_explorer.get_dimension_values(dimension='REGION')
            for region_item in regions_response['DimensionValues']:
                region = region_item['Value']
                try:
                    region_test = cost_explorer.client.get_cost_and_usage(
                        TimePeriod={
                            'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                            'End': datetime.now().strftime('%Y-%m-%d')
                        },
                        Granularity='MONTHLY',
                        Metrics=['UnblendedCost'],
                        Filter={
                            'And': [
                                {'Dimensions': {'Key': 'SERVICE', 'Values': [service_name]}},
                                {'Dimensions': {'Key': 'REGION', 'Values': [region]}}
                            ]
                        }
                    )
                    
                    has_costs = any(
                        float(period.get('Total', {}).get('UnblendedCost', {}).get('Amount', '0')) > 0
                        for period in region_test.get('ResultsByTime', [])
                    )
                    
                    if has_costs:
                        service_regions.append(region)
                        
                except:
                    continue
        except:
            pass
        
        analysis_result = {
            "service_name": service_name,
            "exists": True,
            "service_details": service_details,
            "usage_types": {
                "count": len(service_usage_types),
                "list": service_usage_types
            },
            "regions": {
                "count": len(service_regions),
                "list": service_regions
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(analysis_result, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Erro na validação do serviço: {str(e)}"}, ensure_ascii=False)

@tool
def analyze_account_coverage() -> str:
    """
    Analisa a cobertura geral da conta AWS em diferentes dimensões.
    
    Returns:
        JSON com análise completa de cobertura da conta
    """
    print("CHAMANDO ANALYZE_ACCOUNT_COVERAGE")
    try:
        cost_explorer = CostExplorer()
        
        coverage_data = {
            "analysis_timestamp": datetime.now().isoformat(),
            "dimensions_analysis": {}
        }
        
        # Análise de regiões
        try:
            regions_response = cost_explorer.get_dimension_values(dimension='REGION')
            regions_data = [item['Value'] for item in regions_response['DimensionValues']]
            coverage_data["dimensions_analysis"]["regions"] = {
                "total_count": len(regions_data),
                "list": regions_data,
                "is_multi_region": len(regions_data) > 1
            }
        except Exception as e:
            coverage_data["dimensions_analysis"]["regions"] = {"error": str(e)}
        
        # Análise de tipos de compra
        try:
            purchase_response = cost_explorer.get_dimension_values(dimension='PURCHASE_TYPE')
            purchase_data = [item['Value'] for item in purchase_response['DimensionValues']]
            coverage_data["dimensions_analysis"]["purchase_types"] = {
                "total_count": len(purchase_data),
                "list": purchase_data,
                "has_reserved": any('Reserved' in pt for pt in purchase_data),
                "has_savings_plans": any('Savings' in pt for pt in purchase_data),
                "has_ondemand": any('OnDemand' in pt for pt in purchase_data),
                "is_only_ondemand": purchase_data == ['OnDemand'] if purchase_data else False
            }
        except Exception as e:
            coverage_data["dimensions_analysis"]["purchase_types"] = {"error": str(e)}
        
        # Análise de tags
        try:
            tags_response = cost_explorer.get_tags()
            tags_data = tags_response.get('Tags', [])
            coverage_data["dimensions_analysis"]["tags"] = {
                "total_count": len(tags_data),
                "list": tags_data,
                "has_governance_tags": len(tags_data) > 0
            }
        except Exception as e:
            coverage_data["dimensions_analysis"]["tags"] = {"error": str(e)}
        
        # Análise de sistemas operacionais
        try:
            os_response = cost_explorer.get_dimension_values(dimension='OPERATING_SYSTEM')
            os_data = [item['Value'] for item in os_response['DimensionValues']]
            coverage_data["dimensions_analysis"]["operating_systems"] = {
                "total_count": len(os_data),
                "list": os_data,
                "has_windows": any('Windows' in os for os in os_data),
                "has_linux": any('Linux' in os for os in os_data),
                "is_mixed_environment": len(os_data) > 1
            }
        except Exception as e:
            coverage_data["dimensions_analysis"]["operating_systems"] = {"error": str(e)}
        
        # Análise de tipos de instância
        try:
            instances_response = cost_explorer.get_dimension_values(dimension='INSTANCE_TYPE')
            instances_data = [item['Value'] for item in instances_response['DimensionValues']]
            
            # Categoriza instâncias por geração
            legacy_instances = [inst for inst in instances_data if any(gen in inst for gen in ['t1.', 't2.', 'm1.', 'm3.', 'c1.', 'c3.'])]
            current_instances = [inst for inst in instances_data if inst not in legacy_instances]
            
            coverage_data["dimensions_analysis"]["instance_types"] = {
                "total_count": len(instances_data),
                "list": instances_data,
                "legacy_instances": {
                    "count": len(legacy_instances),
                    "list": legacy_instances
                },
                "current_instances": {
                    "count": len(current_instances),
                    "list": current_instances
                },
                "has_legacy": len(legacy_instances) > 0
            }
        except Exception as e:
            coverage_data["dimensions_analysis"]["instance_types"] = {"error": str(e)}
        
        # Análise de contas vinculadas
        try:
            accounts_response = cost_explorer.get_dimension_values(dimension='LINKED_ACCOUNT')
            accounts_data = [item['Value'] for item in accounts_response['DimensionValues']]
            coverage_data["dimensions_analysis"]["linked_accounts"] = {
                "total_count": len(accounts_data),
                "list": accounts_data,
                "is_organization": len(accounts_data) > 1
            }
        except Exception as e:
            coverage_data["dimensions_analysis"]["linked_accounts"] = {"error": str(e)}
        
        # Análise de engines de banco
        try:
            db_response = cost_explorer.get_dimension_values(dimension='DATABASE_ENGINE')
            db_data = [item['Value'] for item in db_response['DimensionValues']]
            coverage_data["dimensions_analysis"]["database_engines"] = {
                "total_count": len(db_data),
                "list": db_data,
                "has_databases": len(db_data) > 0
            }
        except Exception as e:
            coverage_data["dimensions_analysis"]["database_engines"] = {"error": str(e)}
        
        return json.dumps(coverage_data, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Erro na análise de cobertura: {str(e)}"}, ensure_ascii=False)

@tool
def get_account_context_data() -> str:
    """
    Coleta dados contextuais abrangentes da conta AWS para análise.
    
    Returns:
        JSON com contexto completo da conta para geração de insights
    """
    print("CHAMANDO GET_ACCOUNT_CONTEXT_DATA")
    try:
        cost_explorer = CostExplorer()
        analyzer = CostAnalyzer(cost_explorer)
        
        context_data = {
            "collection_timestamp": datetime.now().isoformat(),
            "cost_trends": {},
            "top_services": {},
            "dimension_summary": {},
            "usage_patterns": {}
        }
        
        # Tendências de custo
        try:
            trends = analyzer.get_cost_trends(months=6)
            context_data["cost_trends"] = trends
        except Exception as e:
            context_data["cost_trends"] = {"error": str(e)}
        
        # Top serviços
        try:
            top_services = analyzer.get_top_services(limit=10)
            context_data["top_services"] = top_services
        except Exception as e:
            context_data["top_services"] = {"error": str(e)}
        
        # Resumo das principais dimensões
        dimensions_to_check = ['SERVICE', 'REGION', 'INSTANCE_TYPE', 'PURCHASE_TYPE', 'OPERATING_SYSTEM']
        
        for dimension in dimensions_to_check:
            try:
                response = cost_explorer.get_dimension_values(dimension=dimension)
                values = [item['Value'] for item in response['DimensionValues']]
                context_data["dimension_summary"][dimension.lower()] = {
                    "count": len(values),
                    "values": values[:20]  # Limita para evitar payloads muito grandes
                }
            except Exception as e:
                context_data["dimension_summary"][dimension.lower()] = {"error": str(e)}
        
        # Padrões de uso (últimos 30 dias)
        try:
            usage_response = cost_explorer.get_cost_by_service(
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                granularity='DAILY'
            )
            
            # Processa dados de uso
            daily_costs = []
            service_usage = {}
            
            for period in usage_response.get('ResultsByTime', []):
                period_total = 0
                period_date = period.get('TimePeriod', {}).get('Start', '')
                
                for group in period.get('Groups', []):
                    service = group.get('Keys', ['Unknown'])[0]
                    cost = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                    
                    period_total += cost
                    
                    if service not in service_usage:
                        service_usage[service] = []
                    service_usage[service].append({
                        'date': period_date,
                        'cost': cost
                    })
                
                daily_costs.append({
                    'date': period_date,
                    'total_cost': period_total
                })
            
            context_data["usage_patterns"] = {
                "daily_costs": daily_costs[-7:],  # Últimos 7 dias
                "service_trends": {k: v[-7:] for k, v in list(service_usage.items())[:5]}  # Top 5 services, últimos 7 dias
            }
            
        except Exception as e:
            context_data["usage_patterns"] = {"error": str(e)}
        
        return json.dumps(context_data, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Erro na coleta de dados contextuais: {str(e)}"}, ensure_ascii=False)

# Configurar o agente
cost_analyzer = Agent(
    chat_generator=OpenAIChatGenerator(model="gpt-4o-mini"),
    tools=[
        get_top_services, 
        get_service_details, 
        get_current_date, 
        format_currency, 
        get_aws_tags, 
        all_dimensions, 
        get_dimension_values, 
        discover_account_resources, 
        validate_and_analyze_service, 
        analyze_account_coverage, 
        get_account_context_data
    ],
    system_prompt="""
    Você é um analista sênior de custos da AWS com expertise em FinOps e otimização de infraestrutura cloud.
    
    ## OBJETIVO PRINCIPAL
    Fornecer análises profundas e recomendações precisas de otimização de custos AWS baseadas em dados reais da conta do usuário.
    
    ## METODOLOGIA DE ANÁLISE
    
    ### 1. DESCOBERTA INICIAL (sempre que apropriado)
    - Use `discover_account_resources()` para mapear a infraestrutura completa
    - Use `analyze_account_coverage()` para entender padrões de governança e cobertura
    - Use `get_account_context_data()` para dados contextuais e tendências
    
    ### 2. ANÁLISE ESPECÍFICA
    - Use `get_top_services()` para identificar os maiores consumidores de custo
    - Use `validate_and_analyze_service()` para validar e analisar serviços específicos mencionados
    - Use `get_service_details()` para drill-down detalhado em serviços específicos
    - Use `get_dimension_values()` para explorar dimensões específicas (regiões, tipos de instância, etc.)
    
    ### 3. CONTEXTUALIZAÇÃO
    - Use `get_aws_tags()` para entender governança e organização
    - Use `all_dimensions()` quando precisar entender quais dimensões estão disponíveis
    - Use `get_current_date()` e calcule períodos quando necessário
    
    ## ESTRUTURA DAS ANÁLISES
    
    ### Para Análises Gerais:
    1. **Descoberta**: Mapeie recursos e cobertura da conta
    2. **Contexto**: Colete dados históricos e tendências  
    3. **Top Custos**: Identifique principais geradores de custo
    4. **Drill-down**: Analise serviços específicos detalhadamente
    5. **Governança**: Avalie tags, regiões, tipos de compra
    6. **Recomendações**: Baseadas nos dados coletados
    
    ### Para Consultas Específicas:
    1. **Validação**: Confirme se serviço/recurso existe na conta
    2. **Análise Detalhada**: Use ferramentas específicas para o contexto
    3. **Comparação**: Compare com padrões e bests practices
    4. **Recomendações**: Específicas para o contexto analisado
    
    ## DIRETRIZES DE ANÁLISE
    
    ### Sempre Analise:
    - **Dimensões de Custo**: Usage types, regiões, tipos de instância, sistemas operacionais
    - **Padrões Temporais**: Tendências, sazonalidade, picos de uso
    - **Otimizações de Compra**: OnDemand vs Reserved vs Savings Plans
    - **Governança**: Uso de tags, distribuição regional, contas vinculadas
    - **Eficiência**: Instâncias legacy vs current generation
    
    ### Identifique Oportunidades:
    - Instâncias subutilizadas ou oversized
    - Recursos não taggeados (falta de governança)
    - Uso exclusivo de OnDemand (oportunidade para Reserved/Savings Plans)
    - Concentração em regiões caras
    - Uso de gerações antigas de instâncias
    
    ### Forneça Recomendações Específicas:
    - Quantifique economias potenciais quando possível
    - Priorize por impacto financeiro
    - Considere complexidade de implementação
    - Base todas as recomendações nos dados coletados
    
    ## REGRAS OPERACIONAIS
    
    1. **SEMPRE USE DADOS REAIS**: Nunca assuma, sempre colete dados com as ferramentas
    2. **SER PROATIVO**: Para análises gerais, use ferramentas de descoberta automaticamente
    3. **CONTEXTUALIZAR**: Explique termos técnicos e forneça contexto de negócio
    4. **QUANTIFICAR**: Use `format_currency()` para valores em reais
    5. **TEMPORALIZAR**: Use `get_current_date()` para cálculos de período precisos
    6. **ESTRUTURAR**: Organize respostas em seções claras e acionáveis
    
    ## TRATAMENTO DE PERÍODOS
    - Para consultas temporais, use `get_current_date()` e calcule o período inicial
    - Sempre formate valores monetários de USD para BRL usando `format_currency()`
    - Para análises históricas, considere pelo menos 3-6 meses de dados quando disponível
    
    ## ESTILO DE COMUNICAÇÃO
    - **Profissional e técnico**, mas acessível
    - **Baseado em evidências** dos dados coletados
    - **Acionável** com próximos passos claros
    - **Quantificado** com métricas concretas sempre que possível
    
    Não peça confirmação desnecessária. Execute as análises e forneça insights baseados nos dados coletados.
    """,
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
    query = f"Qual o serviço mais caro da minha conta AWS?"
    run_agent_query(query)