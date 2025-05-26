#!/usr/bin/env python3
"""
Cloud Insights CLI - Análise inteligente de custos AWS com IA
"""

import os
import sys
import argparse
import boto3
from dotenv import load_dotenv
from pathlib import Path
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ProfileNotFound

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_aws_connection():
    """
    Testa a conexão AWS com diferentes métodos para garantir que funciona.
    """
    try:
        # Tentar várias formas de conectar
        session = boto3.Session()
        
        # Primeiro teste: STS get_caller_identity
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Conexão AWS validada - Account: {identity.get('Account')}")
        
        # Segundo teste: Tentar listar algo simples (regiões)
        ec2 = session.client('ec2')
        regions = ec2.describe_regions()
        print(f"✅ Permissões AWS validadas - {len(regions['Regions'])} regiões acessíveis")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar conexão AWS: {str(e)}")
        
        # Tentar diagnóstico específico
        if "ExpiredToken" in str(e):
            print("🔄 Sua sessão SSO expirou. Execute:")
            print("   jera-cli auth login")
            print("   # ou")
            print("   aws sso login")
        elif "AccessDenied" in str(e):
            print("🔐 Problema de permissões. Verifique suas políticas IAM.")
        elif "InvalidUserID.NotFound" in str(e):
            print("👤 Usuário não encontrado. Verifique sua configuração SSO.")
        
        return False

def check_aws_credentials():
    """
    Verifica se há credenciais AWS válidas disponíveis.
    Testa apenas as fontes essenciais.
    
    Ordem de prioridade:
    1. Variáveis de ambiente (incluindo .env)
    2. AWS SSO (incluindo jera-cli)
    
    Returns:
        tuple: (bool: tem_credenciais, str: método_detectado, str: detalhes)
    """
    try:
        # Tentar criar uma sessão boto3 - ela vai procurar credenciais automaticamente
        session = boto3.Session()
        
        # Tentar obter credenciais
        credentials = session.get_credentials()
        
        if credentials is None:
            return False, "none", "Nenhuma credencial encontrada"
        
        # Testar se as credenciais funcionam fazendo uma chamada simples
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        
        # Identificar o tipo de credencial (apenas 2 opções)
        credential_method = "unknown"
        details = ""
        account_id = identity.get('Account')
        arn = identity.get('Arn', '')
        
        # DEBUG (só mostra se variável DEBUG estiver definida)
        if os.getenv('DEBUG'):
            print(f"🔍 DEBUG - Tipo de credential: {type(credentials)}")
            print(f"🔍 DEBUG - ARN: {arn}")
            print(f"🔍 DEBUG - Access Key: {credentials.access_key[:10]}..." if credentials.access_key else "🔍 DEBUG - Sem access key")
        
        # 1. Verificar se são variáveis de ambiente (maior prioridade)
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('***AWS_SECRET_REMOVED***'):
            credential_method = "env_vars"
            details = f"Variáveis de ambiente (Account: {account_id})"
        
        # 2. Verificar se é SSO - verificação muito mais ampla
        else:
            # Se chegou até aqui e tem credenciais válidas, mas não são env vars, 
            # então deve ser SSO ou similar
            credential_method = "sso"
            user_info = arn.split('/')[-1] if arn else 'unknown'
            
            # Tentar identificar o tipo específico pelo ARN
            if 'jera' in arn.lower():
                details = f"Jera CLI SSO ativo (Account: {account_id}, User: {user_info})"
            elif 'assumed-role' in arn.lower():
                details = f"AWS SSO/AssumedRole ativo (Account: {account_id}, User: {user_info})"
            elif 'sso' in arn.lower():
                details = f"AWS SSO ativo (Account: {account_id}, User: {user_info})"
            else:
                # Se tem credenciais válidas mas não sabemos o tipo exato, assume SSO
                details = f"AWS SSO detectado (Account: {account_id}, User: {user_info})"
        
        return True, credential_method, details
        
    except (NoCredentialsError, PartialCredentialsError) as e:
        return False, "missing", f"Credenciais AWS não encontradas ou incompletas: {str(e)}"
    except ProfileNotFound as e:
        return False, "profile_error", f"Perfil AWS não encontrado: {e}"
    except Exception as e:
        return False, "error", f"Erro ao verificar credenciais AWS: {str(e)}"

def setup_environment():
    """Configura as variáveis de ambiente necessárias com estratégia híbrida."""
    
    # 1. Verificar OpenAI API Key primeiro
    openai_key = None
    env_file = project_root / '.env'
    
    # Tentar carregar do .env se existir
    if env_file.exists():
        load_dotenv(env_file)
        print("🔧 Arquivo .env encontrado")
    
    # Verificar OpenAI key (obrigatória)
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY não encontrada")
        print("📋 Configure a chave OpenAI no arquivo .env ou como variável de ambiente")
        print("💡 Obtenha sua chave em: https://platform.openai.com/api-keys")
        return False
    
    # Configurar modelo padrão se não especificado
    if not os.getenv('OPENAI_MODEL'):
        os.environ['OPENAI_MODEL'] = 'gpt-4'
        print("🤖 Usando modelo OpenAI padrão: gpt-4")
    
    # 2. Verificar credenciais AWS (estratégia híbrida)
    print("\n🔍 Verificando credenciais AWS...")
    
    has_aws_creds, method, details = check_aws_credentials()
    
    if has_aws_creds:
        # Credenciais AWS válidas encontradas
        if method == "sso":
            print(f"✅ {details}")
            print("💡 Usando AWS SSO - excelente para segurança!")
            print("🔗 Certifique-se de que sua sessão SSO não expirou")
        elif method == "env_vars":
            print(f"✅ {details}")
            print("💡 Usando variáveis de ambiente AWS")
        else:
            print(f"✅ {details}")
            print("💡 Método de autenticação detectado")
            
        # Configurar região padrão se não estiver definida
        if not os.getenv('AWS_DEFAULT_REGION'):
            # Tentar pegar da sessão boto3
            session = boto3.Session()
            region = session.region_name or 'us-east-1'
            os.environ['AWS_DEFAULT_REGION'] = region
            print(f"🌍 Região AWS: {region}")
        
        # Teste adicional de conexão para garantir que funciona
        print("\n🔍 Testando conexão AWS...")
        if test_aws_connection():
            print("🎉 Credenciais AWS confirmadas e funcionais!")
            return True
        else:
            print("❌ Credenciais detectadas mas não funcionais")
            return False
    
    else:
        # Verificação de fallback: tentar usar boto3 diretamente mesmo se a detecção falhou
        print("⚠️  Detecção automática falhou, tentando fallback...")
        try:
            session = boto3.Session()
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            print(f"✅ Fallback bem-sucedido! Account: {identity.get('Account')}")
            print("💡 Suas credenciais AWS estão funcionando")
            
            # Configurar região se necessário
            if not os.getenv('AWS_DEFAULT_REGION'):
                region = session.region_name or 'us-east-1'
                os.environ['AWS_DEFAULT_REGION'] = region
                print(f"🌍 Região AWS: {region}")
            
            return True
            
        except Exception as fallback_error:
            print(f"❌ Fallback também falhou: {str(fallback_error)}")
            
            # Credenciais AWS não encontradas
            print("❌ Credenciais AWS não encontradas!")
            print("\n📋 Configure suas credenciais AWS usando uma das opções:")
            print("\n🥇 RECOMENDADO - Variáveis de ambiente (.env):")
            print("   Adicione ao seu arquivo .env:")
            print("   AWS_ACCESS_KEY_ID=sua_access_key")
            print("   ***AWS_SECRET_REMOVED***=sua_secret_key") 
            print("   AWS_DEFAULT_REGION=us-east-1")
            
            print("\n🥈 AWS SSO (inclui jera-cli):")
            print("   jera-cli aws-login && export AWS_PROFILE=profile-que-voce-usou")
            print("   # ou")
            print("   aws sso configure")
            
            print("\n💡 Após configurar, execute novamente:")
            print("   cloud-insights -q \"sua pergunta\"")
            return False

def run_query(question: str):
    """Executa uma consulta no agente Cloud Insights."""
    try:
        print(f"🤖 Processando: \"{question}\"\n")
        
        # Importar a função do agente após configurar environment
        from src.ia.agent import run_agent_query
        
        # Executar consulta
        run_agent_query(question)
        
    except KeyboardInterrupt:
        print("\n⏹️  Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao processar consulta: {str(e)}")
        sys.exit(1)

def show_examples():
    """Mostra exemplos de consultas que podem ser feitas."""
    examples = [
        "Quais são os top 5 serviços mais caros?",
        "Qual foi o custo do RDS no último mês?",
        "Mostre o custo do EC2 nos últimos 3 meses",
        "Analise o tráfego de rede das instâncias EC2",
        "Quais instâncias estão subutilizadas?",
        "Audite recursos sem tags de governança",
        "Compare custos de storage S3 vs EBS",
        "Preveja o custo para o próximo mês",
        "Encontre instâncias EC2 por tag Environment",
        "Analise performance da instância Valhalla"
    ]
    
    print("💡 Exemplos de consultas que você pode fazer:")
    print("=" * 50)
    for i, example in enumerate(examples, 1):
        print(f"{i:2d}. cloud-insights -q \"{example}\"")
    print()

def show_version():
    """Mostra informações de versão e capacidades."""
    print("🔍 Cloud Insights CLI v1.0.0")
    print("📊 Análise inteligente de custos AWS com IA")
    print()
    print("🛠️  Capacidades:")
    print("  • Análise de custos AWS (Cost Explorer)")
    print("  • Monitoramento de performance (CloudWatch)")  
    print("  • Resolução inteligente de serviços")
    print("  • Auditoria de governança")
    print("  • Busca fuzzy para serviços")
    print("  • 24 ferramentas especializadas")
    print()
    print("🔑 Métodos de autenticação AWS suportados:")
    print("  • AWS SSO (Single Sign-On)")
    print("  • Variáveis de ambiente (.env)")
    print()
    print("🤖 Powered by OpenAI GPT-4")

def main():
    """Função principal do CLI."""
    parser = argparse.ArgumentParser(
        prog='cloud-insights',
        description='🔍 Cloud Insights - Análise inteligente de custos AWS com IA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  cloud-insights -q "Quais são os top 5 serviços mais caros?"
  cloud-insights -q "Qual foi o custo do RDS no último mês?"
  cloud-insights --examples
  cloud-insights --version

Autenticação AWS (2 opções):
  • AWS SSO: jera-cli auth login ou aws sso login
  • Arquivo .env: Configure credenciais manualmente
        """
    )
    
    # Argumentos principais
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        '-q', '--query',
        type=str,
        help='Pergunta para análise de custos AWS'
    )
    
    group.add_argument(
        '--examples',
        action='store_true',
        help='Mostrar exemplos de consultas'
    )
    
    group.add_argument(
        '--version',
        action='store_true',
        help='Mostrar versão e capacidades'
    )
    
    # Parse dos argumentos
    args = parser.parse_args()
    
    # Mostrar versão
    if args.version:
        show_version()
        return
    
    # Mostrar exemplos
    if args.examples:
        show_examples()
        return
    
    # Configurar ambiente
    if not setup_environment():
        sys.exit(1)
    
    # Executar consulta
    if args.query:
        run_query(args.query)

if __name__ == '__main__':
    main() 