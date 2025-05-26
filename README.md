# 🔍 Jera Cloud Analyzer CLI

> **Análise inteligente de custos AWS com IA**

O Jera Cloud Analyzer é uma ferramenta CLI avançada que utiliza Inteligência Artificial para analisar, otimizar e fornecer insights sobre seus custos e recursos AWS de forma conversacional e intuitiva.

## ✨ **Características Principais**

- 🤖 **IA Conversacional**: Faça perguntas em linguagem natural sobre seus custos AWS
- 📊 **24 Ferramentas Especializadas**: Análise completa de custos, performance e governança
- 🔍 **Resolução Inteligente**: Sistema híbrido que resolve automaticamente nomes de serviços AWS
- 🚀 **Interface Simples**: CLI minimalista com comando único
- 💰 **Análise de Custos**: Cost Explorer integration com insights avançados
- 📈 **Monitoramento Performance**: CloudWatch metrics e análise de utilização
- 🏷️ **Auditoria de Governança**: Verificação de tags e compliance
- 🔮 **Previsões**: Estimativas de custos futuros baseadas em IA
- 🔑 **Autenticação Simplificada**: AWS SSO e variáveis de ambiente

## 🚀 **Instalação Rápida**

### **1. Clone o Repositório**
```bash
git clone https://github.com/jera/jera-cloud-analyzer
cd jera-cloud-analyzer
```

### **2. Instale Automaticamente**
```bash
./install.sh
```

### **3. Configure apenas a OpenAI API Key**
```bash
# Edite o arquivo .env (será criado automaticamente)
nano .env

# Adicione apenas:
OPENAI_API_KEY=sk-your-openai-api-key-here
```

> **💡 As credenciais AWS são detectadas automaticamente!**

## 🔑 **Configuração de Credenciais**

O Jera Cloud Analyzer usa uma **estratégia simplificada** para credenciais AWS:

### **🥇 Opção 1: Variáveis de Ambiente (Recomendado)**
```bash
# Adicione ao .env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# Ou export direto
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

### **🥈 Opção 2: AWS SSO (inclui jera-cli)**
```bash
# Se você usa jera-cli
jera-cli auth login

# Ou AWS SSO nativo
aws sso configure
aws sso login --profile seu-perfil
```

## 📖 **Uso**

### **Comando Básico**
```bash
cloud-insights -q "Sua pergunta sobre AWS"
```

### **Exemplos Práticos**

```bash
# Análise de custos
cloud-insights -q "Quais são os top 5 serviços mais caros?"
cloud-insights -q "Qual foi o custo do RDS no último mês?"
cloud-insights -q "Compare custos de storage S3 vs EBS"

# Performance e otimização
cloud-insights -q "Quais instâncias EC2 estão subutilizadas?"
cloud-insights -q "Analise o tráfego de rede das instâncias EC2"
cloud-insights -q "Mostre métricas CPU da instância Valhalla"

# Governança e compliance
cloud-insights -q "Audite recursos sem tags de governança"
cloud-insights -q "Encontre instâncias EC2 por tag Environment"
cloud-insights -q "Quais recursos não seguem as políticas de naming?"

# Previsões e insights
cloud-insights -q "Preveja o custo para o próximo mês"
cloud-insights -q "Qual serviço teve maior crescimento nos últimos 3 meses?"
```

### **Comandos de Ajuda**

```bash
# Ver exemplos de consultas
cloud-insights --examples

# Ver versão e capacidades
cloud-insights --version

# Ajuda completa
cloud-insights --help
```

## 🛠️ **Capacidades Avançadas**

### **🔍 Resolução Inteligente de Serviços**
```bash
# Funciona com nomes populares
cloud-insights -q "Custo do rds"           # → Amazon Relational Database Service
cloud-insights -q "Análise do ec2"        # → Amazon Elastic Compute Cloud
cloud-insights -q "Storage do s3"         # → Amazon Simple Storage Service

# Tolerante a typos
cloud-insights -q "Custo do databse"      # → database services
cloud-insights -q "Analise cloudwtch"     # → CloudWatch
```

### **📊 Análise Multi-dimensional**
- **Custos por Serviço**: Breakdown detalhado por service/categoria
- **Custos por Período**: Análise temporal (dia, semana, mês, trimestre)
- **Custos por Tag**: Segmentação por departamento, projeto, ambiente
- **Previsões IA**: Machine learning para estimativas futuras

### **🎯 Monitoramento Inteligente**
- **CPU, Memória, Rede**: Métricas de performance em tempo real
- **Utilização vs Capacidade**: Identify overprovisioning
- **Trends e Anomalias**: Padrões de uso e alertas proativos

## 🔧 **Configuração Avançada**

### **Permissões IAM Mínimas**
Seu usuário AWS precisa das seguintes permissões:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetDimensionValues",
                "ce:GetTags",
                "ce:GetCostForecast",
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics",
                "ec2:DescribeInstances",
                "ec2:DescribeVolumes",
                "ec2:DescribeAddresses"
            ],
            "Resource": "*"
        }
    ]
}
```

**💡 Recomendação**: Use a política `ReadOnlyAccess` para acesso completo e seguro.

### **🏢 Integração com Jera CLI**

O Jera Cloud Analyzer detecta automaticamente sessões do `jera-cli`:

```bash
# 1. Faça login na Jera
jera-cli auth login

# 2. Use o Jera Cloud Analyzer normalmente
cloud-insights -q "Análise de custos"
```

### **🔄 Detecção Automática de Credenciais**

O CLI verifica credenciais nesta ordem:

1. **🌍 Variáveis de Ambiente** - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (incluindo .env)
2. **🔐 AWS SSO** - Sessões ativas (jera-cli, aws sso)

## 🏗️ **Arquitetura**

```
cloud-insights/
├── cli.py                     # 🚀 CLI principal com detecção automática
├── src/
│   ├── ia/
│   │   ├── agent.py          # 🤖 Agente principal
│   │   └── tools/            # 🛠️ 24 ferramentas especializadas
│   └── clouds/aws/           # ☁️ Integrações AWS
├── setup.py                  # 📦 Configuração do pacote
├── env.example               # ⚙️ Template de configuração
└── README.md                 # 📖 Documentação
```

### **🧠 Sistema de IA**
- **LangChain + OpenAI**: Processamento de linguagem natural
- **Haystack AI**: Orquestração de ferramentas e agentes
- **Resolução Híbrida**: Mapeamento + discovery + fuzzy search
- **Cache Inteligente**: TTL de 24h para otimização de performance

### **🔑 Sistema de Autenticação**
- **Detecção Automática**: Testa 2 fontes automaticamente
- **Priorização Inteligente**: Variáveis de ambiente > AWS SSO
- **Feedback Claro**: Mostra qual método foi detectado
- **Configuração Simples**: Apenas .env ou AWS SSO necessários

## 📊 **24 Ferramentas Disponíveis**

| Categoria | Ferramentas | Descrição |
|-----------|-------------|-----------|
| **💰 Cost Explorer** | 8 tools | Análise detalhada de custos AWS |
| **📈 CloudWatch** | 6 tools | Métricas e monitoramento de performance |
| **🖥️ EC2 Management** | 6 tools | Gestão e análise de instâncias |
| **🔍 Service Resolution** | 4 tools | Resolução inteligente de serviços |

## 🔄 **Desenvolvimento**

### **Executar em Modo de Desenvolvimento**
```bash
# Executar diretamente
python3 cli.py -q "Sua pergunta"

# Ou instalar em modo editável
pip install -e .
cloud-insights -q "Sua pergunta"
```

### **Testes**
```bash
# Testar configuração
cloud-insights --version

# Testar exemplos
cloud-insights --examples

# Testar consulta simples
cloud-insights -q "Olá, você está funcionando?"
```

## 📈 **Performance**

- **⚡ Cache Inteligente**: Respostas instantâneas para serviços conhecidos
- **🔍 Discovery Otimizado**: Carregamento único de serviços da conta
- **🚀 Processamento Paralelo**: Múltiplas consultas AWS simultâneas
- **💾 Persistência Local**: Cache TTL de 24h para reduzir latência
- **🔑 Autenticação Eficiente**: Reutiliza sessões AWS existentes

## 🤝 **Contribuindo**

1. **Fork** o repositório
2. **Crie** uma branch para sua feature (`git checkout -b feature/amazing-feature`)
3. **Commit** suas mudanças (`git commit -m 'Add amazing feature'`)
4. **Push** para a branch (`git push origin feature/amazing-feature`)
5. **Abra** um Pull Request

## 📝 **Licença**

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 **Suporte**

- 📧 **Email**: contact@cloudinsights.dev
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/cloud-insights/issues)
- 📖 **Docs**: [Documentation](https://github.com/your-org/cloud-insights/blob/main/README.md)

---

**🚀 Feito com ❤️ para otimizar seus custos AWS**  
**🔗 Integrado perfeitamente com jera-cli e AWS SSO**