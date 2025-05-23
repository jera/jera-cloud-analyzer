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
    check_account_data_availability
)

from src.ia.tools.utility_tools import (
    format_currency,
    get_current_date,
    get_date_from_period,
    all_dimensions
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
    format_currency,
    get_current_date,
    get_date_from_period,
    all_dimensions
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
    'format_currency',
    'get_current_date',
    'get_date_from_period',
    'all_dimensions'
] 