"""
Adaptadores Haystack para as ferramentas de análise AWS.
Estes wrappers decoram as funções core com @tool do Haystack.
"""

from typing import Optional
from haystack.tools import tool

# Importar todas as funções core centralizadas
from src.ia.tools import (
    get_top_services,
    get_service_details,
    get_aws_tags,
    get_dimension_values,
    discover_account_resources,
    validate_and_analyze_service,
    analyze_account_coverage,
    get_account_context_data,
    check_account_data_availability,
    aws_ec2_call,
    get_instance_cost_by_name,
    find_instances_by_tag,
    audit_governance_tags,
    identify_orphaned_resources,
    analyze_multiple_tags_costs,
    analyze_tag_specific_values,
    format_currency,
    get_current_date,
    get_date_from_period,
    all_dimensions,
    get_safe_date_range,
    get_instance_performance_metrics,
    analyze_ec2_fleet_performance,
    get_network_traffic_analysis,
    resolve_service_name,
    suggest_services,
    list_all_services,
    refresh_services_cache
)

# ===============================
# HAYSTACK TOOLS - AWS DATA
# ===============================

@tool
def haystack_get_top_services(start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 5) -> str:
    """
    Obtém os top serviços mais caros da AWS.
    
    Args:
        start_date: Data de início (YYYY-MM-DD) - opcional, padrão últimos 30 dias
        end_date: Data de fim (YYYY-MM-DD) - opcional, padrão hoje
        limit: Número de serviços a retornar (padrão 5)
    """
    return get_top_services(start_date, end_date, limit)

@tool
def haystack_get_service_details(service_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Obtém detalhes de custos de um serviço específico com resolução automática do nome.
    
    Args:
        service_name: Nome do serviço AWS (aceita apelidos como 'rds', 'ec2', etc.)
        start_date: Data de início (YYYY-MM-DD) - opcional
        end_date: Data de fim (YYYY-MM-DD) - opcional
    """
    return get_service_details(service_name, start_date, end_date)

@tool
def haystack_get_aws_tags() -> str:
    """
    Obtém as tags da AWS disponíveis na conta.
    """
    return get_aws_tags()

@tool
def haystack_get_dimension_values(dimension_name: str) -> str:
    """
    Obtém os valores de uma dimensão específica.
    
    Args:
        dimension_name: Dimensão desejada ('SERVICE', 'USAGE_TYPE', 'INSTANCE_TYPE', etc.)
    """
    return get_dimension_values(dimension_name)

@tool
def haystack_discover_account_resources(limit: int = 5) -> str:
    """
    Descobre recursos disponíveis na conta AWS.
    
    Args:
        limit: Número máximo de recursos por categoria (padrão 5)
    """
    return discover_account_resources(limit)

@tool
def haystack_validate_service(service_name: str) -> str:
    """
    Valida e analisa um serviço específico com sugestões e correções.
    
    Args:
        service_name: Nome do serviço a ser validado
    """
    return validate_and_analyze_service(service_name)

@tool
def haystack_analyze_account_coverage() -> str:
    """
    Analisa a cobertura de dados disponíveis na conta AWS.
    """
    return analyze_account_coverage()

@tool
def haystack_get_account_context_data() -> str:
    """
    Obtém dados de contexto completos da conta AWS.
    """
    return get_account_context_data()

@tool
def haystack_check_data_availability() -> str:
    """
    Verifica a disponibilidade de dados na conta AWS.
    """
    return check_account_data_availability()

@tool
def haystack_aws_ec2_call(
    method: str, 
    instance_ids: Optional[str] = None, 
    volume_ids: Optional[str] = None,
    vpc_ids: Optional[str] = None, 
    subnet_ids: Optional[str] = None, 
    group_ids: Optional[str] = None, 
    region_name: Optional[str] = None, 
    limit: int = 5
) -> str:
    """
    Executa chamadas específicas da API EC2.
    
    Args:
        method: Método EC2 a ser executado
        instance_ids: IDs de instâncias (opcional)
        volume_ids: IDs de volumes (opcional)
        vpc_ids: IDs de VPCs (opcional)
        subnet_ids: IDs de subnets (opcional)
        group_ids: IDs de security groups (opcional)
        region_name: Nome da região (opcional)
        limit: Limite de resultados (padrão 5)
    """
    return aws_ec2_call(method, instance_ids, volume_ids, vpc_ids, subnet_ids, group_ids, region_name, limit)

@tool
def haystack_get_instance_cost_by_name(instance_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Obtém custos de uma instância EC2 específica pelo nome.
    
    Args:
        instance_name: Nome da instância EC2
        start_date: Data de início (YYYY-MM-DD) - opcional
        end_date: Data de fim (YYYY-MM-DD) - opcional
    """
    return get_instance_cost_by_name(instance_name, start_date, end_date)

@tool
def haystack_find_instances_by_tag(tag_key: str, tag_value: Optional[str] = None, limit: int = 5) -> str:
    """
    Encontra instâncias EC2 por tag específica.
    
    Args:
        tag_key: Chave da tag
        tag_value: Valor da tag (opcional)
        limit: Número máximo de instâncias (padrão 5)
    """
    return find_instances_by_tag(tag_key, tag_value, limit)

@tool
def haystack_audit_governance_tags() -> str:
    """
    Audita tags de governança nas instâncias EC2.
    """
    return audit_governance_tags()

@tool
def haystack_identify_orphaned_resources(limit: int = 5) -> str:
    """
    Identifica recursos órfãos (não utilizados) na conta AWS.
    
    Args:
        limit: Número máximo de recursos por categoria (padrão 5)
    """
    return identify_orphaned_resources(limit)

@tool
def haystack_analyze_tags_costs(tag_keys: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Analisa custos de múltiplas tags específicas.
    
    Args:
        tag_keys: Chaves das tags separadas por vírgula
        start_date: Data de início (YYYY-MM-DD) - opcional
        end_date: Data de fim (YYYY-MM-DD) - opcional
    """
    return analyze_multiple_tags_costs(tag_keys, start_date, end_date)

@tool
def haystack_analyze_tag_values(tag_key: str, tag_values: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Analisa custos de valores específicos de uma tag.
    
    Args:
        tag_key: Chave da tag
        tag_values: Valores da tag separados por vírgula
        start_date: Data de início (YYYY-MM-DD) - opcional
        end_date: Data de fim (YYYY-MM-DD) - opcional
    """
    return analyze_tag_specific_values(tag_key, tag_values, start_date, end_date)

# ===============================
# HAYSTACK TOOLS - UTILITIES
# ===============================

@tool
def haystack_format_currency(amount: float, currency: str = "USD", to_brl: bool = True) -> str:
    """
    Formata valores monetários com conversão automática USD->BRL.
    
    Args:
        amount: Valor a ser formatado
        currency: Moeda original (USD, BRL)
        to_brl: Se deve converter para BRL
    """
    return format_currency(amount, currency, to_brl)

@tool
def haystack_get_current_date() -> str:
    """
    Retorna a data atual no formato YYYY-MM-DD.
    """
    return get_current_date()

@tool
def haystack_get_date_from_period(period_description: str) -> str:
    """
    Converte descrições de período em datas específicas com validação de limite.
    
    Args:
        period_description: Descrição como "último mês", "últimos 3 meses", etc.
    """
    result = get_date_from_period(period_description)
    import json
    return json.dumps(result, ensure_ascii=False, indent=2)

@tool
def haystack_all_dimensions() -> str:
    """
    Lista todas as dimensões disponíveis para análise de custos AWS.
    """
    dimensions = all_dimensions()
    import json
    return json.dumps(dimensions, ensure_ascii=False, indent=2)

@tool
def haystack_get_safe_date_range(months_back: int = 1) -> str:
    """
    Obtém um intervalo de datas seguro respeitando limitações do Cost Explorer.
    
    Args:
        months_back: Número de meses para trás (padrão 1)
    """
    result = get_safe_date_range(months_back)
    import json
    return json.dumps(result, ensure_ascii=False, indent=2)

# ===============================
# HAYSTACK TOOLS - CLOUDWATCH
# ===============================

@tool
def haystack_get_instance_metrics(instance_id: str, hours: int = 24, metrics: Optional[str] = None) -> str:
    """
    Obtém métricas de performance de uma instância EC2 específica via CloudWatch.
    
    Args:
        instance_id: ID da instância EC2 (ex: 'i-1234567890abcdef0')
        hours: Número de horas para análise (padrão: 24)
        metrics: Métricas específicas separadas por vírgula (opcional)
    """
    return get_instance_performance_metrics(instance_id, hours, metrics)

@tool
def haystack_analyze_fleet_perf(tag_key: Optional[str] = None, tag_value: Optional[str] = None, hours: int = 24, max_instances: int = 10) -> str:
    """
    Analisa performance de uma frota de instâncias EC2.
    
    Args:
        tag_key: Chave da tag para filtrar instâncias (opcional)
        tag_value: Valor da tag para filtrar instâncias (opcional)
        hours: Número de horas para análise (padrão: 24)
        max_instances: Número máximo de instâncias (padrão: 10)
    """
    return analyze_ec2_fleet_performance(tag_key, tag_value, hours, max_instances)

@tool
def haystack_get_network_analysis(instance_id: str, days: int = 7) -> str:
    """
    Analisa tráfego de rede de uma instância EC2.
    
    Args:
        instance_id: ID da instância EC2
        days: Número de dias para análise (padrão: 7)
    """
    return get_network_traffic_analysis(instance_id, days)

# ===============================
# HAYSTACK TOOLS - SERVICES
# ===============================

@tool
def haystack_resolve_service_name(service_name: str, auto_apply: bool = True) -> str:
    """
    Resolve o nome oficial de um serviço AWS a partir de um nome informal.
    
    Args:
        service_name: Nome do serviço (informal, apelido, ou oficial)
        auto_apply: Se deve aplicar automaticamente o melhor match (padrão: True)
    """
    return resolve_service_name(service_name, auto_apply)

@tool
def haystack_suggest_services(partial_name: str, limit: int = 10) -> str:
    """
    Sugere serviços AWS baseado em um nome parcial ou palavras-chave.
    
    Args:
        partial_name: Nome parcial ou palavra-chave
        limit: Número máximo de sugestões (padrão: 10)
    """
    return suggest_services(partial_name, limit)

@tool
def haystack_list_all_services(category_filter: Optional[str] = None) -> str:
    """
    Lista todos os serviços AWS conhecidos, opcionalmente filtrados por categoria.
    
    Args:
        category_filter: Filtro por categoria (compute, storage, database, networking, etc.)
    """
    return list_all_services(category_filter)

@tool
def haystack_refresh_services_cache() -> str:
    """
    Atualiza o cache de serviços AWS.
    """
    return refresh_services_cache()

# ===============================
# LISTA DE TODAS AS FERRAMENTAS HAYSTACK
# ===============================

HAYSTACK_TOOLS = [
    # AWS Data Tools
    haystack_get_top_services,
    haystack_get_service_details,
    haystack_get_aws_tags,
    haystack_get_dimension_values,
    haystack_discover_account_resources,
    haystack_validate_service,
    haystack_analyze_account_coverage,
    haystack_get_account_context_data,
    haystack_check_data_availability,
    haystack_aws_ec2_call,
    haystack_get_instance_cost_by_name,
    haystack_find_instances_by_tag,
    haystack_audit_governance_tags,
    haystack_identify_orphaned_resources,
    haystack_analyze_tags_costs,
    haystack_analyze_tag_values,
    
    # Utility Tools
    haystack_format_currency,
    haystack_get_current_date,
    haystack_get_date_from_period,
    haystack_all_dimensions,
    haystack_get_safe_date_range,
    
    # CloudWatch Tools
    haystack_get_instance_metrics,
    haystack_analyze_fleet_perf,
    haystack_get_network_analysis,
    
    # Service Tools
    haystack_resolve_service_name,
    haystack_suggest_services,
    haystack_list_all_services,
    haystack_refresh_services_cache
] 