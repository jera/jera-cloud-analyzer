import boto3
import pandas as pd
from datetime import datetime, timedelta
from tabulate import tabulate
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import botocore.config

import os
import sys
import requests
from rich.console import Console

import boto3
import pandas as pd
from datetime import datetime, timedelta, timezone
from tabulate import tabulate
import matplotlib.pyplot as plt
import os
import sys
import requests
import botocore.config
import subprocess
import json
from io import StringIO

console = Console()
class AWSCostAnalyzer:
    def __init__(self):
        # Configuração para ignorar perfil padrão
        config = botocore.config.Config(
            signature_version='v4',
            retries={'max_attempts': 3}
        )
        
        # Verifica e configura a sessão SSO
        if not self._check_aws_sso_session():
            self._configure_aws_sso()
        
        # Obtém o profile ativo
        profile = self._get_active_profile()
        
        # Cria a sessão boto3
        try:
            if profile:
                session = boto3.Session(profile_name=profile)
            else:
                # Tenta usar as credenciais padrão
                session = boto3.Session()
            
            # Testa a sessão
            sts = session.client('sts')
            sts.get_caller_identity()
        except Exception as e:
            console.print("❌ Não foi possível autenticar com a AWS!", style="bold red")
            console.print("Por favor, execute 'aws sso login' e tente novamente.", style="bold yellow")
            sys.exit(1)
        
        # Cria os clientes usando a sessão
        self.client = session.client('ce', config=config)
        self.resourcetagging_client = session.client('resourcegroupstaggingapi', config=config)
        
        self.exchange_rate = self._get_exchange_rate()
        self.reports_dir = 'reports'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)


    def _check_aws_sso_config(self):
        """Verifica se o AWS SSO está configurado corretamente"""
        try:
            home = os.path.expanduser("~")
            config_file = os.path.join(home, ".aws", "config")
            
            if not os.path.exists(config_file):
                return False
                
            with open(config_file, 'r') as f:
                config_content = f.read()
                
            required_configs = [
                "sso_session",
                "sso_account_id",
                "sso_role_name",
                "region",
                "output"
            ]
            
            for config in required_configs:
                if config not in config_content:
                    return False
                    
            return True
        except Exception as e:
            console.print(f"Erro ao verificar configuração SSO: {str(e)}", style="bold red")
            return False

    def _check_aws_sso_session(self):
        """Verifica se existe uma sessão AWS SSO ativa"""
        try:
            home = os.path.expanduser("~")
            sso_cache_dir = os.path.join(home, ".aws", "sso", "cache")
            
            if not os.path.exists(sso_cache_dir):
                return False
                
            sso_cache_files = [f for f in os.listdir(sso_cache_dir) if f.endswith('.json')]
            
            for cache_file in sso_cache_files:
                try:
                    with open(os.path.join(sso_cache_dir, cache_file), 'r') as f:
                        cache_data = json.load(f)
                    
                    if (
                        'startUrl' in cache_data and 
                        'accessToken' in cache_data and 
                        'expiresAt' in cache_data
                    ):
                        expiration = datetime.fromisoformat(cache_data['expiresAt'].replace('Z', '+00:00'))
                        if expiration > datetime.now(timezone.utc):
                            return True
                except json.JSONDecodeError:
                    continue
                    
            return False
        except Exception as e:
            console.print(f"Erro ao verificar sessão SSO: {str(e)}", style="dim red")
            return False

    def _configure_aws_sso(self):
        """Configura o AWS SSO"""
        console.print("\n📝 Configurando AWS SSO...", style="bold blue")
        console.print("\nPor favor, tenha em mãos as seguintes informações:", style="bold yellow")
        console.print("1. SSO start URL (exemplo: https://jera.awsapps.com/start)")
        console.print("2. SSO Region (exemplo: us-east-1)")
        console.print("3. Nome do perfil que deseja criar (exemplo: jera-dev)")
        console.print("\nDicas de configuração:", style="bold green")
        console.print("- SSO start URL: Peça para alguém do time ou procure no 1Password")
        console.print("- SSO Region: us-east-1")
        console.print("- CLI default client Region: us-east-1")
        console.print("- CLI default output format: json")
        console.print("- CLI profile name: Use seu nome ou algo que identifique facilmente\n")
        
        input("Pressione Enter quando estiver pronto para continuar...")
        
        try:
            console.print("\n1. Configurando sessão SSO...", style="bold blue")
            subprocess.run(["aws", "configure", "sso"], check=True)
            
            time.sleep(2)
            
            if self._check_aws_sso_config():
                console.print("✅ AWS SSO configurado com sucesso!", style="bold green")
                return True
            else:
                console.print("❌ Configuração do AWS SSO incompleta ou incorreta.", style="bold red")
                console.print("\nDicas de resolução:", style="bold yellow")
                console.print("1. Verifique se você completou todos os passos da configuração")
                console.print("2. Certifique-se de que a URL do SSO está correta")
                console.print("3. Tente remover a configuração atual e começar novamente:")
                console.print("   rm -rf ~/.aws/config ~/.aws/credentials")
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Erro ao configurar AWS SSO: {str(e)}", style="bold red")
            sys.exit(1)

    def _get_active_profile(self):
        """Obtém o profile AWS ativo"""
        try:
            # Primeiro tenta usar o profile padrão
            try:
                result = subprocess.run(
                    ["aws", "sts", "get-caller-identity"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    # Se não der erro, significa que o profile padrão está funcionando
                    return None  # None significa usar as credenciais padrão
            except:
                pass

            # Se não funcionar, lista todos os profiles
            result = subprocess.run(
                ["aws", "configure", "list-profiles"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                profiles = result.stdout.strip().split('\n')
                
                for profile in profiles:
                    try:
                        result = subprocess.run(
                            ["aws", "sts", "get-caller-identity", "--profile", profile],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            return profile
                    except:
                        continue
            
            return None
        except Exception as e:
            console.print(f"Erro ao obter profile ativo: {str(e)}", style="dim red")
            return None

    def _get_exchange_rate(self):
        """Obtém a taxa de câmbio atual USD/BRL"""
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            data = response.json()
            return data['rates']['BRL']
        except Exception as e:
            print(f"\nAVISO: Não foi possível obter a taxa de câmbio atual. Usando taxa fixa de 5.0")
            print(f"Erro: {str(e)}")
            return 5.0  # Taxa fixa caso a API falhe

    def _convert_to_brl(self, usd_value):
        """Converte valor de USD para BRL"""
        return usd_value * self.exchange_rate

    def get_cost_by_service(self, start_date, end_date):
        response = self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        data = []
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost_usd = float(group['Metrics']['UnblendedCost']['Amount'])
                cost_brl = self._convert_to_brl(cost_usd)
                data.append({
                    'Service': service,
                    'Cost_USD': cost_usd,
                    'Cost_BRL': cost_brl,
                    'Period': result['TimePeriod']['Start']
                })
        
        return pd.DataFrame(data)

    def _clean_tag_value(self, tag_value):
        """Limpa o valor da tag removendo caracteres especiais e prefixos"""
        if not tag_value or tag_value == 'NoTag':
            return ''
            
        # Remove o prefixo da tag se existir (formato: chave$valor)
        if '$' in tag_value:
            tag_value = tag_value.split('$')[-1]
            
        # Remove caracteres especiais do final
        tag_value = tag_value.rstrip('$')
        return tag_value

    def get_cost_by_tag(self, start_date, end_date, tag_key):
        """Obtém custos por tag"""
        try:
            # Primeiro tenta sem prefixo
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'TAG', 'Key': tag_key}]
            )
            
            data = []
            
            for result in response['ResultsByTime']:
                for group in result.get('Groups', []):
                    if group['Keys']:
                        tag_value = self._clean_tag_value(group['Keys'][0])
                        if tag_value:  # Ignora valores vazios
                            cost_usd = float(group['Metrics']['UnblendedCost']['Amount'])
                            cost_brl = self._convert_to_brl(cost_usd)
                            data.append({
                                'Tag': tag_value,
                                'Cost_USD': cost_usd,
                                'Cost_BRL': cost_brl,
                                'Period': result['TimePeriod']['Start']
                            })
            
            # Se não encontrou dados, tenta com prefixo 'user:'
            if not data:
                response = self.client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date,
                        'End': end_date
                    },
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[{'Type': 'TAG', 'Key': f'user:{tag_key}'}]
                )
                
                for result in response['ResultsByTime']:
                    for group in result.get('Groups', []):
                        if group['Keys']:
                            tag_value = self._clean_tag_value(group['Keys'][0])
                            if tag_value:  # Ignora valores vazios
                                cost_usd = float(group['Metrics']['UnblendedCost']['Amount'])
                                cost_brl = self._convert_to_brl(cost_usd)
                                data.append({
                                    'Tag': tag_value,
                                    'Cost_USD': cost_usd,
                                    'Cost_BRL': cost_brl,
                                    'Period': result['TimePeriod']['Start']
                                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"\nAVISO: Erro ao buscar custos para a tag {tag_key}: {str(e)}")
            return pd.DataFrame()

    def _format_brl(self, value):
        """Formata valor para Real brasileiro"""
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _save_to_file(self, content, filename):
        """Salva o conteúdo em um arquivo dentro do diretório reports"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(self.reports_dir, f'{filename}_{timestamp}.txt')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\nRelatório salvo em: {filepath}")

    def _print_and_save(self, content, filename):
        """Imprime o conteúdo no terminal e salva em arquivo"""
        print(content)
        self._save_to_file(content, filename)

    def generate_cost_report_by_date(self, start_date, end_date):
        """
        Gera relatório de custos por serviço para um período específico
        start_date e end_date devem estar no formato 'YYYY-MM-DD'
        """
        df_services = self.get_cost_by_service(start_date, end_date)
        
        if df_services.empty:
            message = "\nNenhum custo encontrado para o período."
            self._print_and_save(message, "relatorio_vazio")
            return
        
        # Calcula o total geral
        total_cost_brl = df_services['Cost_BRL'].sum()
        total_cost_usd = df_services['Cost_USD'].sum()
        
        report_content = []
        report_content.append(f"=== Relatório de Custos AWS ===")
        report_content.append(f"Período: {start_date} até {end_date}")
        report_content.append(f"Taxa de câmbio USD/BRL: {self.exchange_rate:.2f}")
        report_content.append(f"\nCusto Total USD: ${total_cost_usd:,.2f}")
        report_content.append(f"Custo Total BRL: {self._format_brl(total_cost_brl)}")
        
        # Calcula o total por serviço
        total_summary = df_services.groupby('Service').agg({
            'Cost_USD': 'sum',
            'Cost_BRL': 'sum'
        }).sort_values('Cost_BRL', ascending=False)
        
        total_summary['Percentual'] = (total_summary['Cost_BRL'] / total_cost_brl * 100)
        
        report_content.append("\n=== Top Serviços por Custo ===")
        
        # Formata a tabela de resumo
        formatted_summary = total_summary.copy()
        formatted_summary['Cost_USD'] = formatted_summary['Cost_USD'].apply(lambda x: f"${x:,.2f}")
        formatted_summary['Cost_BRL'] = formatted_summary['Cost_BRL'].apply(self._format_brl)
        formatted_summary['Percentual'] = formatted_summary['Percentual'].apply(lambda x: f"{x:.1f}%")
        
        report_content.append(tabulate(formatted_summary.reset_index(), 
                      headers=['Serviço', 'Custo (USD)', 'Custo (BRL)', 'Percentual'],
                      showindex=False))
        
        # Calcula totais mensais
        df_services['Month'] = pd.to_datetime(df_services['Period']).dt.strftime('%Y-%m')
        monthly_total_brl = df_services.groupby('Month')['Cost_BRL'].sum()
        monthly_total_usd = df_services.groupby('Month')['Cost_USD'].sum()
        
        report_content.append("\n=== Custos Mensais ===")
        for month in monthly_total_brl.index:
            cost_brl = monthly_total_brl[month]
            cost_usd = monthly_total_usd[month]
            report_content.append(f"{month}: USD ${cost_usd:,.2f} / {self._format_brl(cost_brl)}")
        
        # Prepara tabela detalhada por serviço e mês
        monthly_service = df_services.pivot_table(
            index='Service',
            columns='Month',
            values=['Cost_USD', 'Cost_BRL'],
            aggfunc='sum',
            fill_value=0
        ).sort_values(by=('Cost_BRL', df_services['Month'].max()), ascending=False)
        
        # Adiciona coluna de total e percentual
        monthly_service[('Cost_BRL', 'Total')] = monthly_service['Cost_BRL'].sum(axis=1)
        monthly_service[('Cost_USD', 'Total')] = monthly_service['Cost_USD'].sum(axis=1)
        monthly_service[('', 'Percentual')] = (monthly_service[('Cost_BRL', 'Total')] / total_cost_brl * 100)
        
        # Formata todos os valores da tabela
        formatted_monthly_service = monthly_service.copy()
        for column in formatted_monthly_service.columns:
            metric, month = column
            if metric == 'Cost_USD':
                formatted_monthly_service[column] = formatted_monthly_service[column].apply(lambda x: f"${x:,.2f}")
            elif metric == 'Cost_BRL':
                formatted_monthly_service[column] = formatted_monthly_service[column].apply(self._format_brl)
            elif month == 'Percentual':
                formatted_monthly_service[column] = formatted_monthly_service[column].apply(lambda x: f"{x:.1f}%")
        
        report_content.append("\n=== Detalhamento por Serviço e Mês ===")
        report_content.append("Valores em USD / BRL")
        report_content.append(tabulate(formatted_monthly_service.reset_index(), 
                      headers=['Serviço'] + [f"{m} (USD/BRL)" for m in monthly_service.columns.levels[1]], 
                      showindex=False))
        
        # Junta todo o conteúdo e salva
        final_report = '\n'.join(report_content)
        self._print_and_save(final_report, f"relatorio_custos_{start_date}_a_{end_date}")

    def get_available_tags(self):
        """Retorna todas as tags disponíveis na conta usando Resource Groups Tagging API"""
        try:
            # Busca todas as tags usando o Resource Groups Tagging API
            paginator = self.resourcetagging_client.get_paginator('get_tag_keys')
            tag_keys = set()
            
            for page in paginator.paginate():
                for tag_key in page.get('TagKeys', []):
                    # Remove o prefixo 'aws:' das tags do sistema
                    if not tag_key.startswith('aws:'):
                        tag_keys.add(tag_key)
            
            if not tag_keys:  # Se não encontrou tags, retorna a lista padrão
                return [
                    'application',
                    'servers',
                    'vordesk',
                    'biofaces',
                    'buckets'
                ]
            
            return sorted(list(tag_keys))
            
        except Exception as e:
            print(f"\nAVISO: Erro ao buscar tags: {str(e)}")
            # Retorna uma lista de tags conhecidas como fallback
            return [
                'application',
                'servers',
                'vordesk',
                'biofaces',
                'buckets'
            ]

    def generate_tag_reports(self, days=30):
        """Gera relatórios de custos por tags"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        report_content = []
        report_content.append(f"\n=== Relatório de Custos por Tags ===")
        report_content.append(f"Período: últimos {days} dias ({start_date} até {end_date})")
        
        # Obtém todas as tags disponíveis
        available_tags = self.get_available_tags()
        
        if not available_tags:
            message = "\nNenhuma tag encontrada nos recursos."
            self._print_and_save(message, "relatorio_tags_vazio")
            return
        
        for tag_key in available_tags:
            df_tag = self.get_cost_by_tag(start_date, end_date, tag_key)
            
            if not df_tag.empty:
                total_cost_brl = df_tag['Cost_BRL'].sum()
                total_cost_usd = df_tag['Cost_USD'].sum()
                
                report_content.append(f"\n=== Custos por {tag_key} ===")
                report_content.append(f"Total USD: ${total_cost_usd:,.2f}")
                report_content.append(f"Total BRL: {self._format_brl(total_cost_brl)}")
                
                # Agrupa por tag
                tag_summary = df_tag.groupby('Tag').agg({
                    'Cost_USD': 'sum',
                    'Cost_BRL': 'sum'
                }).sort_values('Cost_BRL', ascending=False)
                
                tag_summary['Percentual'] = (tag_summary['Cost_BRL'] / total_cost_brl * 100)
                
                # Formata a tabela
                formatted_summary = tag_summary.copy()
                formatted_summary['Cost_USD'] = formatted_summary['Cost_USD'].apply(lambda x: f"${x:,.2f}")
                formatted_summary['Cost_BRL'] = formatted_summary['Cost_BRL'].apply(self._format_brl)
                formatted_summary['Percentual'] = formatted_summary['Percentual'].apply(lambda x: f"{x:.1f}%")
                
                report_content.append(tabulate(formatted_summary.reset_index(),
                                   headers=[tag_key, 'Custo (USD)', 'Custo (BRL)', 'Percentual'],
                                   showindex=False))
        
        # Junta todo o conteúdo e salva
        final_report = '\n'.join(report_content)
        self._print_and_save(final_report, f"relatorio_tags_{start_date}_a_{end_date}")

    def get_resource_details(self, service_name, start_date, end_date, detail_limit=15):
        """
        Obtém detalhes dos recursos de um serviço específico
        
        Args:
            service_name (str): Nome do serviço AWS
            start_date (str): Data inicial no formato 'YYYY-MM-DD'
            end_date (str): Data final no formato 'YYYY-MM-DD'
            detail_limit (int): Número máximo de itens a serem mostrados no detalhamento
        """
        try:
            if service_name == 'Amazon Elastic Compute Cloud - Compute':
                # Detalhes por tipo de instância e região
                response = self.client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date,
                        'End': end_date
                    },
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[
                        {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'},
                        {'Type': 'DIMENSION', 'Key': 'REGION'}
                    ],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': [service_name]
                        }
                    }
                )
                
                instance_data = []
                for result in response['ResultsByTime']:
                    for group in result.get('Groups', []):
                        instance_type = group['Keys'][0] or 'N/A'
                        region = group['Keys'][1]
                        cost_usd = float(group['Metrics']['UnblendedCost']['Amount'])
                        cost_brl = self._convert_to_brl(cost_usd)
                        instance_data.append({
                            'Tipo de Instância': instance_type,
                            'Região': region,
                            'Cost_USD': cost_usd,
                            'Cost_BRL': cost_brl,
                            'Period': result['TimePeriod']['Start']
                        })
                
                # Detalhes por tipo de uso e operação
                response = self.client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date,
                        'End': end_date
                    },
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[
                        {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'},
                        {'Type': 'DIMENSION', 'Key': 'OPERATION'}
                    ],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': [service_name]
                        }
                    }
                )
                
                usage_data = []
                for result in response['ResultsByTime']:
                    for group in result.get('Groups', []):
                        usage_type = group['Keys'][0]
                        operation = group['Keys'][1] or 'N/A'
                        cost_usd = float(group['Metrics']['UnblendedCost']['Amount'])
                        cost_brl = self._convert_to_brl(cost_usd)
                        usage_data.append({
                            'Tipo de Uso': usage_type,
                            'Operação': operation,
                            'Cost_USD': cost_usd,
                            'Cost_BRL': cost_brl,
                            'Period': result['TimePeriod']['Start']
                        })
                
                return {
                    'instance_region': pd.DataFrame(instance_data),
                    'usage_operation': pd.DataFrame(usage_data),
                    'detail_limit': detail_limit
                }
                
            else:  # Outros serviços
                response = self.client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date,
                        'End': end_date
                    },
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[
                        {'Type': 'DIMENSION', 'Key': 'REGION'},
                        {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                    ],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': [service_name]
                        }
                    }
                )
                
                data = []
                for result in response['ResultsByTime']:
                    for group in result.get('Groups', []):
                        region = group['Keys'][0]
                        usage_type = group['Keys'][1]
                        cost_usd = float(group['Metrics']['UnblendedCost']['Amount'])
                        cost_brl = self._convert_to_brl(cost_usd)
                        data.append({
                            'Região': region,
                            'Tipo de Uso': usage_type,
                            'Cost_USD': cost_usd,
                            'Cost_BRL': cost_brl,
                            'Period': result['TimePeriod']['Start']
                        })
                
                df = pd.DataFrame(data)
                df.detail_limit = detail_limit  # Adiciona o limite como atributo do DataFrame
                return df
                
        except Exception as e:
            print(f"\nAVISO: Erro ao buscar detalhes do serviço {service_name}: {str(e)}")
            return pd.DataFrame()

    def generate_top_services_detail_by_date(self, start_date, end_date, top_n=5, detail_limit=5):
        """Gera relatório detalhado dos top serviços para um período específico"""
        df_services = self.get_cost_by_service(start_date, end_date)
        
        if df_services.empty:
            message = "\nNenhum custo encontrado para o período."
            self._print_and_save(message, "relatorio_detalhado_vazio")
            return
        
        report_content = []
        report_content.append(f"\n=== Relatório Detalhado dos Top {top_n} Serviços ===")
        report_content.append(f"Período: {start_date} até {end_date}")
        
        # Obtém os top serviços
        top_services = df_services.groupby('Service')['Cost_BRL'].sum().nlargest(top_n)
        
        for service in top_services.index:
            service_cost_brl = top_services[service]
            service_cost_usd = df_services[df_services['Service'] == service]['Cost_USD'].sum()
            
            report_content.append(f"\n=== {service} ===")
            report_content.append(f"Custo Total USD: ${service_cost_usd:,.2f}")
            report_content.append(f"Custo Total BRL: {self._format_brl(service_cost_brl)}")
            
            # Obtém detalhes dos recursos
            details = self.get_resource_details(service, start_date, end_date, detail_limit)
            
            if isinstance(details, dict):  # Para o caso do EC2
                # Processa dados de instância e região
                df_instance = details['instance_region']
                if not df_instance.empty:
                    instance_summary = df_instance.groupby(['Tipo de Instância', 'Região'])['Cost_BRL'].sum().reset_index()
                    instance_summary = instance_summary.sort_values('Cost_BRL', ascending=False).head(detail_limit)
                    instance_summary['Percentual'] = (instance_summary['Cost_BRL'] / service_cost_brl * 100)
                    instance_summary['Cost_USD'] = df_instance.groupby(['Tipo de Instância', 'Região'])['Cost_USD'].sum().reset_index()['Cost_USD']
                    
                    # Formata os valores
                    instance_summary['Cost_USD'] = instance_summary['Cost_USD'].apply(lambda x: f"${x:,.2f}")
                    instance_summary['Cost_BRL'] = instance_summary['Cost_BRL'].apply(self._format_brl)
                    instance_summary['Percentual'] = instance_summary['Percentual'].apply(lambda x: f"{x:.1f}%")
                    
                    report_content.append("\nTop Custos por Tipo de Instância e Região:")
                    report_content.append(tabulate(instance_summary, headers='keys', showindex=False))
                
                # Processa dados de uso e operação
                df_usage = details['usage_operation']
                if not df_usage.empty:
                    usage_summary = df_usage.groupby(['Tipo de Uso', 'Operação'])['Cost_BRL'].sum().reset_index()
                    usage_summary = usage_summary.sort_values('Cost_BRL', ascending=False).head(detail_limit)
                    usage_summary['Percentual'] = (usage_summary['Cost_BRL'] / service_cost_brl * 100)
                    usage_summary['Cost_USD'] = df_usage.groupby(['Tipo de Uso', 'Operação'])['Cost_USD'].sum().reset_index()['Cost_USD']
                    
                    # Formata os valores
                    usage_summary['Cost_USD'] = usage_summary['Cost_USD'].apply(lambda x: f"${x:,.2f}")
                    usage_summary['Cost_BRL'] = usage_summary['Cost_BRL'].apply(self._format_brl)
                    usage_summary['Percentual'] = usage_summary['Percentual'].apply(lambda x: f"{x:.1f}%")
                    
                    report_content.append("\nTop Custos por Tipo de Uso e Operação:")
                    report_content.append(tabulate(usage_summary, headers='keys', showindex=False))
            
            elif isinstance(details, pd.DataFrame) and not details.empty:  # Para outros serviços
                resource_summary = details.groupby(['Região', 'Tipo de Uso'])['Cost_BRL'].sum().reset_index()
                resource_summary = resource_summary.sort_values('Cost_BRL', ascending=False).head(detail_limit)
                resource_summary['Percentual'] = (resource_summary['Cost_BRL'] / service_cost_brl * 100)
                resource_summary['Cost_USD'] = details.groupby(['Região', 'Tipo de Uso'])['Cost_USD'].sum().reset_index()['Cost_USD']
                
                # Formata os valores
                resource_summary['Cost_USD'] = resource_summary['Cost_USD'].apply(lambda x: f"${x:,.2f}")
                resource_summary['Cost_BRL'] = resource_summary['Cost_BRL'].apply(self._format_brl)
                resource_summary['Percentual'] = resource_summary['Percentual'].apply(lambda x: f"{x:.1f}%")
                
                report_content.append("\nTop Detalhamento de Recursos:")
                report_content.append(tabulate(resource_summary, headers='keys', showindex=False))
            else:
                report_content.append("\nNenhum detalhe disponível para este serviço.")
        
        # Junta todo o conteúdo e salva
        final_report = '\n'.join(report_content)
        self._print_and_save(final_report, f"relatorio_detalhado_{start_date}_a_{end_date}")

    def generate_cost_report(self, days=90):
        """Wrapper para manter compatibilidade com código existente"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return self.generate_cost_report_by_date(start_date, end_date)

    def generate_top_services_detail(self, days=90):
        """Wrapper para manter compatibilidade com código existente"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return self.generate_top_services_detail_by_date(start_date, end_date)

    def generate_tag_report_by_date(self, start_date, end_date):
        """
        Gera relatório de custos por tag para um período específico
        start_date e end_date devem estar no formato 'YYYY-MM-DD'
        """
        tags = self.get_available_tags()
        
        if not tags:
            message = "\nNenhuma tag encontrada na conta AWS."
            self._print_and_save(message, "relatorio_tags_vazio")
            return
        
        report_content = []
        report_content.append(f"=== Relatório de Custos por Tag ===")
        report_content.append(f"Período: {start_date} até {end_date}")
        report_content.append(f"Taxa de câmbio USD/BRL: {self.exchange_rate:.2f}")
        report_content.append(f"Tags encontradas: {', '.join(tags)}\n")
        
        total_cost_all_tags_brl = 0
        total_cost_all_tags_usd = 0
        tag_summaries = []
        
        for tag_key in tags:
            df_tags = self.get_cost_by_tag(start_date, end_date, tag_key)
            
            if not df_tags.empty:
                # Calcula o total por valor de tag
                tag_values_summary = df_tags.groupby('Tag').agg({
                    'Cost_USD': 'sum',
                    'Cost_BRL': 'sum'
                }).sort_values('Cost_BRL', ascending=False)
                
                tag_total_brl = tag_values_summary['Cost_BRL'].sum()
                tag_total_usd = tag_values_summary['Cost_USD'].sum()
                total_cost_all_tags_brl += tag_total_brl
                total_cost_all_tags_usd += tag_total_usd
                
                tag_summaries.append({
                    'tag_key': tag_key,
                    'total_cost_brl': tag_total_brl,
                    'total_cost_usd': tag_total_usd,
                    'values': tag_values_summary
                })
        
        # Ordena as tags por custo total
        tag_summaries.sort(key=lambda x: x['total_cost_brl'], reverse=True)
        
        # Adiciona o total geral ao relatório
        report_content.append(f"\nCusto Total de Todos os Recursos Tagueados:")
        report_content.append(f"USD: ${total_cost_all_tags_usd:,.2f}")
        report_content.append(f"BRL: {self._format_brl(total_cost_all_tags_brl)}")
        report_content.append("\n=== Detalhamento por Tag ===")
        
        for summary in tag_summaries:
            tag_key = summary['tag_key']
            tag_total_brl = summary['total_cost_brl']
            tag_total_usd = summary['total_cost_usd']
            tag_percent = (tag_total_brl / total_cost_all_tags_brl * 100) if total_cost_all_tags_brl > 0 else 0
            
            report_content.append(f"\n\nTag: {tag_key}")
            report_content.append(f"Custo Total USD: ${tag_total_usd:,.2f}")
            report_content.append(f"Custo Total BRL: {self._format_brl(tag_total_brl)} ({tag_percent:.1f}% do total)")
            report_content.append("\nDetalhamento por valor:")
            
            # Formata o resumo dos valores da tag
            values_summary = summary['values'].copy()
            values_summary['Percentual'] = (values_summary['Cost_BRL'] / tag_total_brl * 100)
            values_summary['Cost_USD'] = values_summary['Cost_USD'].apply(lambda x: f"${x:,.2f}")
            values_summary['Cost_BRL'] = values_summary['Cost_BRL'].apply(self._format_brl)
            values_summary['Percentual'] = values_summary['Percentual'].apply(lambda x: f"{x:.1f}%")
            
            report_content.append(tabulate(values_summary.reset_index(), 
                         headers=['Valor da Tag', 'Custo (USD)', 'Custo (BRL)', 'Percentual'],
                         showindex=False))
        
        # Junta todo o conteúdo e salva
        final_report = '\n'.join(report_content)
        self._print_and_save(final_report, f"relatorio_tags_{start_date}_a_{end_date}")
        
        return {
            'total_cost_usd': total_cost_all_tags_usd,
            'total_cost_brl': total_cost_all_tags_brl,
            'tag_summaries': tag_summaries
        }

    def generate_report_by_specific_tag(self, tag_key, start_date=None, end_date=None, days=30):
        """
        Gera relatório detalhado para uma tag específica
        
        :param tag_key: Chave da tag para gerar o relatório
        :param start_date: Data de início no formato 'YYYY-MM-DD' (opcional)
        :param end_date: Data de fim no formato 'YYYY-MM-DD' (opcional)
        :param days: Número de dias para o relatório se start_date e end_date não forem fornecidos
        """
        # Se start_date e end_date não forem fornecidos, usa os últimos 'days' dias
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Obtém os custos por tag específica
        df_tag = self.get_cost_by_tag(start_date, end_date, tag_key)
        
        if df_tag.empty:
            message = f"\nNenhum custo encontrado para a tag {tag_key} no período."
            self._print_and_save(message, f"relatorio_tag_{tag_key}_vazio")
            return
        
        # Calcula o total de custos
        total_cost_brl = df_tag['Cost_BRL'].sum()
        total_cost_usd = df_tag['Cost_USD'].sum()
        
        # Prepara o conteúdo do relatório
        report_content = []
        report_content.append(f"=== Relatório Detalhado da Tag: {tag_key} ===")
        report_content.append(f"Período: {start_date} até {end_date}")
        report_content.append(f"Taxa de câmbio USD/BRL: {self.exchange_rate:.2f}")
        
        # Adiciona totais
        report_content.append(f"\nCusto Total USD: ${total_cost_usd:,.2f}")
        report_content.append(f"Custo Total BRL: {self._format_brl(total_cost_brl)}")
        
        # Agrupa por valores da tag
        tag_values_summary = df_tag.groupby('Tag').agg({
            'Cost_USD': 'sum',
            'Cost_BRL': 'sum'
        }).sort_values('Cost_BRL', ascending=False)
        
        # Adiciona percentuais
        tag_values_summary['Percentual'] = (tag_values_summary['Cost_BRL'] / total_cost_brl * 100)
        
        # Formata a tabela de resumo
        formatted_summary = tag_values_summary.copy()
        formatted_summary['Cost_USD'] = formatted_summary['Cost_USD'].apply(lambda x: f"${x:,.2f}")
        formatted_summary['Cost_BRL'] = formatted_summary['Cost_BRL'].apply(self._format_brl)
        formatted_summary['Percentual'] = formatted_summary['Percentual'].apply(lambda x: f"{x:.1f}%")
        
        report_content.append("\n=== Detalhamento por Valor da Tag ===")
        report_content.append(tabulate(formatted_summary.reset_index(), 
                      headers=['Valor da Tag', 'Custo (USD)', 'Custo (BRL)', 'Percentual'],
                      showindex=False))
        
        # Adiciona detalhamento por período
        df_tag['Month'] = pd.to_datetime(df_tag['Period']).dt.strftime('%Y-%m')
        monthly_summary = df_tag.groupby(['Month', 'Tag']).agg({
            'Cost_USD': 'sum',
            'Cost_BRL': 'sum'
        }).reset_index()
        
        report_content.append("\n=== Custos Mensais por Valor da Tag ===")
        for month in monthly_summary['Month'].unique():
            month_data = monthly_summary[monthly_summary['Month'] == month]
            report_content.append(f"\nMês: {month}")
            
            # Formata a tabela mensal
            month_summary = month_data.copy()
            month_summary['Cost_USD'] = month_summary['Cost_USD'].apply(lambda x: f"${x:,.2f}")
            month_summary['Cost_BRL'] = month_summary['Cost_BRL'].apply(self._format_brl)
            
            report_content.append(tabulate(month_summary[['Tag', 'Cost_USD', 'Cost_BRL']], 
                          headers=['Valor da Tag', 'Custo (USD)', 'Custo (BRL)'],
                          showindex=False))
        
        # Junta todo o conteúdo e salva
        final_report = '\n'.join(report_content)
        self._print_and_save(final_report, f"relatorio_tag_{tag_key}_{start_date}_a_{end_date}")
        
        return {
            'total_cost_usd': total_cost_usd,
            'total_cost_brl': total_cost_brl,
            'tag_values_summary': tag_values_summary
        }

if __name__ == '__main__':
    analyzer = AWSCostAnalyzer()
    
    # Exemplo de uso com datas específicas
    start_date = '2025-02-01'  # Primeiro dia do mês
    end_date = '2025-02-28'    # Último dia do mês
    
    # Gerar relatório geral por serviço
    analyzer.generate_cost_report_by_date(start_date, end_date)
    
    # Gerar relatório detalhado dos top 5 serviços
    analyzer.generate_top_services_detail_by_date(start_date, end_date)
    
    # Gerar relatório de custos por tag
    analyzer.generate_tag_report_by_date(start_date, end_date)
    
    # Exemplo de uso do novo método para uma tag específica
    # Você pode escolher qualquer tag disponível usando get_available_tags()
    tags = analyzer.get_available_tags()
    
    # Gera relatório para algumas tags de exemplo
    example_tags = ['Name', 'servers', 'application', 'biofaces']
    for tag in example_tags:
        analyzer.generate_report_by_specific_tag(tag, start_date, end_date)