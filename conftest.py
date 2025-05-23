"""
Arquivo para ajustar o PYTHONPATH e garantir importações corretas.
"""
import os
import sys

# Adiciona o diretório raiz ao path para permitir importações relativas
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))) 