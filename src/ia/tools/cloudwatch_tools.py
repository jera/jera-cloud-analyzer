"""
Ferramentas para monitoramento CloudWatch de instâncias EC2.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from statistics import mean, median

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from haystack.tools import tool
from src.clouds.aws.cost_explorer import CostExplorer


class JsonEncoder(json.JSONEncoder):
    """Encoder JSON personalizado para lidar com tipos especiais como Decimal e datetime."""
    def default(self, obj):
        from decimal import Decimal
        from datetime import datetime, date
        
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


@tool
def get_instance_performance_metrics(instance_id: str, hours: int = 24, metrics: Optional[str] = None) -> str:
    """
    Obtém métricas de performance de uma instância EC2 específica via CloudWatch.
    
    Args:
        instance_id: ID da instância EC2 (ex: 'i-1234567890abcdef0')
        hours: Número de horas para análise (padrão: 24)
        metrics: Métricas específicas separadas por vírgula (ex: 'CPUUtilization,NetworkIn,NetworkOut')
                Se não especificado, busca todas as métricas principais
        
    Returns:
        JSON com métricas de performance da instância
        
    Métricas disponíveis:
    - CPUUtilization: Utilização de CPU (%)
    - NetworkIn: Tráfego de rede de entrada (bytes)
    - NetworkOut: Tráfego de rede de saída (bytes)
    - NetworkPacketsIn: Pacotes de rede de entrada
    - NetworkPacketsOut: Pacotes de rede de saída
    - DiskReadOps: Operações de leitura do disco
    - DiskWriteOps: Operações de escrita do disco
    - DiskReadBytes: Bytes lidos do disco
    - DiskWriteBytes: Bytes escritos no disco
    - StatusCheckFailed: Falhas de health check
    """
    print(f"OBTENDO MÉTRICAS DE PERFORMANCE - Instância: {instance_id}, Período: {hours}h")
    
    try:
        cost_explorer = CostExplorer()
        session = cost_explorer.aws_client.session
        cloudwatch = session.client('cloudwatch')
        
        # Definir período de análise
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Métricas padrão se não especificadas
        if metrics:
            metrics_list = [m.strip() for m in metrics.split(',')]
        else:
            metrics_list = [
                'CPUUtilization',
                'NetworkIn', 
                'NetworkOut',
                'NetworkPacketsIn',
                'NetworkPacketsOut',
                'DiskReadOps',
                'DiskWriteOps',
                'DiskReadBytes',
                'DiskWriteBytes',
                'StatusCheckFailed'
            ]
        
        performance_data = {
            "instance_id": instance_id,
            "analysis_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            },
            "metrics": {},
            "summary": {},
            "alerts": []
        }
        
        # Buscar cada métrica
        for metric_name in metrics_list:
            try:
                print(f"Buscando métrica: {metric_name}")
                
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName=metric_name,
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hora
                    Statistics=['Average', 'Maximum', 'Minimum']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    # Ordenar por timestamp
                    datapoints.sort(key=lambda x: x['Timestamp'])
                    
                    # Calcular estatísticas
                    averages = [dp['Average'] for dp in datapoints]
                    maximums = [dp['Maximum'] for dp in datapoints]
                    minimums = [dp['Minimum'] for dp in datapoints]
                    
                    metric_data = {
                        "unit": datapoints[0].get('Unit', ''),
                        "data_points": len(datapoints),
                        "time_series": [
                            {
                                "timestamp": dp['Timestamp'].isoformat(),
                                "average": dp['Average'],
                                "maximum": dp['Maximum'], 
                                "minimum": dp['Minimum']
                            } for dp in datapoints
                        ],
                        "statistics": {
                            "overall_average": mean(averages),
                            "overall_maximum": max(maximums),
                            "overall_minimum": min(minimums),
                            "median": median(averages)
                        }
                    }
                    
                    performance_data["metrics"][metric_name] = metric_data
                    
                    # Gerar alertas baseados em thresholds
                    if metric_name == 'CPUUtilization':
                        avg_cpu = mean(averages)
                        max_cpu = max(maximums)
                        
                        if avg_cpu > 80:
                            performance_data["alerts"].append({
                                "severity": "HIGH",
                                "metric": metric_name,
                                "message": f"CPU média alta: {avg_cpu:.1f}%",
                                "recommendation": "Considere upgrade do tipo de instância ou otimização de código"
                            })
                        elif avg_cpu < 10:
                            performance_data["alerts"].append({
                                "severity": "LOW",
                                "metric": metric_name,
                                "message": f"CPU subutilizada: {avg_cpu:.1f}%",
                                "recommendation": "Considere reduzir o tipo de instância para economizar custos"
                            })
                    
                    elif metric_name in ['NetworkIn', 'NetworkOut']:
                        # Converter bytes para GB para análise
                        total_traffic_gb = sum(averages) / (1024**3)
                        avg_traffic_mbps = mean(averages) * 8 / (1024**2)  # Convert to Mbps
                        
                        if avg_traffic_mbps > 100:  # > 100 Mbps
                            performance_data["alerts"].append({
                                "severity": "MEDIUM",
                                "metric": metric_name,
                                "message": f"Tráfego de rede alto: {avg_traffic_mbps:.1f} Mbps",
                                "recommendation": "Monitore custos de transferência de dados"
                            })
                    
                else:
                    performance_data["metrics"][metric_name] = {
                        "status": "no_data",
                        "message": f"Nenhum dado encontrado para {metric_name} no período especificado"
                    }
                    
            except Exception as e:
                print(f"Erro ao buscar métrica {metric_name}: {e}")
                performance_data["metrics"][metric_name] = {
                    "error": str(e)
                }
        
        # Gerar resumo geral
        cpu_data = performance_data["metrics"].get("CPUUtilization", {})
        network_in_data = performance_data["metrics"].get("NetworkIn", {})
        network_out_data = performance_data["metrics"].get("NetworkOut", {})
        
        if cpu_data.get("statistics"):
            performance_data["summary"]["cpu_utilization"] = {
                "average_percent": round(cpu_data["statistics"]["overall_average"], 2),
                "peak_percent": round(cpu_data["statistics"]["overall_maximum"], 2),
                "assessment": _assess_cpu_usage(cpu_data["statistics"]["overall_average"])
            }
        
        if network_in_data.get("statistics") and network_out_data.get("statistics"):
            total_in_gb = sum([dp["average"] for dp in network_in_data.get("time_series", [])]) / (1024**3)
            total_out_gb = sum([dp["average"] for dp in network_out_data.get("time_series", [])]) / (1024**3)
            
            performance_data["summary"]["network_usage"] = {
                "total_inbound_gb": round(total_in_gb, 3),
                "total_outbound_gb": round(total_out_gb, 3),
                "total_traffic_gb": round(total_in_gb + total_out_gb, 3),
                "assessment": _assess_network_usage(total_in_gb + total_out_gb)
            }
        
        # Adicionar recomendações gerais
        performance_data["recommendations"] = _generate_performance_recommendations(performance_data)
        
        print(f"Métricas coletadas com sucesso para {instance_id}")
        return json.dumps(performance_data, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erro ao obter métricas de performance: {e}")
        print(f"Traceback:\n{tb}")
        
        return json.dumps({
            "error": f"Erro ao obter métricas para instância {instance_id}",
            "details": str(e),
            "traceback": tb,
            "suggestion": "Verifique se a instância existe e se você tem permissões CloudWatch"
        }, ensure_ascii=False, indent=2)


@tool
def analyze_ec2_fleet_performance(tag_key: Optional[str] = None, tag_value: Optional[str] = None, 
                                hours: int = 24, max_instances: int = 10) -> str:
    """
    Analisa performance de múltiplas instâncias EC2 (fleet analysis).
    
    Args:
        tag_key: Chave da tag para filtrar instâncias (opcional)
        tag_value: Valor da tag para filtrar instâncias (opcional)
        hours: Número de horas para análise (padrão: 24)
        max_instances: Máximo de instâncias a analisar (padrão: 10)
        
    Returns:
        JSON com análise comparativa de performance da frota
    """
    print(f"ANALISANDO PERFORMANCE DA FROTA - Tag: {tag_key}={tag_value}, Período: {hours}h")
    
    try:
        cost_explorer = CostExplorer()
        session = cost_explorer.aws_client.session
        ec2_client = session.client('ec2')
        cloudwatch = session.client('cloudwatch')
        
        # Buscar instâncias baseado nos filtros
        filters = [
            {
                'Name': 'instance-state-name',
                'Values': ['running']  # Apenas instâncias em execução
            }
        ]
        
        if tag_key and tag_value:
            filters.append({
                'Name': f'tag:{tag_key}',
                'Values': [tag_value]
            })
        elif tag_key:
            filters.append({
                'Name': f'tag-key',
                'Values': [tag_key]
            })
        
        instances_response = ec2_client.describe_instances(Filters=filters)
        
        # Extrair informações das instâncias
        instances = []
        for reservation in instances_response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                if len(instances) >= max_instances:
                    break
                instances.append({
                    'instance_id': instance.get('InstanceId'),
                    'instance_type': instance.get('InstanceType'),
                    'availability_zone': instance.get('Placement', {}).get('AvailabilityZone'),
                    'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                })
        
        if not instances:
            return json.dumps({
                "message": "Nenhuma instância encontrada com os filtros especificados",
                "filters_applied": {
                    "tag_key": tag_key,
                    "tag_value": tag_value,
                    "state": "running"
                }
            }, ensure_ascii=False, indent=2)
        
        # Definir período de análise
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        fleet_analysis = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "analysis_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            },
            "fleet_summary": {
                "total_instances_analyzed": len(instances),
                "instance_types": list(set(i['instance_type'] for i in instances)),
                "availability_zones": list(set(i['availability_zone'] for i in instances))
            },
            "instances_performance": [],
            "fleet_insights": {},
            "recommendations": []
        }
        
        # Métricas principais para análise de frota
        key_metrics = ['CPUUtilization', 'NetworkIn', 'NetworkOut']
        
        # Coletar dados de cada instância
        for instance in instances:
            instance_id = instance['instance_id']
            print(f"Analisando instância: {instance_id}")
            
            instance_metrics = {
                "instance_id": instance_id,
                "instance_type": instance['instance_type'],
                "availability_zone": instance['availability_zone'],
                "metrics": {}
            }
            
            for metric_name in key_metrics:
                try:
                    response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName=metric_name,
                        Dimensions=[
                            {
                                'Name': 'InstanceId',
                                'Value': instance_id
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,  # 1 hora
                        Statistics=['Average']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    if datapoints:
                        averages = [dp['Average'] for dp in datapoints]
                        instance_metrics["metrics"][metric_name] = {
                            "average": mean(averages),
                            "maximum": max(averages),
                            "minimum": min(averages),
                            "data_points": len(datapoints)
                        }
                    else:
                        instance_metrics["metrics"][metric_name] = None
                        
                except Exception as e:
                    print(f"Erro ao buscar {metric_name} para {instance_id}: {e}")
                    instance_metrics["metrics"][metric_name] = {"error": str(e)}
            
            fleet_analysis["instances_performance"].append(instance_metrics)
        
        # Gerar insights da frota
        fleet_insights = _generate_fleet_insights(fleet_analysis["instances_performance"])
        fleet_analysis["fleet_insights"] = fleet_insights
        
        # Gerar recomendações
        fleet_analysis["recommendations"] = _generate_fleet_recommendations(fleet_insights)
        
        print(f"Análise da frota concluída: {len(instances)} instâncias")
        return json.dumps(fleet_analysis, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erro na análise da frota: {e}")
        print(f"Traceback:\n{tb}")
        
        return json.dumps({
            "error": f"Erro na análise de performance da frota",
            "details": str(e),
            "traceback": tb,
            "suggestion": "Verifique permissões EC2 e CloudWatch"
        }, ensure_ascii=False, indent=2)


@tool
def get_network_traffic_analysis(instance_id: str, days: int = 7) -> str:
    """
    Análise específica de tráfego de rede de uma instância EC2.
    
    Args:
        instance_id: ID da instância EC2
        days: Número de dias para análise (padrão: 7)
        
    Returns:
        JSON com análise detalhada de tráfego de rede
    """
    print(f"ANALISANDO TRÁFEGO DE REDE - Instância: {instance_id}, Período: {days} dias")
    
    try:
        cost_explorer = CostExplorer()
        session = cost_explorer.aws_client.session
        cloudwatch = session.client('cloudwatch')
        
        # Definir período de análise
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        network_analysis = {
            "instance_id": instance_id,
            "analysis_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days": days
            },
            "traffic_metrics": {},
            "bandwidth_analysis": {},
            "cost_implications": {},
            "recommendations": []
        }
        
        # Métricas de rede para análise
        network_metrics = {
            'NetworkIn': 'Tráfego de entrada',
            'NetworkOut': 'Tráfego de saída', 
            'NetworkPacketsIn': 'Pacotes de entrada',
            'NetworkPacketsOut': 'Pacotes de saída'
        }
        
        for metric_name, description in network_metrics.items():
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName=metric_name,
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hora
                    Statistics=['Sum', 'Average', 'Maximum']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    # Ordenar por timestamp
                    datapoints.sort(key=lambda x: x['Timestamp'])
                    
                    sums = [dp['Sum'] for dp in datapoints]
                    averages = [dp['Average'] for dp in datapoints]
                    maximums = [dp['Maximum'] for dp in datapoints]
                    
                    # Calcular estatísticas de tráfego
                    total_transfer = sum(sums)
                    
                    metric_data = {
                        "description": description,
                        "unit": datapoints[0].get('Unit', ''),
                        "total_transfer": total_transfer,
                        "average_hourly": mean(sums),
                        "peak_hourly": max(sums),
                        "average_rate": mean(averages),
                        "peak_rate": max(maximums),
                        "data_points": len(datapoints)
                    }
                    
                    # Converter para unidades mais legíveis se for bytes
                    if 'Bytes' in metric_data["unit"]:
                        metric_data["total_transfer_gb"] = total_transfer / (1024**3)
                        metric_data["average_hourly_gb"] = mean(sums) / (1024**3)
                        metric_data["peak_hourly_gb"] = max(sums) / (1024**3)
                        metric_data["average_rate_mbps"] = mean(averages) * 8 / (1024**2)
                        metric_data["peak_rate_mbps"] = max(maximums) * 8 / (1024**2)
                    
                    network_analysis["traffic_metrics"][metric_name] = metric_data
                    
                else:
                    network_analysis["traffic_metrics"][metric_name] = {
                        "status": "no_data",
                        "message": f"Nenhum dado encontrado para {metric_name}"
                    }
                    
            except Exception as e:
                print(f"Erro ao buscar {metric_name}: {e}")
                network_analysis["traffic_metrics"][metric_name] = {"error": str(e)}
        
        # Análise de bandwidth
        network_in = network_analysis["traffic_metrics"].get("NetworkIn", {})
        network_out = network_analysis["traffic_metrics"].get("NetworkOut", {})
        
        if network_in.get("total_transfer_gb") is not None and network_out.get("total_transfer_gb") is not None:
            total_traffic_gb = network_in["total_transfer_gb"] + network_out["total_transfer_gb"]
            
            network_analysis["bandwidth_analysis"] = {
                "total_inbound_gb": round(network_in["total_transfer_gb"], 3),
                "total_outbound_gb": round(network_out["total_transfer_gb"], 3),
                "total_traffic_gb": round(total_traffic_gb, 3),
                "traffic_ratio": round(network_out["total_transfer_gb"] / network_in["total_transfer_gb"], 2) if network_in["total_transfer_gb"] > 0 else 0,
                "daily_average_gb": round(total_traffic_gb / days, 3),
                "peak_inbound_mbps": round(network_in.get("peak_rate_mbps", 0), 2),
                "peak_outbound_mbps": round(network_out.get("peak_rate_mbps", 0), 2)
            }
            
            # Análise de implicações de custo
            network_analysis["cost_implications"] = _calculate_network_costs(network_analysis["bandwidth_analysis"])
        
        # Gerar recomendações
        network_analysis["recommendations"] = _generate_network_recommendations(network_analysis)
        
        print(f"Análise de tráfego concluída para {instance_id}")
        return json.dumps(network_analysis, cls=JsonEncoder, ensure_ascii=False, indent=2)
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Erro na análise de tráfego: {e}")
        print(f"Traceback:\n{tb}")
        
        return json.dumps({
            "error": f"Erro na análise de tráfego para instância {instance_id}",
            "details": str(e),
            "traceback": tb,
            "suggestion": "Verifique se a instância existe e permissões CloudWatch"
        }, ensure_ascii=False, indent=2)


def _assess_cpu_usage(avg_cpu: float) -> str:
    """Avalia o uso de CPU e retorna uma assessment."""
    if avg_cpu > 80:
        return "Alto - Considerar upgrade ou otimização"
    elif avg_cpu > 60:
        return "Moderado - Monitorar tendências"
    elif avg_cpu > 20:
        return "Normal - Utilização adequada"
    else:
        return "Baixo - Possível sub-utilização"


def _assess_network_usage(total_gb: float) -> str:
    """Avalia o uso de rede e retorna uma assessment."""
    if total_gb > 100:
        return "Alto - Monitorar custos de transferência"
    elif total_gb > 10:
        return "Moderado - Uso normal"
    else:
        return "Baixo - Pouco tráfego"


def _generate_performance_recommendations(performance_data: Dict[str, Any]) -> List[str]:
    """Gera recomendações baseadas nos dados de performance."""
    recommendations = []
    
    cpu_summary = performance_data.get("summary", {}).get("cpu_utilization", {})
    network_summary = performance_data.get("summary", {}).get("network_usage", {})
    
    if cpu_summary.get("average_percent", 0) < 10:
        recommendations.append("CPU subutilizada - considere reduzir o tipo de instância para economizar custos")
    elif cpu_summary.get("average_percent", 0) > 80:
        recommendations.append("CPU alta - considere upgrade do tipo de instância ou otimização de código")
    
    if network_summary.get("total_traffic_gb", 0) > 50:
        recommendations.append("Alto tráfego de rede - monitore custos de transferência de dados")
    
    return recommendations


def _generate_fleet_insights(instances_performance: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Gera insights da análise de frota."""
    insights = {
        "cpu_statistics": {},
        "network_statistics": {},
        "performance_outliers": []
    }
    
    # Coletar dados de CPU de todas as instâncias
    cpu_values = []
    network_in_values = []
    network_out_values = []
    
    for instance in instances_performance:
        cpu_metric = instance.get("metrics", {}).get("CPUUtilization")
        network_in_metric = instance.get("metrics", {}).get("NetworkIn") 
        network_out_metric = instance.get("metrics", {}).get("NetworkOut")
        
        if cpu_metric and cpu_metric.get("average") is not None:
            cpu_values.append(cpu_metric["average"])
            
            # Identificar outliers de CPU
            if cpu_metric["average"] > 90:
                insights["performance_outliers"].append({
                    "instance_id": instance["instance_id"],
                    "type": "high_cpu",
                    "value": cpu_metric["average"],
                    "severity": "HIGH"
                })
            elif cpu_metric["average"] < 5:
                insights["performance_outliers"].append({
                    "instance_id": instance["instance_id"],
                    "type": "low_cpu", 
                    "value": cpu_metric["average"],
                    "severity": "LOW"
                })
        
        if network_in_metric and network_in_metric.get("average") is not None:
            network_in_values.append(network_in_metric["average"])
        
        if network_out_metric and network_out_metric.get("average") is not None:
            network_out_values.append(network_out_metric["average"])
    
    # Calcular estatísticas da frota
    if cpu_values:
        insights["cpu_statistics"] = {
            "fleet_average_cpu": round(mean(cpu_values), 2),
            "fleet_median_cpu": round(median(cpu_values), 2),
            "fleet_max_cpu": round(max(cpu_values), 2),
            "fleet_min_cpu": round(min(cpu_values), 2),
            "instances_analyzed": len(cpu_values)
        }
    
    if network_in_values and network_out_values:
        total_network_in = sum(network_in_values)
        total_network_out = sum(network_out_values)
        
        insights["network_statistics"] = {
            "fleet_total_inbound": total_network_in,
            "fleet_total_outbound": total_network_out,
            "fleet_total_traffic": total_network_in + total_network_out,
            "average_instance_traffic": (total_network_in + total_network_out) / len(network_in_values)
        }
    
    return insights


def _generate_fleet_recommendations(fleet_insights: Dict[str, Any]) -> List[str]:
    """Gera recomendações para a frota."""
    recommendations = []
    
    cpu_stats = fleet_insights.get("cpu_statistics", {})
    fleet_avg_cpu = cpu_stats.get("fleet_average_cpu", 0)
    
    if fleet_avg_cpu < 15:
        recommendations.append("Frota com CPU subutilizada - considere rightsizing geral para reduzir custos")
    elif fleet_avg_cpu > 75:
        recommendations.append("Frota com CPU alta - monitore performance e considere upgrades")
    
    outliers = fleet_insights.get("performance_outliers", [])
    high_cpu_count = len([o for o in outliers if o["type"] == "high_cpu"])
    low_cpu_count = len([o for o in outliers if o["type"] == "low_cpu"])
    
    if high_cpu_count > 0:
        recommendations.append(f"{high_cpu_count} instância(s) com CPU crítica - priorize otimização")
    
    if low_cpu_count > 0:
        recommendations.append(f"{low_cpu_count} instância(s) subutilizada(s) - oportunidade de economia")
    
    return recommendations


def _calculate_network_costs(bandwidth_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula implicações de custo baseadas no tráfego de rede."""
    # Preços aproximados AWS (podem variar por região)
    data_transfer_out_price = 0.09  # USD por GB (primeiros 10TB)
    
    outbound_gb = bandwidth_data.get("total_outbound_gb", 0)
    
    # Apenas tráfego de saída para internet é cobrado
    estimated_monthly_cost = outbound_gb * data_transfer_out_price * 4.33  # ~4.33 semanas por mês
    
    return {
        "estimated_monthly_cost_usd": round(estimated_monthly_cost, 2),
        "cost_category": "alto" if estimated_monthly_cost > 50 else "moderado" if estimated_monthly_cost > 10 else "baixo",
        "note": "Estimativa baseada em tráfego de saída para internet"
    }


def _generate_network_recommendations(network_data: Dict[str, Any]) -> List[str]:
    """Gera recomendações baseadas na análise de rede."""
    recommendations = []
    
    bandwidth = network_data.get("bandwidth_analysis", {})
    cost_implications = network_data.get("cost_implications", {})
    
    total_traffic = bandwidth.get("total_traffic_gb", 0)
    outbound_traffic = bandwidth.get("total_outbound_gb", 0)
    traffic_ratio = bandwidth.get("traffic_ratio", 0)
    
    if total_traffic > 100:
        recommendations.append("Alto tráfego de rede detectado - monitore custos de transferência de dados")
    
    if traffic_ratio > 3:
        recommendations.append("Muito tráfego de saída - considere CloudFront ou otimização de cache")
    
    if cost_implications.get("cost_category") == "alto":
        recommendations.append("Custos altos de transferência de dados - implemente estratégias de otimização")
    
    if outbound_traffic > 50:
        recommendations.append("Considere usar CloudFront para reduzir custos de bandwidth")
    
    return recommendations 