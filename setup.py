#!/usr/bin/env python3
"""
Setup configuration for Cloud Insights CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Ler o README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Ler requirements do arquivo
requirements_file = this_directory / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('='):
                # Remove comentários inline
                req = line.split('#')[0].strip()
                if req:
                    requirements.append(req)

# Requirements mínimos caso o arquivo não exista
if not requirements:
    requirements = [
        'openai>=1.0.0',
        'boto3>=1.26.0',
        'haystack-ai>=2.0.0',
        'python-dotenv>=0.19.0',
        'pandas>=1.5.0',
        'numpy>=1.24.0',
        'requests>=2.28.0',
        'python-dateutil>=2.8.0'
    ]

setup(
    name="cloud-insights",
    version="1.0.0",
    description="🔍 Análise inteligente de custos AWS com IA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Cloud Insights Team",
    author_email="contact@cloudinsights.dev",
    url="https://github.com/your-org/cloud-insights",
    
    # Packages e módulos
    packages=find_packages(include=['src', 'src.*']),
    py_modules=['cli'],
    include_package_data=True,
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=requirements,
    
    # Console scripts - entry point principal
    entry_points={
        'console_scripts': [
            'cloud-insights=cli:main',
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
        "Bug Reports": "https://github.com/your-org/cloud-insights/issues",
        "Documentation": "https://github.com/your-org/cloud-insights/blob/main/README.md",
        "Source": "https://github.com/your-org/cloud-insights",
    },
    
    # Package data
    package_data={
        '': ['*.md', '*.txt', '*.yml', '*.yaml', 'env.example'],
    },
    
    # Additional metadata
    zip_safe=False,
) 