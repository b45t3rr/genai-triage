"""Cliente MongoDB para guardar resultados de análisis de PDFs."""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from src.domain.exceptions import PDFAnalyzerException


class MongoDBClient:
    """Cliente para operaciones con MongoDB."""
    
    def __init__(self, uri: Optional[str] = None, database_name: Optional[str] = None):
        """Inicializa el cliente MongoDB.
        
        Args:
            uri: URI de conexión a MongoDB
            database_name: Nombre de la base de datos
        """
        self.uri = uri or os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = database_name or os.getenv('DATABASE_NAME', 'vulnerability_validation')
        self.collection_name = os.getenv('COLLECTION_NAME', 'reports')
        self.client = None
        self.db = None
        self.collection = None
    
    def connect(self) -> bool:
        """Establece conexión con MongoDB.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Verificar conexión
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            raise PDFAnalyzerException(f"Error conectando a MongoDB: {str(e)}")
        except Exception as e:
            raise PDFAnalyzerException(f"Error inesperado conectando a MongoDB: {str(e)}")
    
    def disconnect(self):
        """Cierra la conexión con MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None
    
    def save_report(self, pdf_path: str, result_json: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Guarda un reporte de análisis en MongoDB.
        
        Args:
            pdf_path: Ruta del archivo PDF analizado
            result_json: Resultado del análisis en formato JSON
            metadata: Metadatos adicionales
        
        Returns:
            ID del documento insertado
        """
        if self.collection is None:
            raise PDFAnalyzerException("No hay conexión activa con MongoDB")
        
        try:
            # Parsear el JSON del resultado
            result_data = json.loads(result_json)
            
            # Crear documento para MongoDB
            document = {
                'source_file': os.path.basename(pdf_path),
                'full_path': pdf_path,
                'processed_at': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'structured_data': result_data,
                'metadata': metadata or {},
                'title': result_data.get('documento', {}).get('titulo', 'Documento sin título'),
                'summary': result_data.get('resumen_ejecutivo', 'Sin resumen disponible'),
                'content': result_json  # Guardar también el JSON completo
            }
            
            # Insertar documento
            result = self.collection.insert_one(document)
            return str(result.inserted_id)
            
        except json.JSONDecodeError as e:
            raise PDFAnalyzerException(f"Error parseando JSON del resultado: {str(e)}")
        except Exception as e:
            raise PDFAnalyzerException(f"Error guardando en MongoDB: {str(e)}")
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un reporte por su ID.
        
        Args:
            report_id: ID del reporte
        
        Returns:
            Documento del reporte o None si no existe
        """
        if not self.collection:
            raise PDFAnalyzerException("No hay conexión activa con MongoDB")
        
        try:
            from bson import ObjectId
            return self.collection.find_one({'_id': ObjectId(report_id)})
        except Exception as e:
            raise PDFAnalyzerException(f"Error obteniendo reporte: {str(e)}")
    
    def list_reports(self, limit: int = 10) -> list:
        """Lista los reportes más recientes.
        
        Args:
            limit: Número máximo de reportes a retornar
        
        Returns:
            Lista de reportes
        """
        if not self.collection:
            raise PDFAnalyzerException("No hay conexión activa con MongoDB")
        
        try:
            return list(self.collection.find().sort('created_at', -1).limit(limit))
        except Exception as e:
            raise PDFAnalyzerException(f"Error listando reportes: {str(e)}")
    
    def test_connection(self) -> bool:
        """Prueba la conexión con MongoDB.
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            self.connect()
            # Hacer una operación simple para verificar
            self.collection.find_one()
            return True
        except Exception:
            return False
        finally:
            self.disconnect()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()