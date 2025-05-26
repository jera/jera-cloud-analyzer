"""
Ferramentas utilitárias para o agente de IA.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from haystack.tools import tool


class JsonEncoder(json.JSONEncoder):
    """Encoder JSON personalizado para lidar com tipos especiais como Decimal e datetime."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def validate_and_adjust_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """
    Valida e ajusta o intervalo de datas para estar dentro do limite de 14 meses do Cost Explorer.
    
    Args:
        start_date: Data de início no formato YYYY-MM-DD
        end_date: Data de fim no formato YYYY-MM-DD
        
    Returns:
        Tupla com (start_date_ajustada, end_date_ajustada)
    """
    try:
        # Data atual
        current_date = datetime.now()
        
        # Limite de 14 meses atrás
        limit_date = current_date - timedelta(days=14 * 30)  # Aproximadamente 14 meses
        
        # Converter strings para datetime
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Verificar se as datas estão dentro do limite
        adjusted_start = start_dt
        adjusted_end = end_dt
        adjustment_made = False
        
        if start_dt < limit_date:
            adjusted_start = limit_date
            adjustment_made = True
            
        if end_dt < limit_date:
            adjusted_end = limit_date
            adjustment_made = True
            
        # Se a data de fim for futura, ajustar para hoje
        if end_dt > current_date:
            adjusted_end = current_date
            adjustment_made = True
            
        # Converter de volta para strings
        adjusted_start_str = adjusted_start.strftime('%Y-%m-%d')
        adjusted_end_str = adjusted_end.strftime('%Y-%m-%d')
        
        if adjustment_made:
            print(f"⚠️  AJUSTE DE DATAS: Período original ({start_date} a {end_date}) ajustado para ({adjusted_start_str} a {adjusted_end_str}) devido às limitações do Cost Explorer (14 meses)")
            
        return adjusted_start_str, adjusted_end_str
        
    except Exception as e:
        print(f"❌ Erro ao validar datas: {e}")
        # Em caso de erro, retornar o último mês disponível
        current_date = datetime.now()
        end_date = current_date.strftime('%Y-%m-%d')
        start_date = (current_date - timedelta(days=30)).strftime('%Y-%m-%d')
        print(f"🔄 Usando período padrão: {start_date} a {end_date}")
        return start_date, end_date


@tool
def format_currency(amount: float, currency: str = "USD", to_brl: bool = True) -> str:
    """
    Formata valores monetários com conversão automática USD->BRL.
    
    Args:
        amount: Valor a ser formatado
        currency: Moeda original (USD, BRL)
        to_brl: Se deve converter para BRL
        
    Returns:
        Valor formatado como string
    """
    try:
        if to_brl and currency.upper() == "USD":
            # Taxa de conversão aproximada (USD para BRL)
            exchange_rate = 5.20  # Atualizar conforme necessário
            brl_amount = amount * exchange_rate
            return f"${amount:.2f} USD (~R$ {brl_amount:.2f} BRL)"
        elif currency.upper() == "BRL":
            return f"R$ {amount:.2f} BRL"
        else:
            return f"${amount:.2f} {currency.upper()}"
    except Exception as e:
        return f"Erro na formatação: {str(e)}"


@tool
def get_current_date() -> str:
    """
    Retorna a data atual no formato YYYY-MM-DD.
    
    Returns:
        Data atual formatada
    """
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        print(f"GET CURRENT DATE: {current_date}")
        return current_date
    except Exception as e:
        return f"Erro ao obter data: {str(e)}"


@tool
def get_date_from_period(period_description: str) -> Dict[str, str]:
    """
    Converte descrições de período em datas específicas com validação de limite.
    
    Args:
        period_description: Descrição como "último mês", "últimos 3 meses", etc.
        
    Returns:
        Dicionário com start_date e end_date validadas
    """
    try:
        current_date = datetime.now()
        
        # Mapear descrições para períodos
        period_mapping = {
            "último mês": 30,
            "últimos 2 meses": 60,
            "últimos 3 meses": 90,
            "últimos 6 meses": 180,
            "último ano": 365,
            "últimos 12 meses": 365,
            "última semana": 7,
            "últimas 2 semanas": 14,
            "último trimestre": 90
        }
        
        # Encontrar correspondência
        days_back = period_mapping.get(period_description.lower(), 30)
        
        # Calcular datas
        end_date = current_date.strftime('%Y-%m-%d')
        start_date = (current_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Validar e ajustar se necessário
        validated_start, validated_end = validate_and_adjust_date_range(start_date, end_date)
        
        result = {
            "start_date": validated_start,
            "end_date": validated_end,
            "period_description": period_description,
            "days_analyzed": days_back
        }
        
        print(f"GET DATE FROM PERIOD: {period_description} -> {validated_start} a {validated_end}")
        return result
        
    except Exception as e:
        # Em caso de erro, retornar último mês válido
        current_date = datetime.now()
        end_date = current_date.strftime('%Y-%m-%d')
        start_date = (current_date - timedelta(days=30)).strftime('%Y-%m-%d')
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "period_description": "último mês (fallback)",
            "days_analyzed": 30,
            "error": str(e)
        }


@tool
def all_dimensions() -> List[str]:
    """
    Lista todas as dimensões disponíveis para análise de custos AWS.
    
    Returns:
        Lista de dimensões suportadas
    """
    dimensions = [
        "SERVICE",
        "LINKED_ACCOUNT", 
        "OPERATION",
        "PURCHASE_TYPE",
        "REGION",
        "USAGE_TYPE",
        "USAGE_TYPE_GROUP",
        "RECORD_TYPE",
        "RESOURCE_ID",
        "RIGHTSIZING_TYPE",
        "SAVINGS_PLANS_TYPE",
        "SCOPE",
        "DIMENSION",
        "PLATFORM",
        "TENANCY",
        "INSTANCE_TYPE",
        "LEGAL_ENTITY_NAME",
        "DEPLOYMENT_OPTION",
        "DATABASE_ENGINE",
        "CACHE_ENGINE",
        "INSTANCE_TYPE_FAMILY",
        "BILLING_ENTITY",
        "RESERVATION_ID",
        "SAVINGS_PLAN_ARN",
        "OPERATING_SYSTEM"
    ]
    
    return dimensions


@tool  
def get_safe_date_range(months_back: int = 1) -> Dict[str, str]:
    """
    Retorna um intervalo de datas seguro dentro dos limites do Cost Explorer.
    
    Args:
        months_back: Quantos meses para trás (máximo 14)
        
    Returns:
        Dicionário com start_date e end_date seguras
    """
    try:
        # Limitar a no máximo 13 meses para ter margem de segurança
        safe_months = min(months_back, 13)
        
        current_date = datetime.now()
        
        # Data de fim: hoje
        end_date = current_date.strftime('%Y-%m-%d')
        
        # Data de início: X meses atrás
        start_date = (current_date - timedelta(days=safe_months * 30)).strftime('%Y-%m-%d')
        
        result = {
            "start_date": start_date,
            "end_date": end_date,
            "months_analyzed": safe_months,
            "note": f"Período seguro de {safe_months} meses dentro dos limites do Cost Explorer"
        }
        
        print(f"GET SAFE DATE RANGE: {safe_months} meses -> {start_date} a {end_date}")
        return result
        
    except Exception as e:
        # Fallback para último mês
        current_date = datetime.now()
        end_date = current_date.strftime('%Y-%m-%d')
        start_date = (current_date - timedelta(days=30)).strftime('%Y-%m-%d')
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "months_analyzed": 1,
            "error": str(e),
            "note": "Fallback para último mês devido a erro"
        } 