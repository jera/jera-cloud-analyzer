"""
Módulo para resolução inteligente de nomes de serviços AWS.
Combina mapeamento hardcoded, discovery automático e busca fuzzy.
"""

import json
import os
import time
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.clouds.aws.cost_explorer import CostExplorer


class ServiceResolver:
    """
    Resolver inteligente para nomes de serviços AWS.
    """
    
    def __init__(self, cache_file: str = "aws_services_cache.json", cache_ttl_hours: int = 24):
        """
        Inicializa o resolver de serviços.
        
        Args:
            cache_file: Arquivo para cache dos serviços descobertos
            cache_ttl_hours: TTL do cache em horas (padrão: 24h)
        """
        self.cache_file = os.path.join(os.path.dirname(__file__), cache_file)
        self.cache_ttl_hours = cache_ttl_hours
        self._service_mapping = self._get_service_mapping()
        self._cached_services = None
        
    def _get_service_mapping(self) -> Dict[str, str]:
        """
        Mapeamento hardcoded dos serviços AWS mais comuns.
        Mapeia apelidos/nomes populares para nomes oficiais.
        """
        return {
            # Compute
            "ec2": "Amazon Elastic Compute Cloud - Compute",
            "lambda": "AWS Lambda",
            "ecs": "Amazon Elastic Container Service",
            "eks": "Amazon Elastic Kubernetes Service",
            "fargate": "Amazon Elastic Container Service",
            "lightsail": "Amazon Lightsail",
            
            # Storage
            "s3": "Amazon Simple Storage Service",
            "ebs": "Amazon Elastic Block Store",
            "efs": "Amazon Elastic File System",
            "fsx": "Amazon FSx",
            "glacier": "Amazon Glacier",
            "storage gateway": "AWS Storage Gateway",
            
            # Database
            "rds": "Amazon Relational Database Service",
            "dynamodb": "Amazon DynamoDB",
            "aurora": "Amazon Relational Database Service",
            "redshift": "Amazon Redshift",
            "documentdb": "Amazon DocumentDB (with MongoDB compatibility)",
            "neptune": "Amazon Neptune",
            "elasticache": "Amazon ElastiCache",
            
            # Networking
            "cloudfront": "Amazon CloudFront",
            "route53": "Amazon Route 53",
            "vpc": "Amazon Virtual Private Cloud",
            "elb": "Elastic Load Balancing",
            "alb": "Elastic Load Balancing",
            "nlb": "Elastic Load Balancing",
            "api gateway": "Amazon API Gateway",
            "cloudflare": "Amazon CloudFront",  # Comum confusão
            
            # Analytics
            "athena": "Amazon Athena",
            "emr": "Amazon Elastic MapReduce",
            "kinesis": "Amazon Kinesis",
            "glue": "AWS Glue",
            "quicksight": "Amazon QuickSight",
            
            # AI/ML
            "sagemaker": "Amazon SageMaker",
            "rekognition": "Amazon Rekognition",
            "textract": "Amazon Textract",
            "comprehend": "Amazon Comprehend",
            "translate": "Amazon Translate",
            
            # Security
            "iam": "AWS Identity and Access Management",
            "kms": "AWS Key Management Service",
            "secrets manager": "AWS Secrets Manager",
            "waf": "AWS WAF",
            "shield": "AWS Shield",
            "guard duty": "Amazon GuardDuty",
            
            # Monitoring
            "cloudwatch": "Amazon CloudWatch",
            "cloudtrail": "AWS CloudTrail",
            "config": "AWS Config",
            "x-ray": "AWS X-Ray",
            
            # Developer Tools
            "codecommit": "AWS CodeCommit",
            "codebuild": "AWS CodeBuild",
            "codepipeline": "AWS CodePipeline",
            "codedeploy": "AWS CodeDeploy",
            
            # Integration
            "sns": "Amazon Simple Notification Service",
            "sqs": "Amazon Simple Queue Service",
            "eventbridge": "Amazon EventBridge",
            "step functions": "AWS Step Functions",
            
            # Management
            "cloudformation": "AWS CloudFormation",
            "systems manager": "AWS Systems Manager",
            "opsworks": "AWS OpsWorks",
            "organizations": "AWS Organizations",
            
            # Cost Management
            "cost explorer": "AWS Cost Explorer",
            "budgets": "AWS Budgets",
            "cost and usage report": "AWS Cost and Usage Report",
        }
    
    def resolve_service_name(self, user_input: str, confidence_threshold: float = 0.6) -> Tuple[str, float, List[str]]:
        """
        Resolve o nome do serviço usando estratégia híbrida.
        
        Args:
            user_input: Nome do serviço fornecido pelo usuário
            confidence_threshold: Limite mínimo de confiança para match automático
            
        Returns:
            Tupla (nome_resolvido, confiança, sugestões_alternativas)
        """
        user_input_clean = user_input.lower().strip()
        
        # 1. Tentativa: Mapeamento direto
        if user_input_clean in self._service_mapping:
            return self._service_mapping[user_input_clean], 1.0, []
        
        # 2. Tentativa: Busca exata (case insensitive) nos serviços da conta
        all_services = self._get_cached_services()
        
        for service in all_services:
            if service.lower() == user_input_clean:
                return service, 1.0, []
        
        # 3. Tentativa: Busca fuzzy nos serviços mapeados
        mapped_matches = self._fuzzy_search_mapped(user_input_clean, confidence_threshold)
        
        # 4. Tentativa: Busca fuzzy nos serviços da conta
        account_matches = self._fuzzy_search_account(user_input_clean, all_services, confidence_threshold)
        
        # Combinar e ordenar matches por confiança
        all_matches = mapped_matches + account_matches
        all_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Remover duplicatas mantendo o melhor score
        unique_matches = {}
        for service, score in all_matches:
            if service not in unique_matches or unique_matches[service] < score:
                unique_matches[service] = score
        
        # Converter de volta para lista ordenada
        final_matches = [(service, score) for service, score in unique_matches.items()]
        final_matches.sort(key=lambda x: x[1], reverse=True)
        
        if final_matches:
            best_match, best_score = final_matches[0]
            suggestions = [service for service, _ in final_matches[1:6]]  # Top 5 alternativas
            
            if best_score >= confidence_threshold:
                return best_match, best_score, suggestions
            else:
                # Score baixo, retornar original com sugestões
                return user_input, 0.0, suggestions
        
        # Nenhum match encontrado
        return user_input, 0.0, []
    
    def _fuzzy_search_mapped(self, user_input: str, threshold: float) -> List[Tuple[str, float]]:
        """Busca fuzzy nos serviços mapeados."""
        matches = []
        
        for key, official_name in self._service_mapping.items():
            # Comparar com a chave do mapeamento
            key_similarity = SequenceMatcher(None, user_input, key).ratio()
            if key_similarity >= threshold:
                matches.append((official_name, key_similarity))
            
            # Comparar com palavras do nome oficial
            official_words = official_name.lower().split()
            for word in official_words:
                if len(word) > 2:  # Ignorar palavras muito pequenas
                    word_similarity = SequenceMatcher(None, user_input, word).ratio()
                    if word_similarity >= threshold:
                        matches.append((official_name, word_similarity * 0.9))  # Penalizar um pouco
        
        return matches
    
    def _fuzzy_search_account(self, user_input: str, services: List[str], threshold: float) -> List[Tuple[str, float]]:
        """Busca fuzzy nos serviços da conta."""
        matches = []
        
        for service in services:
            # Comparar nome completo
            full_similarity = SequenceMatcher(None, user_input, service.lower()).ratio()
            if full_similarity >= threshold:
                matches.append((service, full_similarity))
            
            # Comparar palavras individuais
            words = service.lower().split()
            for word in words:
                if len(word) > 2:
                    word_similarity = SequenceMatcher(None, user_input, word).ratio()
                    if word_similarity >= threshold:
                        matches.append((service, word_similarity * 0.8))  # Penalizar mais
        
        return matches
    
    def _get_cached_services(self) -> List[str]:
        """
        Obtém lista de serviços, usando cache se disponível e válido.
        """
        if self._cached_services is not None:
            return self._cached_services
        
        # Verificar se cache existe e é válido
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_timestamp = cache_data.get('timestamp', 0)
                cache_age_hours = (time.time() - cache_timestamp) / 3600
                
                if cache_age_hours < self.cache_ttl_hours:
                    print(f"🔄 Usando cache de serviços (idade: {cache_age_hours:.1f}h)")
                    self._cached_services = cache_data.get('services', [])
                    return self._cached_services
                else:
                    print(f"⏰ Cache expirado (idade: {cache_age_hours:.1f}h), renovando...")
            
            except Exception as e:
                print(f"⚠️  Erro ao ler cache: {e}")
        
        # Cache inválido ou inexistente, buscar da AWS
        self._cached_services = self._discover_services()
        self._save_cache()
        
        return self._cached_services
    
    def _discover_services(self) -> List[str]:
        """
        Descobre todos os serviços disponíveis na conta AWS.
        """
        print("🔍 Descobrindo serviços AWS na conta...")
        
        try:
            cost_explorer = CostExplorer()
            response = cost_explorer.get_dimension_values('SERVICE')
            
            services = [item['Value'] for item in response.get('DimensionValues', [])]
            print(f"✅ Descobertos {len(services)} serviços na conta")
            
            return services
            
        except Exception as e:
            print(f"❌ Erro ao descobrir serviços: {e}")
            # Fallback: usar apenas mapeamento hardcoded
            return list(self._service_mapping.values())
    
    def _save_cache(self):
        """Salva cache dos serviços descobertos."""
        if self._cached_services is None:
            return
        
        try:
            cache_data = {
                'timestamp': time.time(),
                'services': self._cached_services,
                'total_services': len(self._cached_services),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Cache salvo: {len(self._cached_services)} serviços")
            
        except Exception as e:
            print(f"⚠️  Erro ao salvar cache: {e}")
    
    def get_all_services(self) -> List[str]:
        """
        Retorna lista completa de todos os serviços conhecidos.
        """
        return sorted(set(list(self._service_mapping.values()) + self._get_cached_services()))
    
    def suggest_services(self, partial_name: str, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Sugere serviços baseado em nome parcial.
        
        Args:
            partial_name: Nome parcial do serviço
            limit: Número máximo de sugestões
            
        Returns:
            Lista de tuplas (nome_serviço, score_confiança)
        """
        matches = []
        all_services = self.get_all_services()
        
        for service in all_services:
            if partial_name.lower() in service.lower():
                score = len(partial_name) / len(service)  # Score baseado em proporção
                matches.append((service, score))
        
        # Ordenar por score e retornar top N
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    def clear_cache(self):
        """Remove o cache de serviços."""
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            print("🗑️  Cache removido")
        
        self._cached_services = None


# Instância global para uso nas ferramentas
service_resolver = ServiceResolver() 