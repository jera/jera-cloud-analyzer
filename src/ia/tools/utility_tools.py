"""
Ferramentas utilitárias para o agente de IA.
"""

from datetime import datetime
from haystack.tools import tool


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
    current_date = datetime.now().strftime('%Y-%m-%d')
    print(f"GET CURRENT DATE: {current_date}")
    return current_date


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