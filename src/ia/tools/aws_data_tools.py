"""
Ferramentas para coleta e análise de dados AWS.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from haystack.tools import tool
from src.clouds.aws.cost_explorer import CostExplorer
from src.clouds.aws.cost_analyzer import CostAnalyzer
from src.ia.tools.utility_tools import validate_and_adjust_date_range
from src.ia.tools.service_resolver import service_resolver


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
    Obtém os top serviços mais caros da AWS.
    
    Args:
        start_date: Data de início (YYYY-MM-DD) - opcional, padrão últimos 30 dias
        end_date: Data de fim (YYYY-MM-DD) - opcional, padrão hoje
        limit: Número de serviços a retornar (padrão 5)
        
    Returns:
        JSON com lista dos serviços mais caros
    """
    print("GET TOP SERVICES", start_date, end_date, limit)
    
    try:
        cost_explorer = CostExplorer()
        
        # Se não especificou datas, usar último mês
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Validar e ajustar as datas antes de usar
        validated_start, validated_end = validate_and_adjust_date_range(start_date, end_date)
        
        print(f"GET TOP SERVICES - Using validated period: {validated_start} to {validated_end}")
        
        top_services = cost_explorer.get_top_services(
            start_date=validated_start, 
            end_date=validated_end, 
            limit=limit
        )
        
        # Se não houver dados, tentar período menor
        if not top_services or len(top_services) == 0:
            # Tentar últimos 7 dias
            fallback_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            fallback_end = datetime.now().strftime('%Y-%m-%d')
            
            print(f"GET TOP SERVICES - No data found, trying fallback period: {fallback_start} to {fallback_end}")
            
            top_services = cost_explorer.get_top_services(
                start_date=fallback_start,
                end_date=fallback_end,
                limit=limit
            )
        
        result = json.dumps(top_services, cls=JsonEncoder, ensure_ascii=False, indent=2)
        return result
        
    except Exception as e:
        print(f"GET TOP SERVICES ERROR: {e}")
        
        # Se for erro de limitação histórica, fornecer orientação específica
        if "historical data beyond 14 months" in str(e):
            return json.dumps({
                "error": "Limitação de dados históricos do AWS Cost Explorer",
                "message": "A AWS Cost Explorer só permite acesso a dados dos últimos 14 meses",
                "solution": "Ajustando automaticamente para período válido",
                "current_date": datetime.now().strftime('%Y-%m-%d'),
                "using_period": "últimos 30 dias"
            }, ensure_ascii=False, indent=2)
        
        return f"Erro ao obter top serviços: {str(e)}"


@tool
def get_service_details(service_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Obtém detalhes de custos de um serviço específico com resolução automática do nome.
    
    Args:
        service_name: Nome do serviço AWS (aceita apelidos como 'rds', 'ec2', etc.)
        start_date: Data de início (YYYY-MM-DD) - opcional
        end_date: Data de fim (YYYY-MM-DD) - opcional
        
    Returns:
        Detalhes de custo do serviço especificado
    """
    print(f"GET SERVICE DETAILS - Service: {service_name}, Start: {start_date}, End: {end_date}")
    
    try:
        # 🔧 NOVA FUNCIONALIDADE: Resolução automática do nome do serviço
        resolved_name, confidence, suggestions = service_resolver.resolve_service_name(service_name)
        
        if confidence >= 0.8:
            actual_service_name = resolved_name
            print(f"✅ Serviço resolvido: '{service_name}' → '{actual_service_name}' (confiança: {confidence:.2f})")
        elif confidence > 0.0:
            actual_service_name = resolved_name
            print(f"🤔 Serviço resolvido com baixa confiança: '{service_name}' → '{actual_service_name}' (confiança: {confidence:.2f})")
            if suggestions:
                print(f"💡 Outras sugestões: {', '.join(suggestions[:3])}")
        else:
            actual_service_name = service_name
            print(f"⚠️  Não foi possível resolver '{service_name}', usando nome original")
            if suggestions:
                print(f"💡 Serviços similares encontrados: {', '.join(suggestions[:3])}")
        
        cost_explorer = CostExplorer()
        
        # Se as datas foram fornecidas, validar antes de usar
        validated_start, validated_end = validate_and_adjust_date_range(start_date, end_date)
        
        print(f"GET SERVICE DETAILS - Using validated dates - Start: {validated_start}, End: {validated_end}")
        service_details = cost_explorer.get_service_details(actual_service_name, validated_start, validated_end)
        print(service_details)
        # Adicionar informações de resolução
        service_details['_service_resolution'] = {
            'original_input': service_name,
            'resolved_name': actual_service_name,
            'confidence': confidence,
            'resolution_applied': actual_service_name != service_name,
            'alternative_suggestions': suggestions[:3] if suggestions else []
        }
        
        result = json.dumps(service_details, cls=JsonEncoder, ensure_ascii=False, indent=2)
        return result
        
    except Exception as e:
        print(f"GET SERVICE DETAILS ERROR: {e}")
        # Se for erro de limitação histórica, fornecer orientação específica
        if "historical data beyond 14 months" in str(e):
            return json.dumps({
                "error": "Limitação de dados históricos do AWS Cost Explorer",
                "message": "A AWS Cost Explorer só permite acesso a dados dos últimos 14 meses",
                "solution": "Use datas mais recentes (últimos 13 meses) para análise",
                "current_date": datetime.now().strftime('%Y-%m-%d'),
                "suggested_start_date": (datetime.now() - timedelta(days=390)).strftime('%Y-%m-%d'),
                "service_attempted": service_name
            }, ensure_ascii=False, indent=2)
        
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
def discover_account_resources(limit: int = 5) -> str:
    """
    Descobre todos os recursos ativos na conta AWS com limitação configurável.
    
    Args:
        limit: Número máximo de recursos a retornar por categoria (padrão: 5)
    
    Returns:
        JSON com dados sobre serviços, regiões, tipos de instância e contas descobertos (limitados)
    """
    print(f"CHAMANDO DISCOVER_ACCOUNT_RESOURCES - Limite: {limit}")
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
            "limit_applied": limit,
            "services": {
                "total_count": len(active_services),
                "list": active_services[:limit],
                "truncated": len(active_services) > limit
            },
            "regions": {
                "total_count": len(active_regions),
                "list": active_regions[:limit],
                "truncated": len(active_regions) > limit
            },
            "instance_types": {
                "total_count": len(instance_types),
                "list": instance_types[:limit],
                "truncated": len(instance_types) > limit
            },
            "linked_accounts": {
                "total_count": len(linked_accounts),
                "list": linked_accounts[:limit],
                "is_multi_account": len(linked_accounts) > 1,
                "truncated": len(linked_accounts) > limit
            },
            "purchase_types": {
                "total_count": len(purchase_types),
                "list": purchase_types[:limit],
                "truncated": len(purchase_types) > limit
            },
            "operating_systems": {
                "total_count": len(operating_systems),
                "list": operating_systems[:limit],
                "truncated": len(operating_systems) > limit
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
                 group_ids: Optional[str] = None, region_name: Optional[str] = None, limit: int = 5) -> str:
    """
    Executa chamadas dinâmicas para EC2 e outros serviços AWS baseado no método solicitado.
    
    Args:
        method: Método da API AWS a ser executado
        instance_ids: IDs de instâncias EC2 (separados por vírgula, opcional)
        volume_ids: IDs de volumes EBS (separados por vírgula, opcional)
        vpc_ids: IDs de VPCs (separados por vírgula, opcional)
        subnet_ids: IDs de subnets (separados por vírgula, opcional)
        group_ids: IDs de security groups (separados por vírgula, opcional)
        region_name: Região AWS específica (opcional)
        limit: Número máximo de recursos a retornar (padrão: 5)
        
    Returns:
        JSON com a resposta da API AWS correspondente ao método solicitado (limitado)
        
    Exemplos:
    - aws_ec2_call("describe_instances", limit=10)
    - aws_ec2_call("describe_volumes", volume_ids="vol-123,vol-456")
    - aws_ec2_call("describe_load_balancers", limit=3)  # Será redirecionado para ELBv2
    """
    print(f"AWS EC2 CALL - Método: {method}, Limite: {limit}")
    
    # Preparar parâmetros dinâmicos baseados no método
    parameters = {}
    
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
    
    # Métodos permitidos para EC2
    EC2_METHODS = {
        # Instâncias 
        'describe_instances',
        'describe_instance_status',
        'describe_instance_types',
        
        # Volumes e storage
        'describe_volumes',
        'describe_snapshots',
        'describe_images',
        
        # Networking
        'describe_vpcs',
        'describe_subnets',
        'describe_security_groups',
        'describe_network_interfaces',
        'describe_route_tables',
        'describe_internet_gateways',
        'describe_nat_gateways',
        'describe_vpc_peering_connections',
        'describe_addresses',
        'describe_network_acls',
        'describe_vpc_endpoints',
        'describe_customer_gateways',
        'describe_vpn_gateways',
        'describe_vpn_connections',
        
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
    
    # Métodos permitidos para ELBv2 (Load Balancers)
    ELB_METHODS = {
        'describe_load_balancers',
        'describe_target_groups',
        'describe_listeners',
        'describe_target_health'
    }
    
    # Determinar qual cliente usar
    if method in EC2_METHODS:
        client_type = 'ec2'
        allowed_methods = EC2_METHODS
    elif method in ELB_METHODS:
        client_type = 'elbv2'
        allowed_methods = ELB_METHODS
    else:
        return json.dumps({
            "error": f"Método '{method}' não reconhecido",
            "ec2_methods": sorted(list(EC2_METHODS)),
            "elb_methods": sorted(list(ELB_METHODS))
        }, ensure_ascii=False, indent=2)

    try:
        cost_explorer = CostExplorer()
        
        # Criar o cliente apropriado usando a mesma sessão do Cost Explorer
        session = cost_explorer.aws_client.session
        aws_client = session.client(client_type)
        
        # Remove parâmetros vazios para evitar erros
        clean_parameters = {k: v for k, v in parameters.items() if v is not None and v != []}
        
        print(f"{client_type.upper()} Call - Executing: {method} with params: {clean_parameters}")
        
        # Executa o método dinamicamente
        aws_method = getattr(aws_client, method)
        response = aws_method(**clean_parameters)
        
        # Debug: verificar se há dados
        print(f"{client_type.upper()} Call - Raw response keys: {list(response.keys())}")
        
        # Debug específico para cada tipo de cliente
        if client_type == 'ec2':
            if method == 'describe_instances' and 'Reservations' in response:
                print(f"EC2 Call - Found {len(response['Reservations'])} reservations")
                total_instances = sum(len(res.get('Instances', [])) for res in response['Reservations'])
                print(f"EC2 Call - Total instances: {total_instances}")
            elif method == 'describe_volumes' and 'Volumes' in response:
                print(f"EC2 Call - Found {len(response['Volumes'])} volumes")
            elif method == 'describe_addresses' and 'Addresses' in response:
                print(f"EC2 Call - Found {len(response['Addresses'])} addresses")
        elif client_type == 'elbv2':
            if method == 'describe_load_balancers' and 'LoadBalancers' in response:
                print(f"ELB Call - Found {len(response['LoadBalancers'])} load balancers")
            elif method == 'describe_target_groups' and 'TargetGroups' in response:
                print(f"ELB Call - Found {len(response['TargetGroups'])} target groups")
        
        # Remove ResponseMetadata para limpar o output
        if 'ResponseMetadata' in response:
            del response['ResponseMetadata']
        
        # Aplicar limitação aos recursos retornados
        original_response = response.copy()
        total_resources = 0
        truncated = False
        
        if client_type == 'ec2':
            if method == 'describe_instances' and 'Reservations' in response:
                # Para instâncias, limitar o número total de instâncias
                limited_reservations = []
                instances_count = 0
                
                for reservation in response['Reservations']:
                    if instances_count >= limit:
                        truncated = True
                        break
                    
                    limited_instances = []
                    for instance in reservation.get('Instances', []):
                        if instances_count >= limit:
                            truncated = True
                            break
                        limited_instances.append(instance)
                        instances_count += 1
                    
                    if limited_instances:
                        limited_reservation = reservation.copy()
                        limited_reservation['Instances'] = limited_instances
                        limited_reservations.append(limited_reservation)
                
                total_resources = sum(len(res.get('Instances', [])) for res in original_response['Reservations'])
                response['Reservations'] = limited_reservations
                
            elif method == 'describe_volumes' and 'Volumes' in response:
                total_resources = len(response['Volumes'])
                response['Volumes'] = response['Volumes'][:limit]
                truncated = total_resources > limit
                
            elif method == 'describe_addresses' and 'Addresses' in response:
                total_resources = len(response['Addresses'])
                response['Addresses'] = response['Addresses'][:limit]
                truncated = total_resources > limit
                
            elif method == 'describe_vpcs' and 'Vpcs' in response:
                total_resources = len(response['Vpcs'])
                response['Vpcs'] = response['Vpcs'][:limit]
                truncated = total_resources > limit
                
            elif method == 'describe_subnets' and 'Subnets' in response:
                total_resources = len(response['Subnets'])
                response['Subnets'] = response['Subnets'][:limit]
                truncated = total_resources > limit
                
            elif method == 'describe_security_groups' and 'SecurityGroups' in response:
                total_resources = len(response['SecurityGroups'])
                response['SecurityGroups'] = response['SecurityGroups'][:limit]
                truncated = total_resources > limit
                
        elif client_type == 'elbv2':
            if method == 'describe_load_balancers' and 'LoadBalancers' in response:
                total_resources = len(response['LoadBalancers'])
                response['LoadBalancers'] = response['LoadBalancers'][:limit]
                truncated = total_resources > limit
                
            elif method == 'describe_target_groups' and 'TargetGroups' in response:
                total_resources = len(response['TargetGroups'])
                response['TargetGroups'] = response['TargetGroups'][:limit]
                truncated = total_resources > limit
        
        # Adicionar metadados sobre limitação
        response['_meta'] = {
            'limit_applied': limit,
            'total_resources_found': total_resources,
            'resources_returned': min(total_resources, limit),
            'truncated': truncated,
            'method': method,
            'client_type': client_type
        }
        
        # Verificar se há dados úteis na resposta
        has_data = False
        if client_type == 'ec2':
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
        elif client_type == 'elbv2':
            if method == 'describe_load_balancers' and response.get('LoadBalancers'):
                has_data = len(response['LoadBalancers']) > 0
            elif method == 'describe_target_groups' and response.get('TargetGroups'):
                has_data = len(response['TargetGroups']) > 0
            else:
                has_data = bool(response and len(response) > 0)
        
        if not has_data:
            print(f"{client_type.upper()} Call - Warning: No data returned for {method}")
            response['_meta'] = {
                'warning': f'Nenhum dado encontrado para {method}',
                'possible_reasons': [
                    'Não há recursos deste tipo na conta',
                    'Recursos podem estar em outras regiões',
                    'Permissões IAM podem estar limitadas',
                    'Recursos podem ter sido filtrados'
                ]
            }
            
        print(f"{client_type.upper()} Call - Success: {method} (has_data: {has_data})")
        return json.dumps(response, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except AttributeError as e:
        import traceback
        tb = traceback.format_exc()
        print(f"{client_type.upper()} Call - AttributeError: {e}")
        print(f"{client_type.upper()} Call - Traceback:\n{tb}")
        return json.dumps({
            "error": f"Método '{method}' não existe no cliente {client_type}",
            "details": str(e),
            "client_type": client_type,
            "traceback": tb,
            "suggestion": f"Verifique se o método {method} está disponível no serviço {client_type}"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = str(e)
        print(f"{client_type.upper()} Call - Error: {error_msg}")
        print(f"{client_type.upper()} Call - Traceback:\n{tb}")
        
        # Tratamento de erros específicos com informações detalhadas
        if "InvalidParameterValue" in error_msg:
            return json.dumps({
                "error": "Parâmetros inválidos fornecidos",
                "details": error_msg,
                "suggestion": "Verifique os parâmetros e tente novamente",
                "client_type": client_type,
                "traceback": tb
            }, ensure_ascii=False, indent=2)
        elif "UnauthorizedOperation" in error_msg:
            return json.dumps({
                "error": "Operação não autorizada",
                "details": error_msg,
                "suggestion": f"Verifique as permissões IAM para {client_type}",
                "client_type": client_type,
                "traceback": tb
            }, ensure_ascii=False, indent=2)
        elif "InvalidInstanceID" in error_msg:
            return json.dumps({
                "error": "ID de instância inválido",
                "details": error_msg,
                "suggestion": "Verifique se o ID da instância existe e está correto",
                "client_type": client_type,
                "traceback": tb
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "error": f"Erro ao executar {method}",
                "details": error_msg,
                "client_type": client_type,
                "traceback": tb,
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
def find_instances_by_tag(tag_key: str, tag_value: str = None, limit: int = 5) -> str:
    """
    Busca instâncias EC2 por uma tag específica ou lista todas as instâncias com uma determinada tag.
    
    Args:
        tag_key: Chave da tag (ex: 'Name', 'Environment', 'Project')
        tag_value: Valor da tag (opcional). Se não fornecido, lista todos os valores para essa tag
        limit: Número máximo de instâncias a retornar (padrão: 5)
        
    Returns:
        JSON com instâncias encontradas e suas informações básicas (limitado)
        
    Exemplos:
    - find_instances_by_tag("Name", "Valhalla")
    - find_instances_by_tag("Environment", "production", limit=10)
    - find_instances_by_tag("Project", limit=3)  # Lista até 3 instâncias com tag Project
    """
    print(f"BUSCANDO INSTÂNCIAS POR TAG: {tag_key}={tag_value or '*'} - Limite: {limit}")
    
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
        total_instances_found = 0
        
        for reservation in instances_response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                total_instances_found += 1
                
                # Aplicar limite
                if len(instances_info) >= limit:
                    continue
                
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
                "search_type": "specific_value" if tag_value else "all_values",
                "limit_applied": limit
            },
            "results_summary": {
                "total_instances_found": total_instances_found,
                "instances_returned": len(instances_info),
                "truncated": total_instances_found > limit,
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


@tool
def identify_orphaned_resources(limit: int = 5) -> str:
    """
    Identifica recursos órfãos (não utilizados) na conta AWS com limitação configurável.
    Prioriza recursos por impacto financeiro potencial.
    
    Args:
        limit: Número máximo de recursos órfãos a retornar por categoria (padrão: 5)
    
    Returns:
        JSON com recursos órfãos identificados, priorizados por economia potencial
        
    Recursos órfãos identificados:
    - Volumes EBS não anexados
    - Elastic IPs não associados
    - Snapshots antigos (>90 dias)
    - Load Balancers sem targets
    - Security Groups não utilizados
    """
    print(f"IDENTIFICANDO RECURSOS ÓRFÃOS - Limite: {limit}")
    
    try:
        cost_explorer = CostExplorer()
        session = cost_explorer.aws_client.session
        ec2_client = session.client('ec2')
        elbv2_client = session.client('elbv2')
        
        orphaned_resources = {
            "analysis_timestamp": datetime.now().isoformat(),
            "limit_applied": limit,
            "summary": {
                "total_orphaned_resources": 0,
                "estimated_monthly_savings": 0.0,
                "categories_analyzed": 5
            },
            "orphaned_resources": {}
        }
        
        # 1. Volumes EBS não anexados
        print("Identificando volumes EBS órfãos...")
        try:
            volumes_response = ec2_client.describe_volumes(
                Filters=[
                    {
                        'Name': 'status',
                        'Values': ['available']  # Volumes não anexados
                    }
                ]
            )
            
            orphaned_volumes = []
            for volume in volumes_response.get('Volumes', []):
                volume_id = volume.get('VolumeId')
                size_gb = volume.get('Size', 0)
                volume_type = volume.get('VolumeType', 'gp2')
                create_time = volume.get('CreateTime')
                
                # Estimativa de custo mensal (preços aproximados)
                cost_per_gb = {
                    'gp2': 0.10, 'gp3': 0.08, 'io1': 0.125, 'io2': 0.125,
                    'st1': 0.045, 'sc1': 0.025, 'standard': 0.05
                }
                monthly_cost = size_gb * cost_per_gb.get(volume_type, 0.10)
                
                orphaned_volumes.append({
                    "resource_id": volume_id,
                    "size_gb": size_gb,
                    "volume_type": volume_type,
                    "create_time": create_time.isoformat() if create_time else None,
                    "estimated_monthly_cost": round(monthly_cost, 2),
                    "priority": "HIGH" if monthly_cost > 20 else "MEDIUM" if monthly_cost > 5 else "LOW"
                })
            
            # Ordenar por custo e limitar
            orphaned_volumes.sort(key=lambda x: x['estimated_monthly_cost'], reverse=True)
            total_volumes = len(orphaned_volumes)
            limited_volumes = orphaned_volumes[:limit]
            
            orphaned_resources["orphaned_resources"]["ebs_volumes"] = {
                "total_found": total_volumes,
                "resources_returned": len(limited_volumes),
                "truncated": total_volumes > limit,
                "total_estimated_savings": sum(v['estimated_monthly_cost'] for v in orphaned_volumes),
                "resources": limited_volumes
            }
            
            orphaned_resources["summary"]["total_orphaned_resources"] += total_volumes
            orphaned_resources["summary"]["estimated_monthly_savings"] += sum(v['estimated_monthly_cost'] for v in orphaned_volumes)
            
        except Exception as e:
            print(f"Erro ao identificar volumes órfãos: {e}")
            orphaned_resources["orphaned_resources"]["ebs_volumes"] = {"error": str(e)}
        
        # 2. Elastic IPs não associados
        print("Identificando Elastic IPs órfãos...")
        try:
            addresses_response = ec2_client.describe_addresses()
            
            orphaned_ips = []
            for address in addresses_response.get('Addresses', []):
                # Elastic IP é órfão se não está associado
                if 'AssociationId' not in address:
                    allocation_id = address.get('AllocationId')
                    public_ip = address.get('PublicIp')
                    
                    # Custo de Elastic IP não associado: ~$3.65/mês
                    monthly_cost = 3.65
                    
                    orphaned_ips.append({
                        "resource_id": allocation_id or public_ip,
                        "public_ip": public_ip,
                        "domain": address.get('Domain', 'vpc'),
                        "estimated_monthly_cost": monthly_cost,
                        "priority": "MEDIUM"
                    })
            
            total_ips = len(orphaned_ips)
            limited_ips = orphaned_ips[:limit]
            
            orphaned_resources["orphaned_resources"]["elastic_ips"] = {
                "total_found": total_ips,
                "resources_returned": len(limited_ips),
                "truncated": total_ips > limit,
                "total_estimated_savings": sum(ip['estimated_monthly_cost'] for ip in orphaned_ips),
                "resources": limited_ips
            }
            
            orphaned_resources["summary"]["total_orphaned_resources"] += total_ips
            orphaned_resources["summary"]["estimated_monthly_savings"] += sum(ip['estimated_monthly_cost'] for ip in orphaned_ips)
            
        except Exception as e:
            print(f"Erro ao identificar Elastic IPs órfãos: {e}")
            orphaned_resources["orphaned_resources"]["elastic_ips"] = {"error": str(e)}
        
        # 3. Snapshots antigos (>90 dias)
        print("Identificando snapshots antigos...")
        try:
            snapshots_response = ec2_client.describe_snapshots(OwnerIds=['self'])
            
            orphaned_snapshots = []
            cutoff_date = datetime.now() - timedelta(days=90)
            
            for snapshot in snapshots_response.get('Snapshots', []):
                start_time = snapshot.get('StartTime')
                if start_time and start_time < cutoff_date:
                    snapshot_id = snapshot.get('SnapshotId')
                    volume_size = snapshot.get('VolumeSize', 0)
                    
                    # Custo de snapshot: ~$0.05 por GB/mês
                    monthly_cost = volume_size * 0.05
                    
                    orphaned_snapshots.append({
                        "resource_id": snapshot_id,
                        "volume_size_gb": volume_size,
                        "start_time": start_time.isoformat(),
                        "age_days": (datetime.now() - start_time.replace(tzinfo=None)).days,
                        "estimated_monthly_cost": round(monthly_cost, 2),
                        "priority": "HIGH" if monthly_cost > 10 else "MEDIUM" if monthly_cost > 2 else "LOW"
                    })
            
            # Ordenar por custo e limitar
            orphaned_snapshots.sort(key=lambda x: x['estimated_monthly_cost'], reverse=True)
            total_snapshots = len(orphaned_snapshots)
            limited_snapshots = orphaned_snapshots[:limit]
            
            orphaned_resources["orphaned_resources"]["old_snapshots"] = {
                "total_found": total_snapshots,
                "resources_returned": len(limited_snapshots),
                "truncated": total_snapshots > limit,
                "cutoff_days": 90,
                "total_estimated_savings": sum(s['estimated_monthly_cost'] for s in orphaned_snapshots),
                "resources": limited_snapshots
            }
            
            orphaned_resources["summary"]["total_orphaned_resources"] += total_snapshots
            orphaned_resources["summary"]["estimated_monthly_savings"] += sum(s['estimated_monthly_cost'] for s in orphaned_snapshots)
            
        except Exception as e:
            print(f"Erro ao identificar snapshots órfãos: {e}")
            orphaned_resources["orphaned_resources"]["old_snapshots"] = {"error": str(e)}
        
        # 4. Load Balancers sem targets
        print("Identificando Load Balancers órfãos...")
        try:
            lbs_response = elbv2_client.describe_load_balancers()
            
            orphaned_lbs = []
            for lb in lbs_response.get('LoadBalancers', []):
                lb_arn = lb.get('LoadBalancerArn')
                lb_name = lb.get('LoadBalancerName')
                lb_type = lb.get('Type', 'application')
                
                # Verificar se tem target groups com targets saudáveis
                try:
                    tgs_response = elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn)
                    has_healthy_targets = False
                    
                    for tg in tgs_response.get('TargetGroups', []):
                        tg_arn = tg.get('TargetGroupArn')
                        health_response = elbv2_client.describe_target_health(TargetGroupArn=tg_arn)
                        
                        healthy_targets = [
                            target for target in health_response.get('TargetHealthDescriptions', [])
                            if target.get('TargetHealth', {}).get('State') == 'healthy'
                        ]
                        
                        if healthy_targets:
                            has_healthy_targets = True
                            break
                    
                    if not has_healthy_targets:
                        # Estimativa de custo de ALB: ~$16/mês, NLB: ~$16/mês
                        monthly_cost = 16.0
                        
                        orphaned_lbs.append({
                            "resource_id": lb_arn,
                            "load_balancer_name": lb_name,
                            "type": lb_type,
                            "estimated_monthly_cost": monthly_cost,
                            "priority": "HIGH"
                        })
                        
                except Exception as e:
                    print(f"Erro ao verificar targets do LB {lb_name}: {e}")
            
            total_lbs = len(orphaned_lbs)
            limited_lbs = orphaned_lbs[:limit]
            
            orphaned_resources["orphaned_resources"]["load_balancers"] = {
                "total_found": total_lbs,
                "resources_returned": len(limited_lbs),
                "truncated": total_lbs > limit,
                "total_estimated_savings": sum(lb['estimated_monthly_cost'] for lb in orphaned_lbs),
                "resources": limited_lbs
            }
            
            orphaned_resources["summary"]["total_orphaned_resources"] += total_lbs
            orphaned_resources["summary"]["estimated_monthly_savings"] += sum(lb['estimated_monthly_cost'] for lb in orphaned_lbs)
            
        except Exception as e:
            print(f"Erro ao identificar Load Balancers órfãos: {e}")
            orphaned_resources["orphaned_resources"]["load_balancers"] = {"error": str(e)}
        
        # Gerar recomendações priorizadas
        orphaned_resources["recommendations"] = _generate_orphaned_resources_recommendations(orphaned_resources)
        
        print(f"Análise de recursos órfãos concluída: {orphaned_resources['summary']['total_orphaned_resources']} recursos encontrados")
        return json.dumps(orphaned_resources, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erro na identificação de recursos órfãos: {e}")
        print(f"Traceback:\n{tb}")
        
        return json.dumps({
            "error": f"Erro na identificação de recursos órfãos",
            "details": str(e),
            "traceback": tb,
            "suggestion": "Verifique permissões EC2 e ELB"
        }, ensure_ascii=False, indent=2)


def _generate_orphaned_resources_recommendations(orphaned_data: Dict[str, Any]) -> List[str]:
    """Gera recomendações priorizadas para recursos órfãos."""
    recommendations = []
    
    total_savings = orphaned_data.get("summary", {}).get("estimated_monthly_savings", 0)
    
    if total_savings > 100:
        recommendations.append(f"ALTA PRIORIDADE: Economia potencial de ${total_savings:.2f}/mês identificada")
    elif total_savings > 20:
        recommendations.append(f"MÉDIA PRIORIDADE: Economia potencial de ${total_savings:.2f}/mês identificada")
    
    # Recomendações específicas por tipo de recurso
    ebs_data = orphaned_data.get("orphaned_resources", {}).get("ebs_volumes", {})
    if ebs_data.get("total_found", 0) > 0:
        ebs_savings = ebs_data.get("total_estimated_savings", 0)
        recommendations.append(f"Volumes EBS: {ebs_data['total_found']} volumes órfãos (${ebs_savings:.2f}/mês)")
    
    ip_data = orphaned_data.get("orphaned_resources", {}).get("elastic_ips", {})
    if ip_data.get("total_found", 0) > 0:
        ip_savings = ip_data.get("total_estimated_savings", 0)
        recommendations.append(f"Elastic IPs: {ip_data['total_found']} IPs não utilizados (${ip_savings:.2f}/mês)")
    
    snapshot_data = orphaned_data.get("orphaned_resources", {}).get("old_snapshots", {})
    if snapshot_data.get("total_found", 0) > 0:
        snapshot_savings = snapshot_data.get("total_estimated_savings", 0)
        recommendations.append(f"Snapshots antigos: {snapshot_data['total_found']} snapshots >90 dias (${snapshot_savings:.2f}/mês)")
    
    lb_data = orphaned_data.get("orphaned_resources", {}).get("load_balancers", {})
    if lb_data.get("total_found", 0) > 0:
        lb_savings = lb_data.get("total_estimated_savings", 0)
        recommendations.append(f"Load Balancers: {lb_data['total_found']} LBs sem targets (${lb_savings:.2f}/mês)")
    
    if total_savings > 50:
        recommendations.append("Recomenda-se implementar automação para limpeza regular de recursos órfãos")
    
    return recommendations


@tool
def analyze_multiple_tags_costs(tag_keys: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Analisa custos de múltiplas tags simultaneamente para um período específico.
    
    Args:
        tag_keys: Lista de chaves de tags separadas por vírgula (ex: "Environment,Project,kubernetes.io/cluster/jera-cluster")
        start_date: Data inicial no formato YYYY-MM-DD (opcional, padrão: 30 dias atrás)
        end_date: Data final no formato YYYY-MM-DD (opcional, padrão: hoje)
        
    Returns:
        JSON com análise de custos para cada tag especificada
        
    Exemplos:
    - analyze_multiple_tags_costs("Environment,Project,Owner")
    - analyze_multiple_tags_costs("aws:eks:cluster-name,kubernetes.io/cluster/jera-cluster", "2024-05-01", "2024-05-31")
    """
    print(f"ANALISANDO CUSTOS DE MÚLTIPLAS TAGS: {tag_keys}")
    
    try:
        # Processar lista de tags
        tag_list = [tag.strip() for tag in tag_keys.split(',') if tag.strip()]
        
        if not tag_list:
            return json.dumps({
                "error": "Nenhuma tag válida fornecida",
                "suggestion": "Forneça uma lista de tags separadas por vírgula",
                "example": "Environment,Project,Owner"
            }, ensure_ascii=False, indent=2)
        
        cost_explorer = CostExplorer()
        
        # Definir período de análise
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Validar e ajustar as datas
        validated_start, validated_end = validate_and_adjust_date_range(start_date, end_date)
        
        analysis_result = {
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_period": {
                "start_date": validated_start,
                "end_date": validated_end,
                "days": (datetime.strptime(validated_end, '%Y-%m-%d') - datetime.strptime(validated_start, '%Y-%m-%d')).days
            },
            "tags_analyzed": tag_list,
            "summary": {
                "total_tags_requested": len(tag_list),
                "tags_with_costs": 0,
                "tags_without_costs": 0,
                "total_cost_usd": 0.0,
                "total_cost_brl": 0.0
            },
            "tag_analysis": []
        }
        
        # Analisar cada tag individualmente
        for tag_key in tag_list:
            print(f"Analisando tag: {tag_key}")
            
            try:
                # Buscar custos por esta tag específica
                tag_cost_response = cost_explorer.get_cost_by_tag(tag_key, validated_start, validated_end)
                
                tag_analysis = {
                    "tag_key": tag_key,
                    "has_costs": False,
                    "total_cost_usd": 0.0,
                    "total_cost_brl": 0.0,
                    "tag_values": [],
                    "error": None
                }
                
                # Processar resultados
                if tag_cost_response.get('ResultsByTime'):
                    tag_values_costs = {}
                    
                    for period in tag_cost_response['ResultsByTime']:
                        for group in period.get('Groups', []):
                            tag_value = group.get('Keys', [''])[0]
                            cost_usd = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                            
                            # Limpar valor da tag (remover prefixos se houver)
                            if '$' in tag_value:
                                tag_value = tag_value.split('$')[-1]
                            tag_value = tag_value.rstrip('$')
                            
                            # Ignorar valores vazios ou "NoTag"
                            if tag_value and tag_value.lower() not in ['notag', 'no tag', '']:
                                if tag_value not in tag_values_costs:
                                    tag_values_costs[tag_value] = 0.0
                                tag_values_costs[tag_value] += cost_usd
                    
                    # Organizar valores por custo
                    if tag_values_costs:
                        tag_analysis["has_costs"] = True
                        tag_analysis["total_cost_usd"] = sum(tag_values_costs.values())
                        tag_analysis["total_cost_brl"] = tag_analysis["total_cost_usd"] * 5.5  # Taxa aproximada
                        
                        # Criar lista de valores ordenada por custo
                        for tag_value, cost_usd in sorted(tag_values_costs.items(), key=lambda x: x[1], reverse=True):
                            tag_analysis["tag_values"].append({
                                "value": tag_value,
                                "cost_usd": round(cost_usd, 2),
                                "cost_brl": round(cost_usd * 5.5, 2),
                                "percentage": round((cost_usd / tag_analysis["total_cost_usd"]) * 100, 1) if tag_analysis["total_cost_usd"] > 0 else 0
                            })
                        
                        # Atualizar totais gerais
                        analysis_result["summary"]["tags_with_costs"] += 1
                        analysis_result["summary"]["total_cost_usd"] += tag_analysis["total_cost_usd"]
                        analysis_result["summary"]["total_cost_brl"] += tag_analysis["total_cost_brl"]
                        
                        print(f"✅ Tag '{tag_key}': ${tag_analysis['total_cost_usd']:.2f} encontrados")
                    else:
                        analysis_result["summary"]["tags_without_costs"] += 1
                        print(f"⚠️  Tag '{tag_key}': Nenhum custo encontrado")
                else:
                    analysis_result["summary"]["tags_without_costs"] += 1
                    print(f"⚠️  Tag '{tag_key}': Nenhum dado retornado")
                
            except Exception as e:
                tag_analysis["error"] = str(e)
                analysis_result["summary"]["tags_without_costs"] += 1
                print(f"❌ Erro ao analisar tag '{tag_key}': {e}")
            
            analysis_result["tag_analysis"].append(tag_analysis)
        
        # Gerar insights e recomendações
        analysis_result["insights"] = []
        analysis_result["recommendations"] = []
        
        if analysis_result["summary"]["tags_with_costs"] == 0:
            analysis_result["insights"].append("Nenhuma das tags especificadas possui custos associados no período analisado")
            analysis_result["recommendations"].extend([
                "Verifique se as tags existem nos recursos da conta AWS",
                "Considere usar um período de análise maior",
                "Verifique se os recursos estão sendo tagueados corretamente"
            ])
        else:
            # Identificar tag mais cara
            tags_with_costs = [tag for tag in analysis_result["tag_analysis"] if tag["has_costs"]]
            if tags_with_costs:
                most_expensive_tag = max(tags_with_costs, key=lambda x: x["total_cost_usd"])
                analysis_result["insights"].append(f"Tag mais cara: '{most_expensive_tag['tag_key']}' com ${most_expensive_tag['total_cost_usd']:.2f}")
            
            # Recomendações baseadas nos resultados
            if analysis_result["summary"]["total_cost_usd"] > 100:
                analysis_result["recommendations"].append("Considere implementar políticas de cost optimization para as tags com maior custo")
            
            if analysis_result["summary"]["tags_without_costs"] > 0:
                analysis_result["recommendations"].append(f"{analysis_result['summary']['tags_without_costs']} tags não possuem custos - verifique se estão sendo aplicadas corretamente")
        
        # Adicionar informações sobre tags Kubernetes específicas
        k8s_tags = [tag for tag in tag_list if 'kubernetes' in tag.lower() or 'eks' in tag.lower()]
        if k8s_tags:
            analysis_result["kubernetes_insights"] = {
                "kubernetes_tags_found": len(k8s_tags),
                "tags": k8s_tags,
                "note": "Tags relacionadas ao Kubernetes/EKS detectadas - custos podem estar distribuídos entre diferentes recursos (EC2, EBS, ELB, etc.)"
            }
        
        print(f"Análise concluída: {analysis_result['summary']['tags_with_costs']}/{len(tag_list)} tags com custos")
        
        return json.dumps(analysis_result, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erro na análise de múltiplas tags: {e}")
        print(f"Traceback:\n{tb}")
        
        return json.dumps({
            "error": f"Erro na análise de múltiplas tags",
            "details": str(e),
            "traceback": tb,
            "suggestion": "Verifique se as tags estão no formato correto e se você tem permissões adequadas"
        }, ensure_ascii=False, indent=2)


 