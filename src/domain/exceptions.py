"""Excepciones personalizadas del dominio."""


class PDFAnalyzerException(Exception):
    """Excepción base para el analizador de PDF."""
    pass


class PDFReadError(PDFAnalyzerException):
    """Error al leer un archivo PDF."""
    pass


class PDFNotFoundError(PDFAnalyzerException):
    """Archivo PDF no encontrado."""
    pass


class InvalidPDFError(PDFAnalyzerException):
    """Archivo PDF inválido o corrupto."""
    pass


class ReportAnalysisError(PDFAnalyzerException):
    """Error al analizar el reporte."""
    pass


class LLMConnectionError(PDFAnalyzerException):
    """Error de conexión con el modelo de lenguaje."""
    pass


class InvalidConfigurationError(PDFAnalyzerException):
    """Error de configuración inválida."""
    pass


class JSONParsingError(PDFAnalyzerException):
    """Error al parsear JSON generado por el LLM."""
    pass