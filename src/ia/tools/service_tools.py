"""
Ferramentas para resolução e sugestão de serviços AWS.
"""

import json
import sys
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.ia.tools.service_resolver import service_resolver


def resolve_service_name(service_name: str, auto_apply: bool = True) -> str:
    """
    Resolve o nome oficial de um serviço AWS a partir de um nome informal.
    
    Args:
        service_name: Nome do serviço (informal, apelido, ou oficial)
        auto_apply: Se deve aplicar automaticamente o melhor match (padrão: True)
        
    Returns:
        JSON com nome resolvido, confiança e sugestões
        
    Exemplos:
    - resolve_service_name("rds") → "Amazon Relational Database Service"
    - resolve_service_name("ec2") → "Amazon Elastic Compute Cloud - Compute"
    - resolve_service_name("lambda") → "AWS Lambda"
    """
    print(f"RESOLVENDO NOME DO SERVIÇO: '{service_name}'")
    
    try:
        resolved_name, confidence, suggestions = service_resolver.resolve_service_name(service_name)
        
        result = {
            "original_input": service_name,
            "resolved_name": resolved_name,
            "confidence": confidence,
            "auto_applied": False,
            "suggestions": suggestions,
            "resolution_method": "unknown"
        }
        
        # Determinar método de resolução
        if confidence == 1.0:
            if resolved_name != service_name:
                result["resolution_method"] = "exact_mapping"
            else:
                result["resolution_method"] = "exact_match"
        elif confidence > 0.6:
            result["resolution_method"] = "fuzzy_match"
        else:
            result["resolution_method"] = "no_confident_match"
        
        # Aplicar automaticamente se confiança alta
        if auto_apply and confidence >= 0.8:
            result["auto_applied"] = True
            print(f"✅ Auto-aplicado: {resolved_name} (confiança: {confidence:.2f})")
        elif confidence > 0.0:
            print(f"🤔 Match encontrado: {resolved_name} (confiança: {confidence:.2f})")
        else:
            print(f"❌ Nenhum match confiável para '{service_name}'")
        
        # Adicionar informações extras
        if suggestions:
            result["has_alternatives"] = True
            print(f"💡 {len(suggestions)} sugestões alternativas disponíveis")
        else:
            result["has_alternatives"] = False
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Erro ao resolver nome do serviço: {str(e)}",
            "original_input": service_name
        }, ensure_ascii=False, indent=2)


def suggest_services(partial_name: str, limit: int = 10) -> str:
    """
    Sugere serviços AWS baseado em um nome parcial ou palavras-chave.
    
    Args:
        partial_name: Nome parcial ou palavra-chave
        limit: Número máximo de sugestões (padrão: 10)
        
    Returns:
        JSON com lista de serviços sugeridos e seus scores
        
    Exemplos:
    - suggest_services("database") → Lista serviços de banco de dados
    - suggest_services("stor") → Lista serviços de storage
    - suggest_services("compute") → Lista serviços de computação
    """
    print(f"SUGERINDO SERVIÇOS PARA: '{partial_name}'")
    
    try:
        suggestions = service_resolver.suggest_services(partial_name, limit)
        
        result = {
            "search_term": partial_name,
            "total_suggestions": len(suggestions),
            "suggestions": [
                {
                    "service_name": service,
                    "relevance_score": score,
                    "category": _categorize_service(service)
                }
                for service, score in suggestions
            ]
        }
        
        if suggestions:
            print(f"✅ Encontradas {len(suggestions)} sugestões")
        else:
            print(f"❌ Nenhuma sugestão encontrada para '{partial_name}'")
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Erro ao sugerir serviços: {str(e)}",
            "search_term": partial_name
        }, ensure_ascii=False, indent=2)


def list_all_services(category_filter: Optional[str] = None) -> str:
    """
    Lista todos os serviços AWS conhecidos, opcionalmente filtrados por categoria.
    
    Args:
        category_filter: Filtro por categoria (compute, storage, database, networking, etc.)
        
    Returns:
        JSON com lista completa de serviços organizados por categoria
        
    Exemplos:
    - list_all_services() → Todos os serviços
    - list_all_services("database") → Apenas serviços de banco de dados
    - list_all_services("compute") → Apenas serviços de computação
    """
    print(f"LISTANDO SERVIÇOS - Filtro: {category_filter or 'nenhum'}")
    
    try:
        all_services = service_resolver.get_all_services()
        
        # Categorizar serviços
        categorized_services = {}
        
        for service in all_services:
            category = _categorize_service(service)
            
            if category not in categorized_services:
                categorized_services[category] = []
            
            categorized_services[category].append(service)
        
        # Aplicar filtro se fornecido
        if category_filter:
            category_filter = category_filter.lower()
            filtered_categories = {
                k: v for k, v in categorized_services.items() 
                if category_filter in k.lower()
            }
            categorized_services = filtered_categories
        
        # Ordenar categorias e serviços
        for category in categorized_services:
            categorized_services[category].sort()
        
        result = {
            "total_services": len(all_services),
            "categories_shown": len(categorized_services),
            "filter_applied": category_filter,
            "services_by_category": categorized_services,
            "summary": {
                category: len(services) 
                for category, services in categorized_services.items()
            }
        }
        
        print(f"✅ Listados {len(all_services)} serviços em {len(categorized_services)} categorias")
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Erro ao listar serviços: {str(e)}"
        }, ensure_ascii=False, indent=2)


def refresh_services_cache() -> str:
    """
    Força a atualização do cache de serviços AWS, redescobrindo todos os serviços da conta.
    
    Returns:
        JSON com status da atualização do cache
    """
    print("🔄 FORÇANDO ATUALIZAÇÃO DO CACHE DE SERVIÇOS")
    
    try:
        # Limpar cache atual
        service_resolver.clear_cache()
        
        # Forçar nova descoberta
        services = service_resolver._get_cached_services()
        
        result = {
            "status": "success",
            "message": "Cache de serviços atualizado com sucesso",
            "total_services_discovered": len(services),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"✅ Cache atualizado: {len(services)} serviços descobertos")
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Erro ao atualizar cache: {str(e)}"
        }, ensure_ascii=False, indent=2)


def _categorize_service(service_name: str) -> str:
    """
    Categoriza um serviço AWS baseado no seu nome.
    """
    service_lower = service_name.lower()
    
    # Compute
    if any(keyword in service_lower for keyword in ['compute', 'ec2', 'lambda', 'container', 'kubernetes', 'fargate', 'lightsail']):
        return "compute"
    
    # Storage
    elif any(keyword in service_lower for keyword in ['storage', 's3', 'ebs', 'efs', 'glacier', 'backup']):
        return "storage"
    
    # Database
    elif any(keyword in service_lower for keyword in ['database', 'rds', 'dynamodb', 'redshift', 'documentdb', 'neptune', 'elasticache']):
        return "database"
    
    # Networking
    elif any(keyword in service_lower for keyword in ['network', 'vpc', 'cloudfront', 'route', 'load balancing', 'api gateway']):
        return "networking"
    
    # Security
    elif any(keyword in service_lower for keyword in ['identity', 'iam', 'security', 'kms', 'secrets', 'waf', 'shield', 'guard']):
        return "security"
    
    # Analytics
    elif any(keyword in service_lower for keyword in ['analytics', 'athena', 'emr', 'kinesis', 'glue', 'quicksight']):
        return "analytics"
    
    # AI/ML
    elif any(keyword in service_lower for keyword in ['sagemaker', 'rekognition', 'textract', 'comprehend', 'translate', 'machine learning']):
        return "ai_ml"
    
    # Monitoring
    elif any(keyword in service_lower for keyword in ['cloudwatch', 'cloudtrail', 'config', 'x-ray', 'monitoring']):
        return "monitoring"
    
    # Developer Tools
    elif any(keyword in service_lower for keyword in ['code', 'build', 'pipeline', 'deploy']):
        return "developer_tools"
    
    # Integration
    elif any(keyword in service_lower for keyword in ['notification', 'queue', 'eventbridge', 'step functions', 'sns', 'sqs']):
        return "integration"
    
    # Management
    elif any(keyword in service_lower for keyword in ['cloudformation', 'systems manager', 'opsworks', 'organizations']):
        return "management"
    
    # Cost Management
    elif any(keyword in service_lower for keyword in ['cost', 'budget', 'billing']):
        return "cost_management"
    
    else:
        return "other" 