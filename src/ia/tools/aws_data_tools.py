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
    """Encoder JSON personalizado para lidar com tipos especiais como Decimal e datetime."""
    def default(self, obj):
        from decimal import Decimal
        from datetime import datetime, date
        
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
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
    print("GET AWS TAGS")
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


@tool
def aws_ec2_call(method: str, instance_ids: Optional[str] = None, volume_ids: Optional[str] = None, 
                 vpc_ids: Optional[str] = None, subnet_ids: Optional[str] = None, 
                 group_ids: Optional[str] = None, region_name: Optional[str] = None) -> str:
    """
    Executa chamadas dinâmicas para a API do Amazon EC2 via boto3.
    
    Args:
        method: Nome do método EC2 a ser executado (ex: 'describe_instances', 'describe_volumes')
        instance_ids: IDs específicos de instâncias (separados por vírgula, ex: 'i-123,i-456')
        volume_ids: IDs específicos de volumes (separados por vírgula, ex: 'vol-123,vol-456') 
        vpc_ids: IDs específicos de VPCs (separados por vírgula)
        subnet_ids: IDs específicos de subnets (separados por vírgula)
        group_ids: IDs específicos de grupos de segurança (separados por vírgula)
        region_name: Nome da região específica (opcional)
        
    Returns:
        JSON com os dados retornados pela API do EC2
        
    Exemplos de uso:
    - aws_ec2_call("describe_instances") - Lista todas as instâncias
    - aws_ec2_call("describe_instances", instance_ids="i-1234567890abcdef0") - Instância específica
    - aws_ec2_call("describe_volumes") - Lista todos os volumes EBS
    - aws_ec2_call("describe_addresses") - Lista todos os Elastic IPs
    
    Métodos principais:
    - describe_instances: Lista instâncias EC2
    - describe_volumes: Lista volumes EBS  
    - describe_addresses: Lista Elastic IPs
    - describe_vpcs: Lista VPCs
    - describe_subnets: Lista subnets
    - describe_security_groups: Lista grupos de segurança
    - describe_snapshots: Lista snapshots
    - describe_nat_gateways: Lista NAT gateways
    - describe_reserved_instances: Lista instâncias reservadas
    """
    # Construir parâmetros dinamicamente
    parameters = {}
    
    # Converter strings separadas por vírgula em listas
    if instance_ids:
        parameters['InstanceIds'] = [id.strip() for id in instance_ids.split(',')]
    if volume_ids:
        parameters['VolumeIds'] = [id.strip() for id in volume_ids.split(',')]
    if vpc_ids:
        parameters['VpcIds'] = [id.strip() for id in vpc_ids.split(',')]
    if subnet_ids:
        parameters['SubnetIds'] = [id.strip() for id in subnet_ids.split(',')]
    if group_ids:
        parameters['GroupIds'] = [id.strip() for id in group_ids.split(',')]
    
    print(f"AWS EC2 CALL - Method: {method}, Parameters: {parameters}")
    
    # Whitelist de métodos permitidos para segurança
    ALLOWED_METHODS = {
        # Instâncias e recursos compute
        'describe_instances',
        'describe_instance_types',
        'describe_instance_attribute',
        'describe_instance_status',
        'describe_reserved_instances',
        'describe_scheduled_instances',
        'describe_spot_instances',
        'describe_spot_price_history',
        'describe_placement_groups',
        
        # Storage
        'describe_volumes',
        'describe_volume_status',
        'describe_volume_attribute',
        'describe_snapshots',
        'describe_snapshot_attribute',
        
        # Images
        'describe_images',
        'describe_image_attribute',
        
        # Networking
        'describe_vpcs',
        'describe_subnets',
        'describe_security_groups',
        'describe_network_interfaces',
        'describe_addresses',
        'describe_internet_gateways',
        'describe_nat_gateways',
        'describe_route_tables',
        'describe_network_acls',
        'describe_vpc_endpoints',
        'describe_customer_gateways',
        'describe_vpn_gateways',
        'describe_vpn_connections',
        
        # Load Balancers (ELBv2)
        'describe_load_balancers',
        'describe_target_groups',
        'describe_listeners',
        
        # Key pairs
        'describe_key_pairs',
        
        # Regions and AZs
        'describe_regions',
        'describe_availability_zones',
        
        # Tags
        'describe_tags',
        
        # Billing e usage
        'describe_account_attributes',
        'describe_instance_credit_specifications'
    }
    
    if method not in ALLOWED_METHODS:
        return json.dumps({
            "error": f"Método '{method}' não permitido",
            "allowed_methods": sorted(list(ALLOWED_METHODS))
        }, ensure_ascii=False, indent=2)
    
    try:
        cost_explorer = CostExplorer()
        
        # Cria cliente EC2 usando a mesma sessão do Cost Explorer
        session = cost_explorer.aws_client.session
        ec2_client = session.client('ec2')
        
        # Remove parâmetros vazios para evitar erros
        clean_parameters = {k: v for k, v in parameters.items() if v is not None and v != []}
        
        print(f"EC2 Call - Executing: {method} with params: {clean_parameters}")
        
        # Executa o método dinamicamente
        ec2_method = getattr(ec2_client, method)
        response = ec2_method(**clean_parameters)
        
        # Debug: verificar se há dados
        print(f"EC2 Call - Raw response keys: {list(response.keys())}")
        if method == 'describe_instances' and 'Reservations' in response:
            print(f"EC2 Call - Found {len(response['Reservations'])} reservations")
            total_instances = sum(len(res.get('Instances', [])) for res in response['Reservations'])
            print(f"EC2 Call - Total instances: {total_instances}")
        elif method == 'describe_volumes' and 'Volumes' in response:
            print(f"EC2 Call - Found {len(response['Volumes'])} volumes")
        elif method == 'describe_addresses' and 'Addresses' in response:
            print(f"EC2 Call - Found {len(response['Addresses'])} addresses")
        
        # Remove ResponseMetadata para limpar o output
        if 'ResponseMetadata' in response:
            del response['ResponseMetadata']
        
        # Verificar se há dados úteis na resposta
        has_data = False
        if method == 'describe_instances' and response.get('Reservations'):
            has_data = any(res.get('Instances', []) for res in response['Reservations'])
        elif method == 'describe_volumes' and response.get('Volumes'):
            has_data = len(response['Volumes']) > 0
        elif method == 'describe_addresses' and response.get('Addresses'):
            has_data = len(response['Addresses']) > 0
        elif method in ['describe_vpcs', 'describe_subnets', 'describe_security_groups'] and response:
            # Para estes métodos, verificar se há dados nas chaves principais
            main_key = {
                'describe_vpcs': 'Vpcs',
                'describe_subnets': 'Subnets', 
                'describe_security_groups': 'SecurityGroups'
            }.get(method)
            has_data = bool(response.get(main_key, []))
        else:
            # Para outros métodos, assumir que há dados se a resposta não está vazia
            has_data = bool(response and len(response) > 0)
        
        if not has_data:
            print(f"EC2 Call - Warning: No data returned for {method}")
            response['_meta'] = {
                'warning': f'Nenhum dado encontrado para {method}',
                'possible_reasons': [
                    'Não há recursos deste tipo na conta',
                    'Recursos podem estar em outras regiões',
                    'Permissões IAM podem estar limitadas',
                    'Recursos podem ter sido filtrados'
                ]
            }
            
        print(f"EC2 Call - Success: {method} (has_data: {has_data})")
        return json.dumps(response, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except AttributeError as e:
        import traceback
        tb = traceback.format_exc()
        print(f"EC2 Call - AttributeError: {e}")
        print(f"EC2 Call - Traceback:\n{tb}")
        return json.dumps({
            "error": f"Método '{method}' não existe no cliente EC2",
            "details": str(e),
            "traceback": tb,
            "line_info": f"Erro na linha: {traceback.extract_tb(e.__traceback__)[-1].lineno}"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = str(e)
        print(f"EC2 Call - Error: {error_msg}")
        print(f"EC2 Call - Traceback:\n{tb}")
        
        # Tratamento de erros específicos com informações detalhadas
        if "InvalidParameterValue" in error_msg:
            return json.dumps({
                "error": "Parâmetros inválidos fornecidos",
                "details": error_msg,
                "suggestion": "Verifique os parâmetros e tente novamente",
                "traceback": tb,
                "line_info": f"Erro na linha: {traceback.extract_tb(e.__traceback__)[-1].lineno}"
            }, ensure_ascii=False, indent=2)
        elif "UnauthorizedOperation" in error_msg:
            return json.dumps({
                "error": "Operação não autorizada",
                "details": error_msg,
                "suggestion": "Verifique as permissões IAM",
                "traceback": tb,
                "line_info": f"Erro na linha: {traceback.extract_tb(e.__traceback__)[-1].lineno}"
            }, ensure_ascii=False, indent=2)
        elif "InvalidInstanceID" in error_msg:
            return json.dumps({
                "error": "ID de instância inválido",
                "details": error_msg,
                "suggestion": "Verifique se o ID da instância existe e está correto",
                "traceback": tb,
                "line_info": f"Erro na linha: {traceback.extract_tb(e.__traceback__)[-1].lineno}"
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "error": f"Erro ao executar {method}",
                "details": error_msg,
                "traceback": tb,
                "line_info": f"Erro na linha: {traceback.extract_tb(e.__traceback__)[-1].lineno}",
                "method": method,
                "parameters": parameters
            }, ensure_ascii=False, indent=2)


@tool
def get_instance_cost_by_name(instance_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Busca o custo de uma instância EC2 específica pelo nome, usando correlação com tags.
    
    Args:
        instance_name: Nome da instância (valor da tag 'Name')
        start_date: Data inicial no formato YYYY-MM-DD (opcional)
        end_date: Data final no formato YYYY-MM-DD (opcional)
        
    Returns:
        JSON com detalhes da instância e estimativa de custo baseada em tags
        
    Exemplos:
    - get_instance_cost_by_name("Valhalla")
    - get_instance_cost_by_name("WebServer-Prod")
    """
    print(f"BUSCANDO CUSTO DA INSTÂNCIA: {instance_name}")
    
    try:
        # 1. Buscar a instância pelo nome
        cost_explorer = CostExplorer()
        session = cost_explorer.aws_client.session
        ec2_client = session.client('ec2')
        
        # Buscar instâncias com filtro por tag Name
        print(f"Buscando instância com nome: {instance_name}")
        instances_response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [instance_name]
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['running', 'stopped']  # Excluir instâncias terminadas
                }
            ]
        )
        
        # Processar resultados
        found_instances = []
        for reservation in instances_response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                found_instances.append(instance)
        
        if not found_instances:
            return json.dumps({
                "error": f"Instância com nome '{instance_name}' não encontrada",
                "suggestion": "Verifique se o nome está correto e se a instância existe",
                "searched_name": instance_name
            }, ensure_ascii=False, indent=2)
        
        # Se encontrou múltiplas instâncias com o mesmo nome
        if len(found_instances) > 1:
            instances_info = []
            for instance in found_instances:
                instances_info.append({
                    "instance_id": instance.get('InstanceId'),
                    "state": instance.get('State', {}).get('Name'),
                    "instance_type": instance.get('InstanceType'),
                    "availability_zone": instance.get('Placement', {}).get('AvailabilityZone')
                })
            
            return json.dumps({
                "warning": f"Encontradas {len(found_instances)} instâncias com nome '{instance_name}'",
                "instances": instances_info,
                "suggestion": "Use o Instance ID específico para análise mais precisa"
            }, ensure_ascii=False, indent=2)
        
        # Processar a instância encontrada
        instance = found_instances[0]
        instance_id = instance.get('InstanceId')
        instance_type = instance.get('InstanceType')
        state = instance.get('State', {}).get('Name')
        availability_zone = instance.get('Placement', {}).get('AvailabilityZone')
        
        # 2. Extrair tags da instância
        instance_tags = {}
        cost_relevant_tags = []
        
        for tag in instance.get('Tags', []):
            key = tag.get('Key')
            value = tag.get('Value')
            instance_tags[key] = value
            
            # Tags relevantes para análise de custo (excluir tags da AWS)
            if not key.startswith('aws:'):
                cost_relevant_tags.append({"key": key, "value": value})
        
        print(f"Instância encontrada: {instance_id} ({instance_type}) - Tags: {len(cost_relevant_tags)}")
        
        # 3. Buscar custos por tags relevantes
        cost_analysis = {
            "total_estimated_cost_usd": 0,
            "total_estimated_cost_brl": 0,
            "tag_based_costs": [],
            "estimation_method": "tag_correlation"
        }
        
        # Definir período de análise
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Buscar custos por cada tag relevante
        for tag_info in cost_relevant_tags:
            tag_key = tag_info["key"]
            tag_value = tag_info["value"]
            
            try:
                # Buscar custos por esta tag específica
                tag_cost_response = cost_explorer.get_cost_by_tag(tag_key, start_date, end_date)
                
                tag_total_cost = 0
                matching_cost = 0
                
                for period in tag_cost_response.get('ResultsByTime', []):
                    for group in period.get('Groups', []):
                        group_tag_value = group.get('Keys', [''])[0]
                        cost_usd = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                        
                        # Limpar valor da tag (remover prefixos se houver)
                        if '$' in group_tag_value:
                            group_tag_value = group_tag_value.split('$')[-1]
                        group_tag_value = group_tag_value.rstrip('$')
                        
                        tag_total_cost += cost_usd
                        
                        # Se o valor da tag corresponde exatamente
                        if group_tag_value == tag_value:
                            matching_cost += cost_usd
                
                if matching_cost > 0:
                    cost_analysis["tag_based_costs"].append({
                        "tag_key": tag_key,
                        "tag_value": tag_value,
                        "cost_usd": matching_cost,
                        "cost_brl": matching_cost * cost_explorer.get_exchange_rate() if hasattr(cost_explorer, 'get_exchange_rate') else matching_cost * 5.5,
                        "period_days": (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
                    })
                    
                    print(f"Tag {tag_key}={tag_value}: ${matching_cost:.2f}")
                
            except Exception as e:
                print(f"Erro ao buscar custo para tag {tag_key}: {e}")
                continue
        
        # 4. Calcular estimativa de custo total
        if cost_analysis["tag_based_costs"]:
            # Se temos custos por tags, usar o maior valor (mais específico)
            max_cost_entry = max(cost_analysis["tag_based_costs"], key=lambda x: x["cost_usd"])
            cost_analysis["total_estimated_cost_usd"] = max_cost_entry["cost_usd"]
            cost_analysis["total_estimated_cost_brl"] = max_cost_entry["cost_brl"]
            cost_analysis["primary_cost_tag"] = f"{max_cost_entry['tag_key']}={max_cost_entry['tag_value']}"
        else:
            # Fallback: estimar com base no tipo de instância
            try:
                service_details = cost_explorer.get_service_details('Amazon Elastic Compute Cloud - Compute', start_date, end_date)
                
                for period in service_details.get('ResultsByTime', []):
                    for group in period.get('Groups', []):
                        usage_type = group.get('Keys', [''])[0]
                        if instance_type in usage_type or availability_zone.replace('-', '') in usage_type:
                            cost_usd = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                            if cost_usd > 0:
                                cost_analysis["total_estimated_cost_usd"] = cost_usd
                                cost_analysis["total_estimated_cost_brl"] = cost_usd * 5.5
                                cost_analysis["estimation_method"] = "instance_type_correlation"
                                break
                
            except Exception as e:
                print(f"Erro na estimativa por tipo de instância: {e}")
        
        # 5. Montar resposta final
        result = {
            "instance_name": instance_name,
            "instance_details": {
                "instance_id": instance_id,
                "instance_type": instance_type,
                "state": state,
                "availability_zone": availability_zone,
                "tags": instance_tags
            },
            "cost_analysis": cost_analysis,
            "analysis_period": {
                "start_date": start_date,
                "end_date": end_date,
                "days": (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
            },
            "recommendations": []
        }
        
        # 6. Adicionar recomendações
        if cost_analysis["total_estimated_cost_usd"] == 0:
            result["recommendations"].append("Não foi possível estimar o custo através das tags. Considere implementar tags mais específicas para esta instância.")
        
        if state == 'stopped':
            result["recommendations"].append("Esta instância está parada, mas ainda pode ter custos de armazenamento EBS.")
        
        if not cost_relevant_tags:
            result["recommendations"].append("Esta instância não possui tags de governança. Adicione tags como Environment, Project, Owner para melhor rastreamento de custos.")
        
        print(f"Análise concluída para {instance_name}: ${cost_analysis['total_estimated_cost_usd']:.2f}")
        
        return json.dumps(result, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erro na análise de custo da instância: {e}")
        print(f"Traceback:\n{tb}")
        
        return json.dumps({
            "error": f"Erro ao analisar custo da instância '{instance_name}'",
            "details": str(e),
            "traceback": tb,
            "suggestion": "Verifique se a instância existe e se você tem permissões adequadas"
        }, ensure_ascii=False, indent=2)


@tool
def find_instances_by_tag(tag_key: str, tag_value: str = None) -> str:
    """
    Busca instâncias EC2 por uma tag específica ou lista todas as instâncias com uma determinada tag.
    
    Args:
        tag_key: Chave da tag (ex: 'Name', 'Environment', 'Project')
        tag_value: Valor da tag (opcional). Se não fornecido, lista todos os valores para essa tag
        
    Returns:
        JSON com instâncias encontradas e suas informações básicas
        
    Exemplos:
    - find_instances_by_tag("Name", "Valhalla")
    - find_instances_by_tag("Environment", "production")
    - find_instances_by_tag("Project")  # Lista todas as instâncias com tag Project
    """
    print(f"BUSCANDO INSTÂNCIAS POR TAG: {tag_key}={tag_value or '*'}")
    
    try:
        cost_explorer = CostExplorer()
        session = cost_explorer.aws_client.session
        ec2_client = session.client('ec2')
        
        # Preparar filtros
        filters = [
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'stopped', 'stopping', 'starting']  # Excluir apenas terminated
            }
        ]
        
        # Adicionar filtro por tag
        if tag_value:
            filters.append({
                'Name': f'tag:{tag_key}',
                'Values': [tag_value]
            })
        else:
            # Buscar todas as instâncias que têm essa tag (independente do valor)
            filters.append({
                'Name': f'tag-key',
                'Values': [tag_key]
            })
        
        print(f"Aplicando filtros: {filters}")
        instances_response = ec2_client.describe_instances(Filters=filters)
        
        # Processar resultados
        instances_info = []
        tag_values_found = set()
        
        for reservation in instances_response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                # Extrair informações básicas
                instance_id = instance.get('InstanceId')
                instance_type = instance.get('InstanceType')
                state = instance.get('State', {}).get('Name')
                availability_zone = instance.get('Placement', {}).get('AvailabilityZone')
                launch_time = instance.get('LaunchTime')
                
                # Processar tags
                instance_tags = {}
                target_tag_value = None
                
                for tag in instance.get('Tags', []):
                    key = tag.get('Key')
                    value = tag.get('Value')
                    instance_tags[key] = value
                    
                    if key == tag_key:
                        target_tag_value = value
                        tag_values_found.add(value)
                
                # Informações da instância
                instance_info = {
                    "instance_id": instance_id,
                    "instance_type": instance_type,
                    "state": state,
                    "availability_zone": availability_zone,
                    "launch_time": launch_time.isoformat() if launch_time else None,
                    "target_tag_value": target_tag_value,
                    "all_tags": instance_tags
                }
                
                instances_info.append(instance_info)
        
        # Montar resposta
        result = {
            "search_criteria": {
                "tag_key": tag_key,
                "tag_value": tag_value,
                "search_type": "specific_value" if tag_value else "all_values"
            },
            "results_summary": {
                "total_instances_found": len(instances_info),
                "unique_tag_values": list(tag_values_found) if not tag_value else None
            },
            "instances": instances_info
        }
        
        # Adicionar insights
        if not instances_info:
            result["message"] = f"Nenhuma instância encontrada com a tag '{tag_key}'" + (f"='{tag_value}'" if tag_value else "")
            result["suggestions"] = [
                f"Verifique se a tag '{tag_key}' existe nas suas instâncias",
                "Use find_instances_by_tag(tag_key) para ver todos os valores disponíveis para esta tag"
            ]
        elif not tag_value and len(tag_values_found) > 1:
            result["insights"] = [
                f"Encontrados {len(tag_values_found)} valores diferentes para a tag '{tag_key}'",
                "Use um valor específico para análise mais precisa de custos"
            ]
        
        print(f"Busca concluída: {len(instances_info)} instâncias encontradas")
        
        return json.dumps(result, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erro na busca de instâncias por tag: {e}")
        print(f"Traceback:\n{tb}")
        
        return json.dumps({
            "error": f"Erro ao buscar instâncias pela tag '{tag_key}'",
            "details": str(e),
            "traceback": tb,
            "suggestion": "Verifique se você tem permissões para listar instâncias EC2"
        }, ensure_ascii=False, indent=2)


@tool
def audit_governance_tags() -> str:
    """
    Auditoria otimizada de recursos sem tags de governança adequadas.
    Retorna resumo eficiente focando apenas em recursos sem tags críticas.
    
    Returns:
        JSON compacto com auditoria de governança por tipo de recurso
        
    Exemplo de uso:
    - audit_governance_tags() - Mostra recursos sem tags de governança
    """
    print("INICIANDO AUDITORIA DE GOVERNANÇA OTIMIZADA")
    
    try:
        cost_explorer = CostExplorer()
        session = cost_explorer.aws_client.session
        ec2_client = session.client('ec2')
        
        # Tags críticas de governança
        governance_tags = ['Environment', 'Project', 'Owner', 'Team', 'CostCenter', 'Application']
        
        audit_result = {
            "audit_timestamp": datetime.now().isoformat(),
            "governance_tags_checked": governance_tags,
            "summary": {
                "total_resources_audited": 0,
                "resources_without_governance": 0,
                "compliance_percentage": 0
            },
            "resources_audit": {}
        }
        
        # 1. Auditoria de Instâncias EC2 (resumida)
        print("Auditando instâncias EC2...")
        try:
            instances_response = ec2_client.describe_instances(
                Filters=[
                    {
                        'Name': 'instance-state-name',
                        'Values': ['running', 'stopped']
                    }
                ]
            )
            
            instances_without_governance = []
            total_instances = 0
            
            for reservation in instances_response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    total_instances += 1
                    instance_id = instance.get('InstanceId')
                    instance_type = instance.get('InstanceType')
                    state = instance.get('State', {}).get('Name')
                    
                    # Verificar tags de governança
                    instance_tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    # Verificar se tem pelo menos uma tag de governança
                    has_governance_tag = any(tag in instance_tags for tag in governance_tags)
                    
                    if not has_governance_tag:
                        instances_without_governance.append({
                            "resource_id": instance_id,
                            "type": instance_type,
                            "state": state,
                            "existing_tags": list(instance_tags.keys())[:3],  # Máximo 3 tags para economizar tokens
                            "missing_governance_tags": governance_tags
                        })
            
            audit_result["resources_audit"]["ec2_instances"] = {
                "total_count": total_instances,
                "without_governance_count": len(instances_without_governance),
                "compliance_rate": f"{((total_instances - len(instances_without_governance)) / total_instances * 100):.1f}%" if total_instances > 0 else "0%",
                "non_compliant_resources": instances_without_governance[:10]  # Limitar a 10 recursos
            }
            
            audit_result["summary"]["total_resources_audited"] += total_instances
            audit_result["summary"]["resources_without_governance"] += len(instances_without_governance)
            
        except Exception as e:
            print(f"Erro na auditoria de instâncias: {e}")
            audit_result["resources_audit"]["ec2_instances"] = {"error": str(e)}
        
        # 2. Auditoria de Volumes EBS (resumida)
        print("Auditando volumes EBS...")
        try:
            volumes_response = ec2_client.describe_volumes()
            
            volumes_without_governance = []
            total_volumes = len(volumes_response.get('Volumes', []))
            
            for volume in volumes_response.get('Volumes', []):
                volume_id = volume.get('VolumeId')
                volume_size = volume.get('Size')
                volume_state = volume.get('State')
                
                # Verificar tags de governança
                volume_tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                has_governance_tag = any(tag in volume_tags for tag in governance_tags)
                
                if not has_governance_tag:
                    volumes_without_governance.append({
                        "resource_id": volume_id,
                        "size_gb": volume_size,
                        "state": volume_state,
                        "existing_tags": list(volume_tags.keys())[:2],  # Máximo 2 tags
                        "is_attached": len(volume.get('Attachments', [])) > 0
                    })
            
            audit_result["resources_audit"]["ebs_volumes"] = {
                "total_count": total_volumes,
                "without_governance_count": len(volumes_without_governance),
                "compliance_rate": f"{((total_volumes - len(volumes_without_governance)) / total_volumes * 100):.1f}%" if total_volumes > 0 else "0%",
                "non_compliant_resources": volumes_without_governance[:5]  # Limitar a 5 volumes
            }
            
            audit_result["summary"]["total_resources_audited"] += total_volumes
            audit_result["summary"]["resources_without_governance"] += len(volumes_without_governance)
            
        except Exception as e:
            print(f"Erro na auditoria de volumes: {e}")
            audit_result["resources_audit"]["ebs_volumes"] = {"error": str(e)}
        
        # 3. Auditoria de Elastic IPs (resumida)
        print("Auditando Elastic IPs...")
        try:
            addresses_response = ec2_client.describe_addresses()
            
            addresses_without_governance = []
            total_addresses = len(addresses_response.get('Addresses', []))
            
            for address in addresses_response.get('Addresses', []):
                allocation_id = address.get('AllocationId')
                public_ip = address.get('PublicIp')
                is_associated = 'AssociationId' in address
                
                # Verificar tags de governança
                address_tags = {tag['Key']: tag['Value'] for tag in address.get('Tags', [])}
                has_governance_tag = any(tag in address_tags for tag in governance_tags)
                
                if not has_governance_tag:
                    addresses_without_governance.append({
                        "resource_id": allocation_id or public_ip,
                        "public_ip": public_ip,
                        "is_associated": is_associated,
                        "existing_tags": list(address_tags.keys())[:2]
                    })
            
            audit_result["resources_audit"]["elastic_ips"] = {
                "total_count": total_addresses,
                "without_governance_count": len(addresses_without_governance),
                "compliance_rate": f"{((total_addresses - len(addresses_without_governance)) / total_addresses * 100):.1f}%" if total_addresses > 0 else "0%",
                "non_compliant_resources": addresses_without_governance[:5]  # Limitar a 5 IPs
            }
            
            audit_result["summary"]["total_resources_audited"] += total_addresses
            audit_result["summary"]["resources_without_governance"] += len(addresses_without_governance)
            
        except Exception as e:
            print(f"Erro na auditoria de Elastic IPs: {e}")
            audit_result["resources_audit"]["elastic_ips"] = {"error": str(e)}
        
        # Calcular compliance geral
        if audit_result["summary"]["total_resources_audited"] > 0:
            compliance_rate = ((audit_result["summary"]["total_resources_audited"] - audit_result["summary"]["resources_without_governance"]) / 
                             audit_result["summary"]["total_resources_audited"]) * 100
            audit_result["summary"]["compliance_percentage"] = f"{compliance_rate:.1f}%"
        
        # Adicionar recomendações
        audit_result["recommendations"] = []
        
        if audit_result["summary"]["resources_without_governance"] > 0:
            audit_result["recommendations"].extend([
                f"Implementar tags de governança em {audit_result['summary']['resources_without_governance']} recursos",
                "Criar política de tagging obrigatória",
                "Configurar AWS Config para compliance automático",
                "Treinar equipes sobre importância de tags para cost allocation"
            ])
        else:
            audit_result["recommendations"].append("Excelente! Todos os recursos auditados possuem tags de governança.")
        
        # Priorização por impacto
        audit_result["priority_actions"] = []
        
        ec2_non_compliant = audit_result["resources_audit"].get("ec2_instances", {}).get("without_governance_count", 0)
        if ec2_non_compliant > 0:
            audit_result["priority_actions"].append(f"ALTA: {ec2_non_compliant} instâncias EC2 sem tags (maior impacto de custo)")
        
        ebs_non_compliant = audit_result["resources_audit"].get("ebs_volumes", {}).get("without_governance_count", 0)
        if ebs_non_compliant > 0:
            audit_result["priority_actions"].append(f"MÉDIA: {ebs_non_compliant} volumes EBS sem tags")
        
        eip_non_compliant = audit_result["resources_audit"].get("elastic_ips", {}).get("without_governance_count", 0)
        if eip_non_compliant > 0:
            audit_result["priority_actions"].append(f"BAIXA: {eip_non_compliant} Elastic IPs sem tags")
        
        print(f"Auditoria concluída: {audit_result['summary']['compliance_percentage']} compliance")
        
        return json.dumps(audit_result, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erro na auditoria de governança: {e}")
        print(f"Traceback:\n{tb}")
        
        return json.dumps({
            "error": f"Erro na auditoria de governança",
            "details": str(e),
            "traceback": tb,
            "suggestion": "Verifique permissões e conectividade AWS"
        }, ensure_ascii=False, indent=2)


 