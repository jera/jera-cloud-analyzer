"""
Módulo para análise e recomendações específicas de otimização de custos.
"""
from typing import Dict, List, Any, Optional
from decimal import Decimal

from clouds.aws.client import AWSClient
from clouds.aws.cost_explorer import CostExplorer
from clouds.aws.utils import AWSUtils, DecimalEncoder


class AWSOptimizer:
    """
    Gerador de recomendações específicas para otimização de custos na AWS.
    """
    
    def __init__(self, cost_explorer: Optional[CostExplorer] = None):
        """
        Inicializa o otimizador.
        
        Args:
            cost_explorer: Cliente Cost Explorer opcional. Se não fornecido, um novo será criado.
        """
        self.cost_explorer = cost_explorer or CostExplorer()
        self.aws_client = AWSClient()
        self.utils = AWSUtils()
        
    def get_ec2_optimization(self) -> List[Dict[str, Any]]:
        """
        Analisa e fornece recomendações específicas para EC2.
        
        Returns:
            Lista de recomendações para EC2
        """
        recommendations = []
        
        # Obter detalhes do uso de EC2
        ec2_details = self.cost_explorer.get_service_details('Amazon Elastic Compute Cloud - Compute')
        
        # Identificar instâncias On-Demand
        has_on_demand = False
        on_demand_types = set()
        
        for period in ec2_details.get('ResultsByTime', []):
            for group in period.get('Groups', []):
                usage_type = group.get('Keys', [''])[0].lower()
                cost = AWSUtils.extract_amount(group.get('Metrics', {}))
                
                if 'ondemand' in usage_type and AWSUtils.is_significant_amount(cost):
                    has_on_demand = True
                    # Extrair tipo de instância do usage_type
                    parts = usage_type.split(':')
                    if len(parts) >= 2:
                        instance_family = parts[1].split('-')[0]
                        on_demand_types.add(instance_family)
        
        # Recomendar Instâncias Reservadas se há instâncias On-Demand
        if has_on_demand:
            recommendations.append({
                'title': 'Migrar de instâncias On-Demand para Instâncias Reservadas',
                'description': (
                    f'Detectamos uso significativo de instâncias On-Demand '
                    f'(famílias: {", ".join(on_demand_types)}). Considere usar Instâncias Reservadas '
                    f'para workloads previsíveis e constantes.'
                ),
                'estimated_savings': 'Até 75% em comparação com preços On-Demand',
                'effort': 'Médio',
                'implementation': [
                    'Analise os padrões de uso das instâncias nos últimos 30-60 dias',
                    'Identifique instâncias que são executadas constantemente',
                    'Compre Instâncias Reservadas para essas cargas de trabalho',
                    'Para maior flexibilidade, considere Instâncias Reservadas Convertíveis'
                ]
            })
        
        # Recomendar Savings Plans
        recommendations.append({
            'title': 'Implementar Savings Plans para maior flexibilidade',
            'description': (
                'Savings Plans oferecem economia semelhante às Instâncias Reservadas, '
                'mas com maior flexibilidade para diferentes tipos de instância, '
                'famílias e até mesmo outros serviços como Fargate e Lambda.'
            ),
            'estimated_savings': 'Até 72% em comparação com preços On-Demand',
            'effort': 'Baixo',
            'implementation': [
                'Acesse o Cost Explorer e veja a recomendação de Savings Plans',
                'Escolha entre planos de Computação (maior flexibilidade) ou EC2 Instance (maior desconto)',
                'Selecione o compromisso por 1 ou 3 anos com base na sua previsão de uso',
                'Monitore regularmente a utilização dos seus Savings Plans'
            ]
        })
        
        return recommendations
    
    def get_ebs_optimization(self) -> List[Dict[str, Any]]:
        """
        Analisa e fornece recomendações específicas para volumes EBS.
        
        Returns:
            Lista de recomendações para EBS
        """
        # Utiliza o cliente boto3 diretamente para informações que o Cost Explorer não fornece
        ec2_client = self.aws_client.get_client('ec2')
        
        # Buscar volumes não anexados
        volumes = ec2_client.describe_volumes(
            Filters=[
                {
                    'Name': 'status',
                    'Values': ['available']  # Volumes não anexados
                }
            ]
        )
        
        recommendations = []
        
        # Recomendar remoção de volumes não utilizados
        if volumes.get('Volumes', []):
            unused_volume_count = len(volumes['Volumes'])
            total_size = sum(v.get('Size', 0) for v in volumes['Volumes'])
            
            recommendations.append({
                'title': f'Remover {unused_volume_count} volumes EBS não utilizados',
                'description': (
                    f'Encontramos {unused_volume_count} volumes EBS não anexados '
                    f'totalizando {total_size} GB. Estes volumes geram custos '
                    f'desnecessários e devem ser removidos ou anexados a instâncias.'
                ),
                'estimated_savings': f'Aproximadamente ${total_size * 0.10:.2f} por mês (estimativa)',
                'effort': 'Baixo',
                'implementation': [
                    'Verifique se os volumes não contêm dados importantes',
                    'Faça backup dos dados necessários',
                    'Exclua os volumes ou anexe-os a instâncias existentes'
                ]
            })
        
        # Recomendar verificação de tipos de volumes
        recommendations.append({
            'title': 'Otimizar tipos de volumes EBS',
            'description': (
                'Revise o tipo de cada volume EBS para garantir que esteja adequado à carga de trabalho. '
                'Use gp3 em vez de gp2 para melhor desempenho e custo.'
            ),
            'estimated_savings': 'Até 20% ao migrar de gp2 para gp3',
            'effort': 'Médio',
            'implementation': [
                'Identifique volumes gp2 em uso',
                'Crie snapshots dos volumes como backup',
                'Migre os volumes para o tipo gp3',
                'Ajuste as configurações de IOPS e throughput conforme necessário'
            ]
        })
        
        # Snapshots antigos e não utilizados
        recommendations.append({
            'title': 'Limpar snapshots EBS antigos',
            'description': (
                'Identifique e remova snapshots EBS antigos ou redundantes para reduzir '
                'custos de armazenamento. Implemente uma política de retenção para '
                'gerenciar snapshots automaticamente.'
            ),
            'estimated_savings': 'Varia de acordo com o número de snapshots',
            'effort': 'Baixo',
            'implementation': [
                'Liste todos os snapshots e identifique aqueles com mais de X meses',
                'Verifique se não há dependências nos snapshots antigos',
                'Implemente uma estratégia de snapshots com retenção automática',
                'Configure o AWS Data Lifecycle Manager para gerenciar snapshots'
            ]
        })
        
        return recommendations
    
    def get_s3_optimization(self) -> List[Dict[str, Any]]:
        """
        Analisa e fornece recomendações específicas para Amazon S3.
        
        Returns:
            Lista de recomendações para S3
        """
        recommendations = []
        
        # Recomendações gerais para S3
        recommendations.append({
            'title': 'Implementar políticas de ciclo de vida para objetos S3',
            'description': (
                'Configure regras de ciclo de vida para mover automaticamente objetos para '
                'classes de armazenamento mais econômicas com base na frequência de acesso.'
            ),
            'estimated_savings': 'Até 70% em custos de armazenamento',
            'effort': 'Médio',
            'implementation': [
                'Analise padrões de acesso aos seus objetos S3',
                'Configure regras de ciclo de vida por bucket',
                'Mova objetos acessados com pouca frequência para S3 Standard-IA após 30 dias',
                'Mova objetos raramente acessados para Glacier após 90 dias',
                'Configure expiração para objetos que não precisam ser mantidos permanentemente'
            ]
        })
        
        # Recomendação de S3 Intelligent-Tiering
        recommendations.append({
            'title': 'Utilizar S3 Intelligent-Tiering para objetos com padrões de acesso desconhecidos',
            'description': (
                'O S3 Intelligent-Tiering move automaticamente objetos entre camadas de acesso '
                'com base em padrões de uso, otimizando custos sem comprometer a performance.'
            ),
            'estimated_savings': 'Até 40% em custos de armazenamento',
            'effort': 'Baixo',
            'implementation': [
                'Identifique buckets com padrões de acesso variáveis ou imprevisíveis',
                'Configure o bucket para usar S3 Intelligent-Tiering como classe de armazenamento padrão',
                'Para objetos existentes, use um job de replicação por lote para migrar'
            ]
        })
        
        # Recomendação para S3 Analytics
        recommendations.append({
            'title': 'Usar S3 Analytics para otimização baseada em dados',
            'description': (
                'Habilite o S3 Analytics para receber recomendações automatizadas sobre quando '
                'migrar objetos para Standard-IA baseado em padrões reais de acesso.'
            ),
            'estimated_savings': 'Varia de acordo com o uso',
            'effort': 'Baixo',
            'implementation': [
                'Ative o S3 Analytics nos buckets mais utilizados',
                'Aguarde pelo menos 30 dias para coletar dados suficientes',
                'Analise as recomendações e implemente políticas de ciclo de vida apropriadas'
            ]
        })
        
        return recommendations
    
    def get_networking_optimization(self) -> List[Dict[str, Any]]:
        """
        Analisa e fornece recomendações específicas para otimização de rede.
        
        Returns:
            Lista de recomendações para networking
        """
        recommendations = []
        
        # Verificar IPs elásticos não utilizados
        ec2_client = self.aws_client.get_client('ec2')
        addresses = ec2_client.describe_addresses()
        
        unused_ips = [addr for addr in addresses.get('Addresses', []) 
                     if 'AssociationId' not in addr]
        
        if unused_ips:
            recommendations.append({
                'title': f'Liberar {len(unused_ips)} IPs elásticos não utilizados',
                'description': (
                    f'Encontramos {len(unused_ips)} IPs elásticos não associados a recursos. '
                    f'IPs elásticos não utilizados geram custos desnecessários.'
                ),
                'estimated_savings': f'Aproximadamente ${len(unused_ips) * 3.6:.2f} por mês',
                'effort': 'Baixo',
                'implementation': [
                    'Verifique se os IPs não são necessários para uso futuro imediato',
                    'Libere os IPs elásticos não utilizados',
                    'Use DNS em vez de IPs estáticos quando possível'
                ]
            })
        
        # Recomendação para NAT Gateway
        recommendations.append({
            'title': 'Otimizar uso de NAT Gateways',
            'description': (
                'NAT Gateways têm custo por hora mais taxa por GB transferido. Considere '
                'consolidar NAT Gateways em zonas de disponibilidade para reduzir custos.'
            ),
            'estimated_savings': 'Até $32 por mês por NAT Gateway eliminado',
            'effort': 'Médio',
            'implementation': [
                'Avalie se suas aplicações requerem alta disponibilidade em múltiplas AZs',
                'Para ambientes não críticos, considere usar um único NAT Gateway',
                'Use NAT Instances para ambientes de desenvolvimento/teste'
            ]
        })
        
        # Recomendação para otimizar transferência de dados
        recommendations.append({
            'title': 'Reduzir custos de transferência de dados',
            'description': (
                'A transferência de dados entre zonas de disponibilidade e para a internet '
                'gera custos significativos. Otimize o tráfego de rede para reduzir custos.'
            ),
            'estimated_savings': 'Varia de acordo com o volume de tráfego',
            'effort': 'Alto',
            'implementation': [
                'Use CloudFront para distribuir conteúdo e reduzir tráfego direto da origem',
                'Mantenha recursos relacionados na mesma zona de disponibilidade',
                'Use VPC Endpoints para serviços AWS em vez de tráfego pela internet',
                'Configure Cache para reduzir solicitações repetidas'
            ]
        })
        
        return recommendations
    
    def get_all_recommendations(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtém todas as recomendações de otimização disponíveis.
        
        Returns:
            Dicionário com todas as recomendações por categoria
        """
        return {
            'ec2': self.get_ec2_optimization(),
            'ebs': self.get_ebs_optimization(),
            's3': self.get_s3_optimization(),
            'networking': self.get_networking_optimization()
        } 