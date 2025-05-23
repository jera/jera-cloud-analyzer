"""
Cliente para conexão com AWS Cost Explorer e outros serviços.
"""
import os
import boto3
from typing import Dict, List, Any, Optional


class AWSClient:
    """
    Cliente base para comunicação com a AWS.
    Gerencia a sessão e fornece acesso aos diversos serviços da AWS.
    """
    
    def __init__(self, region_name: str = None, profile_name: Optional[str] = None):
        """
        Inicializa um cliente AWS.
        
        Args:
            region_name: Região da AWS para conexão
            profile_name: Nome do perfil de credenciais (opcional)
        """
        # Usar a região das variáveis de ambiente como fallback
        region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        self.session = self._create_session(region_name, profile_name)
        
    def _create_session(self, region_name: str, profile_name: Optional[str] = None) -> boto3.Session:
        """
        Cria uma sessão boto3.
        
        Args:
            region_name: Região da AWS para conexão
            profile_name: Nome do perfil de credenciais (opcional)
            
        Returns:
            Sessão boto3 configurada
        """
        session_kwargs = {"region_name": region_name}
        
        if profile_name:
            session_kwargs["profile_name"] = profile_name
            
        return boto3.Session(**session_kwargs)
    
    def get_client(self, service_name: str) -> Any:
        """
        Obtém um cliente para um serviço específico da AWS.
        
        Args:
            service_name: Nome do serviço AWS (ex: 'ce' para Cost Explorer)
            
        Returns:
            Cliente boto3 para o serviço solicitado
        """
        return self.session.client(service_name) 