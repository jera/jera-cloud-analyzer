"""
Ferramentas para coleta e análise de dados AWS.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from haystack.tools import tool
from src.clouds.aws.cost_explorer import CostExplorer
from src.clouds.aws.cost_analyzer import CostAnalyzer


class JsonEncoder(json.JSONEncoder):
    """Encoder JSON personalizado para lidar com tipos especiais como Decimal."""
    def default(self, obj):
        from decimal import Decimal
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


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
        print(f"GET TOP SERVICES - Input dates - Start: {start_date}, End: {end_date}")
        
        # Definir datas padrão se não fornecidas
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"GET TOP SERVICES - Calculated dates - Start: {start_date}, End: {end_date}")
        
        cost_explorer = CostExplorer()
        analyzer = CostAnalyzer(cost_explorer)
        top_services = analyzer.get_top_services(limit=limit, start_date=start_date, end_date=end_date)
        
        result = json.dumps(top_services, cls=JsonEncoder, ensure_ascii=False, indent=2)
        print(f"GET TOP SERVICES - Found {len(top_services)} services")
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
    print(f"GET SERVICE DETAILS - Service: {service_name}, Start: {start_date}, End: {end_date}")
    
    try:
        cost_explorer = CostExplorer()
        
        # Se não forneceu datas, tenta períodos progressivamente maiores
        if not start_date or not end_date:
            # Define data final como hoje
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Tenta diferentes períodos: 30, 90, 180, 365 dias
            periods_to_try = [30, 90, 180, 365]
            
            for days in periods_to_try:
                test_start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                print(f"GET SERVICE DETAILS - Trying period: {test_start_date} to {end_date} ({days} days)")
                
                try:
                    service_details = cost_explorer.get_service_details(service_name, test_start_date, end_date)
                    
                    # Verifica se há dados (não vazios)
                    has_data = False
                    for period in service_details.get('ResultsByTime', []):
                        total_cost = float(period.get('Total', {}).get('UnblendedCost', {}).get('Amount', '0'))
                        groups = period.get('Groups', [])
                        if total_cost > 0 or len(groups) > 0:
                            has_data = True
                            break
                    
                    if has_data:
                        print(f"GET SERVICE DETAILS - Found data with {days} days period")
                        result = json.dumps(service_details, cls=JsonEncoder, ensure_ascii=False, indent=2)
                        return result
                    else:
                        print(f"GET SERVICE DETAILS - No data found for {days} days, trying longer period...")
                        
                except Exception as e:
                    print(f"GET SERVICE DETAILS - Error with {days} days period: {e}")
                    continue
            
            # Se chegou aqui, não encontrou dados em nenhum período
            return json.dumps({
                "message": f"Nenhum dado encontrado para {service_name} nos últimos 365 dias",
                "service_name": service_name,
                "periods_checked": periods_to_try,
                "suggestion": "Verifique se o serviço está sendo usado ou se há dados históricos disponíveis"
            }, ensure_ascii=False, indent=2)
        
        else:
            # Se as datas foram fornecidas, usa elas diretamente
            print(f"GET SERVICE DETAILS - Using provided dates - Start: {start_date}, End: {end_date}")
            service_details = cost_explorer.get_service_details(service_name, start_date, end_date)
            result = json.dumps(service_details, cls=JsonEncoder, ensure_ascii=False, indent=2)
            return result
        
    except Exception as e:
        print(f"GET SERVICE DETAILS ERROR: {e}")
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


@tool
def check_account_data_availability() -> str:
    """
    Verifica se existem dados de custos disponíveis na conta AWS e em que períodos.
    
    Returns:
        JSON com informações sobre disponibilidade de dados históricos
    """
    print("CHAMANDO CHECK_ACCOUNT_DATA_AVAILABILITY")
    try:
        cost_explorer = CostExplorer()
        
        # Períodos para verificar (em dias atrás)
        periods_to_check = [7, 30, 90, 180, 365]
        data_availability = {
            "check_timestamp": datetime.now().isoformat(),
            "periods_checked": [],
            "has_any_data": False,
            "recommended_period": None,
            "suggestions": []
        }
        
        for days in periods_to_check:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            try:
                # Tenta buscar dados gerais de custo
                response = cost_explorer.client.get_cost_and_usage(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost']
                )
                
                total_cost = 0
                for period in response.get('ResultsByTime', []):
                    cost = float(period.get('Total', {}).get('UnblendedCost', {}).get('Amount', '0'))
                    total_cost += cost
                
                period_info = {
                    "days": days,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_cost": total_cost,
                    "has_data": total_cost > 0
                }
                
                data_availability["periods_checked"].append(period_info)
                
                if total_cost > 0 and not data_availability["has_any_data"]:
                    data_availability["has_any_data"] = True
                    data_availability["recommended_period"] = days
                
            except Exception as e:
                period_info = {
                    "days": days,
                    "start_date": start_date,
                    "end_date": end_date,
                    "error": str(e)
                }
                data_availability["periods_checked"].append(period_info)
        
        # Gerar sugestões baseadas nos resultados
        if not data_availability["has_any_data"]:
            data_availability["suggestions"] = [
                "Esta conta AWS pode ser nova ou não ter custos registrados ainda",
                "Verifique se há recursos ativos usando discovery tools",
                "Configure billing alerts para monitorar custos futuros",
                "Considere implementar tagging para melhor organização"
            ]
        else:
            data_availability["suggestions"] = [
                f"Use período de {data_availability['recommended_period']} dias para análises",
                "Configure tags para melhor categorização de custos",
                "Implemente políticas de cost optimization"
            ]
        
        return json.dumps(data_availability, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Erro na verificação de dados: {str(e)}"}, ensure_ascii=False) 