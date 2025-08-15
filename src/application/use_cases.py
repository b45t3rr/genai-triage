"""Casos de uso de la aplicación - Compatibilidad hacia atrás.

Este archivo mantiene compatibilidad con el código existente importando
los casos de uso desde su nueva ubicación modularizada.
"""

# Importar desde la nueva estructura modularizada
from .use_cases import (
    ReadPDFUseCase as ReadPDFReportUseCase,  # Mantener nombre original para compatibilidad
    TriageVulnerabilitiesUseCase,
    CompleteSecurityAnalysisUseCase
)

# Re-exportar para mantener compatibilidad
__all__ = [
    "ReadPDFReportUseCase",
    "TriageVulnerabilitiesUseCase", 
    "CompleteSecurityAnalysisUseCase"
]