"""
Módulo para interagir com AWS Cost Explorer e obter dados de custos.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.clouds.aws.client import AWSClient

# Configurar logger específico para dados brutos da AWS
aws_data_logger = logging.getLogger('aws_raw_data')
aws_data_logger.setLevel(logging.INFO)

# Handler para arquivo de log
if not aws_data_logger.handlers:
    handler = logging.FileHandler('aws_raw_data.log', encoding='utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    aws_data_logger.addHandler(handler)
    aws_data_logger.propagate = False

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
        
    def _log_raw_aws_data(self, operation: str, parameters: Dict[str, Any], raw_response: Dict[str, Any]) -> None:
        """
        Loga os dados brutos retornados pela AWS para auditoria.
        
        Args:
            operation: Nome da operação AWS executada
            parameters: Parâmetros enviados para a AWS
            raw_response: Resposta bruta da AWS
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'parameters': parameters,
            'raw_response': raw_response,
            'account_id': getattr(self.aws_client, 'account_id', 'unknown'),
            'region': getattr(self.aws_client, 'region', 'unknown')
        }
        aws_data_logger.info(f"RAW_DATA: {json.dumps(log_entry, default=str, ensure_ascii=False)}")
        
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
        
        parameters = {
            'TimePeriod': {
                'Start': start,
                'End': end
            },
            'Granularity': granularity,
            'Metrics': ['UnblendedCost'],
            'GroupBy': [
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        }
        
        raw_response = self.client.get_cost_and_usage(**parameters)
        
        # Log dos dados brutos para auditoria
        self._log_raw_aws_data('get_cost_and_usage_by_service', parameters, raw_response)
        
        return raw_response
    
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
        
        parameters = {
            'TimePeriod': {
                'Start': start,
                'End': end
            },
            'Granularity': granularity,
            'Metrics': ['UnblendedCost'],
            'GroupBy': [
                {
                    'Type': 'TAG',
                    'Key': tag_key
                }
            ]
        }
        
        raw_response = self.client.get_cost_and_usage(**parameters)
        
        # Log dos dados brutos para auditoria
        self._log_raw_aws_data('get_cost_and_usage_by_tag', parameters, raw_response)
        
        return raw_response
    
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
        
        parameters = {
            'TimePeriod': {
                'Start': start,
                'End': end
            },
            'Granularity': granularity,
            'Metrics': ['UnblendedCost'],
            'Filter': {
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [service]
                }
            },
            'GroupBy': [
                {
                    'Type': 'DIMENSION',
                    'Key': 'USAGE_TYPE'
                }
            ]
        }
        
        raw_response = self.client.get_cost_and_usage(**parameters)
        
        # Log dos dados brutos para auditoria
        self._log_raw_aws_data('get_cost_and_usage_service_details', parameters, raw_response)
        
        return raw_response
    
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
        
        parameters = {
            'TimePeriod': {
                'Start': start,
                'End': end
            },
            'Granularity': granularity,
            'Metric': metric
        }
        
        raw_response = self.client.get_cost_forecast(**parameters)
        
        # Log dos dados brutos para auditoria
        self._log_raw_aws_data('get_cost_forecast', parameters, raw_response)
        
        return raw_response
    
    def get_tags(self) -> Dict[str, Any]:
        """
        Obtém todas as chaves de tags disponíveis na conta.
        
        Returns:
            Lista de chaves de tags ativas
        """
        parameters = {
            'SearchString': '',
            'TimePeriod': {
                'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            }
        }
        
        raw_response = self.client.get_tags(**parameters)
        
        # Log dos dados brutos para auditoria
        self._log_raw_aws_data('get_tags', parameters, raw_response)
        
        return raw_response
    
    def get_dimension_values(self, dimension: str) -> Dict[str, Any]:
        """
        Obtém valores válidos para uma dimensão específica.
        
        Args:
            dimension: Dimensão desejada ('SERVICE', 'USAGE_TYPE', 'INSTANCE_TYPE', etc.)
            
        Returns:
            Valores da dimensão solicitada
        """
        parameters = {
            'SearchString': '',
            'TimePeriod': {
                'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            },
            'Dimension': dimension
        }
        
        raw_response = self.client.get_dimension_values(**parameters)
        
        # Log dos dados brutos para auditoria
        self._log_raw_aws_data('get_dimension_values', parameters, raw_response)
        
        return raw_response
    
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
        # Usar o método existente get_cost_by_service (já faz log internamente)
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
        
        top_services = services_costs[:limit]
        
        # Log dos dados processados para comparação
        processed_data = {
            'operation': 'get_top_services_processed',
            'input_periods': len(cost_data.get('ResultsByTime', [])),
            'total_services_found': len(services_costs),
            'top_services_returned': len(top_services),
            'top_services_summary': [
                {
                    'service': service['service_name'],
                    'total_cost': service['total_cost'],
                    'currency': service['currency']
                }
                for service in top_services
            ]
        }
        
        aws_data_logger.info(f"PROCESSED_DATA: {json.dumps(processed_data, default=str, ensure_ascii=False)}")
        
        return top_services
    
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