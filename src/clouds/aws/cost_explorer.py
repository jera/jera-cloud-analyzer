"""
Módulo para interagir com AWS Cost Explorer e obter dados de custos.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.clouds.aws.client import AWSClient


class CostExplorer:
    """
    Cliente para obtenção de dados de custo da AWS usando o Cost Explorer.
    """
    
    def __init__(self, aws_client: Optional[AWSClient] = None):
        """
        Inicializa o cliente Cost Explorer.
        
        Args:
            aws_client: Cliente AWS opcional. Se não fornecido, um novo será criado.
        """
        self.aws_client = aws_client or AWSClient()
        self.client = self.aws_client.get_client('ce')
        
    def get_cost_by_service(self, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None,
                           granularity: str = 'MONTHLY') -> Dict[str, Any]:
        """
        Obtém custos agrupados por serviço da AWS.
        
        Args:
            start_date: Data inicial no formato YYYY-MM-DD (padrão: 30 dias atrás)
            end_date: Data final no formato YYYY-MM-DD (padrão: hoje)
            granularity: Granularidade dos resultados ('DAILY'|'MONTHLY'|'HOURLY')
            
        Returns:
            Dados de custo agrupados por serviço
        """
        start, end = self._normalize_dates(start_date, end_date)
        
        return self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start,
                'End': end
            },
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
    
    def get_cost_by_tag(self, tag_key: str, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None, 
                        granularity: str = 'MONTHLY') -> Dict[str, Any]:
        """
        Obtém custos agrupados por uma tag específica.
        
        Args:
            tag_key: Chave da tag para agrupar resultados
            start_date: Data inicial no formato YYYY-MM-DD (padrão: 30 dias atrás)
            end_date: Data final no formato YYYY-MM-DD (padrão: hoje)
            granularity: Granularidade dos resultados ('DAILY'|'MONTHLY'|'HOURLY')
            
        Returns:
            Dados de custo agrupados pela tag especificada
        """
        start, end = self._normalize_dates(start_date, end_date)
        
        return self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start,
                'End': end
            },
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'TAG',
                    'Key': tag_key
                }
            ]
        )
    
    def get_service_details(self, service: str, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None,
                           granularity: str = 'MONTHLY') -> Dict[str, Any]:
        """
        Obtém detalhes de custos de um serviço específico, agrupados por operação/uso.
        
        Args:
            service: Nome do serviço AWS (ex: 'Amazon EC2', 'Amazon S3')
            start_date: Data inicial no formato YYYY-MM-DD (padrão: 30 dias atrás)
            end_date: Data final no formato YYYY-MM-DD (padrão: hoje)
            granularity: Granularidade dos resultados ('DAILY'|'MONTHLY'|'HOURLY')
            
        Returns:
            Detalhes de custo do serviço especificado
        """
        start, end = self._normalize_dates(start_date, end_date)
        
        return self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start,
                'End': end
            },
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [service]
                }
            },
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'USAGE_TYPE'
                }
            ]
        )
    
    def get_cost_forecast(self, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None,
                         granularity: str = 'MONTHLY',
                         metric: str = 'UNBLENDED_COST') -> Dict[str, Any]:
        """
        Obtém uma previsão de custos para o período especificado.
        
        Args:
            start_date: Data inicial no formato YYYY-MM-DD (padrão: hoje)
            end_date: Data final no formato YYYY-MM-DD (padrão: 30 dias a partir de hoje)
            granularity: Granularidade dos resultados ('DAILY'|'MONTHLY')
            metric: Métrica utilizada ('UNBLENDED_COST'|'BLENDED_COST'|'AMORTIZED_COST')
            
        Returns:
            Previsão de custos futuros
        """
        # Para previsão, o padrão é hoje até 30 dias no futuro
        today = datetime.now().strftime('%Y-%m-%d')
        future = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        start = start_date or today
        end = end_date or future
        
        return self.client.get_cost_forecast(
            TimePeriod={
                'Start': start,
                'End': end
            },
            Granularity=granularity,
            Metric=metric
        )
    
    def get_tags(self) -> Dict[str, Any]:
        """
        Obtém todas as chaves de tags disponíveis na conta.
        
        Returns:
            Lista de chaves de tags ativas
        """
        return self.client.get_tags(
            SearchString='',
            TimePeriod={
                'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            }
        )
    
    def get_dimension_values(self, dimension: str) -> Dict[str, Any]:
        """
        Obtém valores válidos para uma dimensão específica.
        
        Args:
            dimension: Dimensão desejada ('SERVICE', 'USAGE_TYPE', 'INSTANCE_TYPE', etc.)
            
        Returns:
            Valores da dimensão solicitada
        """
        return self.client.get_dimension_values(
            SearchString='',
            TimePeriod={
                'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            },
            Dimension=dimension
        )
    
    def get_top_services(self, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None, 
                        limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém os top serviços mais caros da AWS ordenados por custo.
        
        Args:
            start_date: Data inicial no formato YYYY-MM-DD (padrão: 30 dias atrás)
            end_date: Data final no formato YYYY-MM-DD (padrão: hoje)
            limit: Número máximo de serviços a retornar (padrão: 5)
            
        Returns:
            Lista dos serviços mais caros ordenados por custo descendente
        """
        # Usar o método existente get_cost_by_service
        cost_data = self.get_cost_by_service(start_date, end_date)
        
        # Processar os dados para extrair top serviços
        services_costs = []
        
        for period in cost_data.get('ResultsByTime', []):
            period_start = period.get('TimePeriod', {}).get('Start')
            
            for group in period.get('Groups', []):
                service_name = group.get('Keys', ['Unknown'])[0]
                cost_amount = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                cost_unit = group.get('Metrics', {}).get('UnblendedCost', {}).get('Unit', 'USD')
                
                # Procurar se já existe este serviço na lista
                existing_service = next((s for s in services_costs if s['service_name'] == service_name), None)
                
                if existing_service:
                    existing_service['total_cost'] += cost_amount
                    existing_service['periods'].append({
                        'period_start': period_start,
                        'cost': cost_amount
                    })
                else:
                    services_costs.append({
                        'service_name': service_name,
                        'total_cost': cost_amount,
                        'currency': cost_unit,
                        'periods': [{
                            'period_start': period_start,
                            'cost': cost_amount
                        }]
                    })
        
        # Ordenar por custo total (descendente) e limitar
        services_costs.sort(key=lambda x: x['total_cost'], reverse=True)
        
        return services_costs[:limit]
    
    def _normalize_dates(self, start_date: Optional[str], 
                        end_date: Optional[str]) -> tuple:
        """
        Normaliza datas de entrada, aplicando valores padrão se necessário.
        
        Args:
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Tupla (start_date, end_date) normalizada
        """
        # Obter data atual
        today = datetime.now()
        
        # Padrão: últimos 30 dias
        if not end_date:
            # A data final é hoje
            end_date = today.strftime('%Y-%m-%d')
            
        if not start_date:
            # A data inicial é 30 dias atrás
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            
        # Converter strings para objetos datetime para comparação
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Garantir que a data inicial seja anterior à final
        if start_dt >= end_dt:
            # Se a data inicial é maior ou igual à data final, definir a data inicial para 1 dia antes da final
            start_dt = end_dt - timedelta(days=1)
            start_date = start_dt.strftime('%Y-%m-%d')
        
        return start_date, end_date 