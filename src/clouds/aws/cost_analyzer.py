"""
Módulo para análise de custos e recomendações de otimização.
"""
from typing import Dict, List, Any, Optional
import json
from decimal import Decimal
from datetime import datetime, timedelta

from src.clouds.aws.cost_explorer import CostExplorer


class CostDecimalEncoder(json.JSONEncoder):
    """
    Encoder JSON personalizado para lidar com objetos Decimal.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class CostAnalyzer:
    """
    Analisador de custos que processa dados do Cost Explorer e gera insights.
    """
    
    def __init__(self, cost_explorer: Optional[CostExplorer] = None):
        """
        Inicializa o analisador de custos.
        
        Args:
            cost_explorer: Cliente Cost Explorer opcional. Se não fornecido, um novo será criado.
        """
        self.cost_explorer = cost_explorer or CostExplorer()
        
    def get_top_services(self, limit: int = 5, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna os serviços mais caros no período.
        
        Args:
            limit: Número máximo de serviços a retornar
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Lista dos serviços mais caros, ordenada por custo (do maior para o menor)
        """
        result = self.cost_explorer.get_cost_by_service(start_date, end_date)
        
        if 'ResultsByTime' not in result or not result['ResultsByTime']:
            return []
            
        services = []
        
        # Somamos os custos dos serviços em todos os períodos retornados
        service_costs = {}
        
        for period in result['ResultsByTime']:
            for group in period.get('Groups', []):
                service_name = group.get('Keys', ['Desconhecido'])[0]
                cost = Decimal(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                unit = group.get('Metrics', {}).get('UnblendedCost', {}).get('Unit', 'USD')
                
                if service_name in service_costs:
                    service_costs[service_name]['cost'] += cost
                else:
                    service_costs[service_name] = {
                        'service': service_name,
                        'cost': cost,
                        'unit': unit
                    }
        
        # Ordenar e limitar a quantidade de serviços
        services = sorted(service_costs.values(), key=lambda x: x['cost'], reverse=True)[:limit]
        
        return json.loads(json.dumps(services, cls=CostDecimalEncoder))
    
    def get_cost_trends(self, months: int = 6) -> Dict[str, Any]:
        """
        Analisa tendências de custo nos últimos meses.
        
        Args:
            months: Número de meses a analisar
            
        Returns:
            Dados de tendência de custos, incluindo comparações mês a mês
        """
        # Definir datas para o período
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=30 * months)).strftime('%Y-%m-%d')
        
        # Garantir que temos pelo menos 1 dia entre start_date e end_date
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        if (end_dt - start_dt).days < 1:
            start_date = (end_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        
        result = self.cost_explorer.get_cost_by_service(
            start_date=start_date, 
            end_date=end_date,
            granularity='MONTHLY'
        )
        
        if 'ResultsByTime' not in result or not result['ResultsByTime']:
            return {'trends': [], 'total_change': 0, 'average_change': 0}
            
        # Calcular custos totais por mês
        monthly_costs = []
        for period in result['ResultsByTime']:
            total_cost = Decimal('0')
            for group in period.get('Groups', []):
                cost = Decimal(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                total_cost += cost
                
            monthly_costs.append({
                'period': period.get('TimePeriod', {}).get('Start', ''),
                'cost': total_cost
            })
        
        # Calcular mudanças percentuais
        trends = []
        for i in range(1, len(monthly_costs)):
            previous_cost = monthly_costs[i-1]['cost']
            current_cost = monthly_costs[i]['cost']
            
            if previous_cost > 0:
                percent_change = ((current_cost - previous_cost) / previous_cost) * 100
            else:
                percent_change = 0 if current_cost == 0 else 100
                
            trends.append({
                'period': monthly_costs[i]['period'],
                'cost': current_cost,
                'previous_cost': previous_cost,
                'percent_change': percent_change
            })
        
        # Calcular tendência geral
        total_change = 0
        if trends:
            first_month = monthly_costs[0]['cost']
            last_month = monthly_costs[-1]['cost']
            
            if first_month > 0:
                total_change = ((last_month - first_month) / first_month) * 100
            else:
                total_change = 0 if last_month == 0 else 100
        
        # Calcular média de mudança
        average_change = sum(t['percent_change'] for t in trends) / len(trends) if trends else 0
        
        return json.loads(json.dumps({
            'trends': trends,
            'total_change': total_change,
            'average_change': average_change
        }, cls=CostDecimalEncoder))
    
    def get_cost_by_tag_analysis(self, tag_key: str, start_date: Optional[str] = None, 
                                end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analisa custos agrupados por uma tag específica.
        
        Args:
            tag_key: Chave da tag a analisar
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Análise detalhada dos custos agrupados pela tag
        """
        result = self.cost_explorer.get_cost_by_tag(tag_key, start_date, end_date)
        
        if 'ResultsByTime' not in result or not result['ResultsByTime']:
            return {'tag_values': [], 'untagged_cost': 0, 'total_cost': 0}
            
        tag_costs = {}
        untagged_cost = Decimal('0')
        total_cost = Decimal('0')
        
        for period in result['ResultsByTime']:
            for group in period.get('Groups', []):
                tag_value = group.get('Keys', [''])[0]
                cost = Decimal(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                
                # Tratar recursos sem a tag especificada
                if tag_value == '' or tag_value.lower() == 'no tag':
                    untagged_cost += cost
                else:
                    if tag_value in tag_costs:
                        tag_costs[tag_value] += cost
                    else:
                        tag_costs[tag_value] = cost
                        
                total_cost += cost
                
        # Organizar resultados
        tag_values = [{
            'tag_value': tag_value,
            'cost': cost,
            'percentage': (cost / total_cost * 100) if total_cost > 0 else 0
        } for tag_value, cost in tag_costs.items()]
        
        # Ordenar por custo
        tag_values.sort(key=lambda x: x['cost'], reverse=True)
        
        return json.loads(json.dumps({
            'tag_values': tag_values,
            'untagged_cost': float(untagged_cost),
            'untagged_percentage': float(untagged_cost / total_cost * 100) if total_cost > 0 else 0,
            'total_cost': float(total_cost)
        }, cls=CostDecimalEncoder))
    
    def generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Gera recomendações de otimização de custos baseadas nos dados disponíveis.
        
        Returns:
            Lista de recomendações de otimização
        """
        recommendations = []
        
        # Obter os serviços mais caros
        top_services = self.get_top_services(limit=3)
        
        # Verificar EC2 e gerar recomendações
        ec2_service = next((s for s in top_services if 'EC2' in s['service']), None)
        if ec2_service:
            ec2_details = self.cost_explorer.get_service_details('Amazon Elastic Compute Cloud - Compute')
            
            # Verificar se há instâncias reservadas ou on-demand
            has_on_demand = False
            for period in ec2_details.get('ResultsByTime', []):
                for group in period.get('Groups', []):
                    usage_type = group.get('Keys', [''])[0].lower()
                    if 'ondemand' in usage_type:
                        has_on_demand = True
                        break
            
            if has_on_demand:
                recommendations.append({
                    'service': 'EC2',
                    'title': 'Considere usar instâncias reservadas',
                    'description': 'Você está usando instâncias on-demand que poderiam ser mais econômicas com reservas.',
                    'potential_savings': 'Até 75% de economia em instâncias reservadas por 3 anos',
                    'priority': 'Alta'
                })
                
            # Recomendar Savings Plans
            recommendations.append({
                'service': 'EC2/Lambda/Fargate',
                'title': 'Avalie o uso de Savings Plans',
                'description': 'Savings Plans oferecem preços mais baixos em troca de compromisso de uso por 1 ou 3 anos.',
                'potential_savings': 'Até 72% de economia em relação aos preços on-demand',
                'priority': 'Alta'
            })
        
        # Verificar S3 e gerar recomendações
        s3_service = next((s for s in top_services if 'S3' in s['service']), None)
        if s3_service:
            recommendations.append({
                'service': 'S3',
                'title': 'Otimize classes de armazenamento S3',
                'description': 'Mova dados acessados com pouca frequência para S3 Standard-IA ou Glacier.',
                'potential_savings': 'Até 90% de economia em dados raramente acessados',
                'priority': 'Média'
            })
        
        # Recomendação de limpeza de recursos não utilizados
        recommendations.append({
            'service': 'Todos',
            'title': 'Identifique e remova recursos não utilizados',
            'description': 'Procure por volumes EBS não anexados, IPs elásticos não utilizados e outros recursos ociosos.',
            'potential_savings': 'Varia de acordo com os recursos ociosos',
            'priority': 'Alta'
        })
        
        # Recomendação de melhor uso de tags
        recommendations.append({
            'service': 'Todos',
            'title': 'Implemente uma estratégia consistente de tags',
            'description': 'Tags consistentes ajudam a identificar custos por equipe, projeto ou ambiente.',
            'potential_savings': 'Melhora a alocação de custos e identificação de oportunidades',
            'priority': 'Média'
        })
        
        return recommendations
        
    def get_cost_anomalies(self, threshold_percent: float = 20.0) -> List[Dict[str, Any]]:
        """
        Detecta anomalias nos custos, como aumentos súbitos acima de um limiar.
        
        Args:
            threshold_percent: Percentual de variação que caracteriza uma anomalia
            
        Returns:
            Lista de anomalias detectadas
        """
        # Obter tendências dos últimos meses
        trends_data = self.get_cost_trends(months=3)
        
        anomalies = []
        for trend in trends_data.get('trends', []):
            if trend['percent_change'] > threshold_percent:
                anomalies.append({
                    'period': trend['period'],
                    'percent_change': trend['percent_change'],
                    'previous_cost': trend['previous_cost'],
                    'current_cost': trend['cost'],
                    'severity': 'Alta' if trend['percent_change'] > 50 else 'Média'
                })
                
        # Se encontrou anomalias, buscar os serviços que mais contribuíram
        if anomalies:
            for anomaly in anomalies:
                # Obter detalhes dos serviços no período da anomalia
                period_start = anomaly['period']
                # Calcular a data final como o último dia do mês
                start_date = datetime.strptime(period_start, '%Y-%m-%d')
                # Determinar o último dia do mês
                if start_date.month == 12:
                    end_date = datetime(start_date.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(start_date.year, start_date.month + 1, 1) - timedelta(days=1)
                
                # Converter para string no formato YYYY-MM-DD
                period_end = end_date.strftime('%Y-%m-%d')
                
                services = self.get_top_services(limit=3, start_date=period_start, end_date=period_end)
                anomaly['top_contributors'] = services
                
        return json.loads(json.dumps(anomalies, cls=CostDecimalEncoder))
    
    def analyze_all_tags_with_services(self, start_date: Optional[str] = None, 
                                     end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analisa todas as tags disponíveis, levantando custos e serviços associados a cada tag.
        
        Args:
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Análise detalhada dos custos por tag e serviços associados
        """
        # Obter todas as tags disponíveis
        tags_result = self.cost_explorer.get_tags()
        tag_keys = tags_result.get('Tags', [])
        
        if not tag_keys:
            return {"message": "Nenhuma tag encontrada na conta AWS", "tags": []}
        
        result = {"tags": []}
        
        # Para cada tag, obter análise de custos e serviços associados
        for tag_key in tag_keys:
            # Análise de custos da tag
            tag_analysis = self.get_cost_by_tag_analysis(tag_key, start_date, end_date)
            
            tag_data = {
                "tag_key": tag_key,
                "total_cost": tag_analysis.get("total_cost", 0),
                "untagged_cost": tag_analysis.get("untagged_cost", 0),
                "untagged_percentage": tag_analysis.get("untagged_percentage", 0),
                "values": []
            }
            
            # Para cada valor da tag, obter os serviços associados
            for tag_value_data in tag_analysis.get("tag_values", []):
                tag_value = tag_value_data.get("tag_value", "")
                
                # Consultar serviços para esta tag:valor específica
                services = self._get_services_for_tag_value(tag_key, tag_value, start_date, end_date)
                
                tag_value_data["services"] = services
                tag_data["values"].append(tag_value_data)
            
            result["tags"].append(tag_data)
        
        return result
    
    def _get_services_for_tag_value(self, tag_key: str, tag_value: str, 
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtém serviços associados a um valor específico de tag.
        
        Args:
            tag_key: Chave da tag
            tag_value: Valor da tag
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Lista de serviços associados à tag com seus respectivos custos
        """
        # Obter datas normalizadas
        start, end = self.cost_explorer._normalize_dates(start_date, end_date)
        
        # Consultar custo por serviço filtrado pela tag
        try:
            result = self.cost_explorer.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start,
                    'End': end
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                Filter={
                    'Tags': {
                        'Key': tag_key,
                        'Values': [tag_value]
                    }
                }
            )
        except Exception as e:
            # Em caso de erro, retornar lista vazia
            print(f"Erro ao consultar serviços para tag {tag_key}:{tag_value}: {str(e)}")
            return []
            
        # Processar resultados
        services = []
        service_costs = {}
        
        for period in result.get('ResultsByTime', []):
            for group in period.get('Groups', []):
                service_name = group.get('Keys', ['Desconhecido'])[0]
                cost = Decimal(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0'))
                unit = group.get('Metrics', {}).get('UnblendedCost', {}).get('Unit', 'USD')
                
                if service_name in service_costs:
                    service_costs[service_name]['cost'] += cost
                else:
                    service_costs[service_name] = {
                        'service': service_name,
                        'cost': cost,
                        'unit': unit
                    }
        
        # Ordenar por custo
        services = sorted(service_costs.values(), key=lambda x: x['cost'], reverse=True)
        
        return json.loads(json.dumps(services, cls=CostDecimalEncoder)) 