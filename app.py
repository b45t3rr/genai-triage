#!/usr/bin/env python3
"""
PDF Report Analyzer

Aplicación para analizar reportes de seguridad en PDF usando LangChain y OpenAI.
Sigue principios de Clean Architecture y SOLID.

Uso:
    python app.py read --pdf archivo.pdf
    python app.py read --pdf archivo.pdf --output resultado.json
    python app.py test
    python app.py version

Autor: AI Assistant
Versión: 1.0.0
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.presentation.cli import app

if __name__ == "__main__":
    app()