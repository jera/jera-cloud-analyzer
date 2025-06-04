#!/usr/bin/env python3
"""
Setup configuration for Jera Cloud Analyzer CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Ler o README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Dependências definidas diretamente (sincronizadas com pyproject.toml)
requirements = [
    'boto3>=1.34.0',
    'click>=8.1.0',
    'rich>=13.7.0',
    'python-dateutil>=2.8.2',
    'requests>=2.31.0',
    'pydantic>=2.5.0',
    'mcp[cli]>=1.0.0',
    'starlette>=0.37.0',
    'uvicorn>=0.24.0',
    'haystack-ai>=2.8.0',
    'openai>=1.0.0',
    'pandas>=1.5.0',
    'python-dotenv>=1.0.0',
    'fastapi>=0.100.0',
    'fastmcp>=2.6.1',
    'botocore>=1.38.28',
    'numpy>=2.2.6',
    'urllib3>=2.4.0',
    'pyyaml>=6.0.2',
    'setuptools>=80.9.0',
    'wheel>=0.45.1',
    'diskcache>=5.6.3',
]

setup(
    name="cloud-analyzer",
    version="1.0.0",
    description="Jera Cloud Analyzer - Análise inteligente de custos AWS com IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jera Team",
    author_email="hospegadem@jera.com.br",
    url="https://github.com/jera/jera-cloud-analyzer",
    
    # Packages e módulos
    packages=find_packages(),
    py_modules=['cli'],
    include_package_data=True,
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=requirements,
    
    # Console scripts - entry point principal
    entry_points={
        'console_scripts': [
            'cloud-analyzer=cli:main',
        ],
    },
    
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    
    # Keywords for discovery
    keywords=[
        "aws", "cost", "analysis", "cloud", "insights", 
        "cli", "ai", "openai", "billing", "optimization"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/jera/jera-cloud-analyzer/issues",
        "Documentation": "https://github.com/jera/jera-cloud-analyzer/blob/main/README.md",
        "Source": "https://github.com/jera/jera-cloud-analyzer",
    },
    
    # Package data
    package_data={
        '': ['*.md', '*.txt', '*.yml', '*.yaml', 'env.example'],
    },
    
    # Additional metadata
    zip_safe=False,
) 