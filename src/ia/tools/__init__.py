"""
Módulo de ferramentas para o agente de IA de análise de custos AWS.
"""

# Importar todas as ferramentas
from src.ia.tools.aws_data_tools import (
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
    analyze_tag_specific_values
)

from src.ia.tools.utility_tools import (
    format_currency,
    get_current_date,
    get_date_from_period,
    all_dimensions,
    get_safe_date_range
)

from src.ia.tools.cloudwatch_tools import (
    get_instance_performance_metrics,
    analyze_ec2_fleet_performance,
    get_network_traffic_analysis
)

from src.ia.tools.service_tools import (
    resolve_service_name,
    suggest_services,
    list_all_services,
    refresh_services_cache
)

# Lista com todas as ferramentas para fácil importação
ALL_TOOLS = [
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
]

__all__ = [
    'ALL_TOOLS',
    'get_top_services',
    'get_service_details',
    'get_aws_tags',
    'get_dimension_values',
    'discover_account_resources',
    'validate_and_analyze_service',
    'analyze_account_coverage',
    'get_account_context_data',
    'check_account_data_availability',
    'aws_ec2_call',
    'get_instance_cost_by_name',
    'find_instances_by_tag',
    'audit_governance_tags',
    'identify_orphaned_resources',
    'analyze_multiple_tags_costs',
    'analyze_tag_specific_values',
    'format_currency',
    'get_current_date',
    'get_date_from_period',
    'all_dimensions',
    'get_safe_date_range',
    'get_instance_performance_metrics',
    'analyze_ec2_fleet_performance',
    'get_network_traffic_analysis',
    'resolve_service_name',
    'suggest_services',
    'list_all_services',
    'refresh_services_cache'
] 