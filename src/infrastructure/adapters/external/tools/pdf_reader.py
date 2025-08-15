import os
from typing import Dict, Any
from PyPDF2 import PdfReader
from src.domain.interfaces import PDFReaderInterface
from src.domain.entities import PDFDocument
from src.domain.exceptions import PDFNotFoundError, InvalidPDFError, PDFReadError


class PyPDF2Reader(PDFReaderInterface):
    """Implementación del lector de PDF usando PyPDF2."""
    
    def can_read(self, file_path: str) -> bool:
        """Verifica si puede leer el tipo de archivo."""
        return file_path.lower().endswith('.pdf') and os.path.exists(file_path)
    
    def read_document(self, file_path: str) -> Dict[str, Any]:
        """Lee un documento y retorna su contenido estructurado."""
        pdf_document = self.read_pdf(file_path)
        return {
            "file_path": pdf_document.file_path,
            "content": pdf_document.content,
            "metadata": pdf_document.metadata,
            "extracted_at": pdf_document.extracted_at.isoformat()
        }
    
    def read_pdf(self, file_path: str) -> PDFDocument:
        """Lee un archivo PDF y extrae su contenido."""
        if not os.path.exists(file_path):
            raise PDFNotFoundError(f"El archivo {file_path} no existe")
        
        if not file_path.lower().endswith('.pdf'):
            raise InvalidPDFError("El archivo debe tener extensión .pdf")
        
        try:
            reader = PdfReader(file_path)
            
            # Extraer texto de todas las páginas
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
            
            # Extraer metadata
            metadata = {
                "num_pages": len(reader.pages),
                "file_size": os.path.getsize(file_path),
                "file_name": os.path.basename(file_path)
            }
            
            # Agregar metadata del PDF si está disponible
            if reader.metadata:
                pdf_metadata = {
                    "title": reader.metadata.get('/Title', 'Desconocido'),
                    "author": reader.metadata.get('/Author', 'Desconocido'),
                    "subject": reader.metadata.get('/Subject', ''),
                    "creator": reader.metadata.get('/Creator', ''),
                    "producer": reader.metadata.get('/Producer', ''),
                    "creation_date": str(reader.metadata.get('/CreationDate', 'Desconocida')),
                    "modification_date": str(reader.metadata.get('/ModDate', 'Desconocida'))
                }
                metadata.update(pdf_metadata)
            
            return PDFDocument(
                file_path=file_path,
                content=content.strip(),
                metadata=metadata
            )
            
        except (PDFNotFoundError, InvalidPDFError):
            raise
        except Exception as e:
            raise PDFReadError(f"Error leyendo el archivo PDF: {str(e)}")