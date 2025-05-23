"""
Utilitários para processamento de dados da AWS.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from decimal import Decimal


class AWSUtils:
    """
    Classe utilitária com funções comuns para processamento de dados da AWS.
    """
    
    @staticmethod
    def format_currency(amount: Decimal, currency: str = 'USD') -> str:
        """
        Formata um valor como moeda.
        
        Args:
            amount: Valor a ser formatado
            currency: Código da moeda
            
        Returns:
            Valor formatado como string (ex: "$123.45")
        """
        if currency == 'USD':
            return f"${float(amount):.2f}"
        return f"{float(amount):.2f} {currency}"
    
    @staticmethod
    def percent_change(old_value: Decimal, new_value: Decimal) -> float:
        """
        Calcula a variação percentual entre dois valores.
        
        Args:
            old_value: Valor antigo/inicial
            new_value: Valor novo/final
            
        Returns:
            Percentual de variação
        """
        if old_value == 0:
            return float('inf') if new_value > 0 else 0.0
            
        return float((new_value - old_value) / old_value * 100)
    
    @staticmethod
    def get_default_time_period(months: int = 1) -> Dict[str, str]:
        """
        Retorna um período de tempo padrão.
        
        Args:
            months: Número de meses para o período
            
        Returns:
            Dicionário com datas de início e fim no formato 'YYYY-MM-DD'
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
        
        return {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
    
    @staticmethod
    def last_n_months(n: int = 6) -> List[Dict[str, str]]:
        """
        Gera uma lista com os últimos N meses.
        
        Args:
            n: Número de meses para retornar
            
        Returns:
            Lista de dicionários contendo início e fim de cada mês
        """
        months = []
        today = datetime.now()
        
        for i in range(n):
            # Calcular o mês atual menos i
            month = today.month - i
            year = today.year
            
            # Ajustar para meses anteriores ao atual
            while month <= 0:
                month += 12
                year -= 1
            
            # Primeiro dia do mês
            first_day = datetime(year, month, 1)
            
            # Último dia do mês
            if month == 12:
                last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)
            
            months.append({
                'name': first_day.strftime('%b %Y'),
                'start': first_day.strftime('%Y-%m-%d'),
                'end': last_day.strftime('%Y-%m-%d')
            })
            
        # Inverter para ordem cronológica
        months.reverse()
        return months
        
    @staticmethod
    def extract_amount(metrics: Dict[str, Any], metric_name: str = 'UnblendedCost') -> Decimal:
        """
        Extrai um valor numérico de métricas retornadas pela AWS.
        
        Args:
            metrics: Dicionário de métricas da AWS
            metric_name: Nome da métrica a extrair
            
        Returns:
            Valor decimal extraído
        """
        try:
            return Decimal(metrics.get(metric_name, {}).get('Amount', '0'))
        except:
            return Decimal('0')
            
    @staticmethod
    def is_significant_amount(amount: Decimal, threshold: Decimal = Decimal('1.0')) -> bool:
        """
        Verifica se um valor é significativo para análise.
        
        Args:
            amount: Valor a verificar
            threshold: Limite mínimo para considerar significativo
            
        Returns:
            True se o valor for significativo
        """
        return amount >= threshold


class DecimalEncoder(json.JSONEncoder):
    """
    Codificador JSON para tratar objetos Decimal.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj) 