"""Herramienta para leer archivos de código fuente."""

import os
from typing import Optional


class FileReaderTool:
    """Herramienta mejorada para leer archivos de código fuente."""
    
    def __init__(self, source_path: str):
        self.source_path = source_path
    
    def read_file_smart(self, query: str) -> str:
        """Lee archivos de forma inteligente basado en la consulta."""
        parts = query.split(',')
        file_path = parts[0].strip()
        
        start_line = None
        end_line = None
        
        if len(parts) == 3:
            try:
                start_line = int(parts[1].strip())
                end_line = int(parts[2].strip())
            except ValueError:
                pass
        
        return self.read_file(file_path, start_line, end_line)
    
    def read_file(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """Lee un archivo específico o un rango de líneas."""
        try:
            # Limpiar y normalizar la ruta del archivo
            clean_file_path = file_path.strip()
            
            # Construir ruta completa
            if not os.path.isabs(clean_file_path):
                full_path = os.path.join(self.source_path, clean_file_path)
            else:
                full_path = clean_file_path
            
            # Intentar múltiples variaciones de la ruta si no existe
            possible_paths = [full_path]
            
            # Si la ruta original no existe, intentar variaciones más inteligentes
            if not os.path.exists(full_path):
                # 1. Si contiene subdirectorios anidados, intentar extraer la parte más relevante
                path_parts = clean_file_path.split('/')
                
                # 2. Buscar cualquier directorio que coincida con las partes de la ruta
                for part in path_parts[:-1]:  # Excluir el nombre del archivo
                    if part:  # Evitar partes vacías
                        for root, dirs, files in os.walk(self.source_path):
                            if part in dirs:
                                # Encontrar la posición de esta parte en la ruta original
                                if part in path_parts:
                                    part_index = path_parts.index(part)
                                    remaining_path = '/'.join(path_parts[part_index:])
                                    candidate_path = os.path.join(root, remaining_path)
                                    if os.path.exists(candidate_path):
                                        possible_paths.append(candidate_path)
                                break  # Solo necesitamos la primera coincidencia por directorio
                
                # 3. Si hay múltiples niveles de anidamiento, intentar desde diferentes puntos
                if len(path_parts) > 2:
                    for i in range(1, len(path_parts)):
                        partial_path = '/'.join(path_parts[i:])
                        possible_paths.append(os.path.join(self.source_path, partial_path))
                
                # 4. Buscar el archivo por nombre en todo el árbol de directorios
                filename = os.path.basename(clean_file_path)
                for root, dirs, files in os.walk(self.source_path):
                    if filename in files:
                        candidate_path = os.path.join(root, filename)
                        # Verificar que la ruta candidata tenga sentido contextualmente
                        if any(part in candidate_path for part in path_parts[:-1]):
                            possible_paths.append(candidate_path)
            
            # Intentar encontrar el archivo en cualquiera de las rutas posibles
            working_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    working_path = path
                    break
            
            if working_path is None:
                return f"Error: Archivo {file_path} no encontrado en ninguna de las rutas: {possible_paths[:5]}"  # Limitar salida
            
            with open(working_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if start_line is not None and end_line is not None:
                # Leer rango específico (1-indexed)
                start_idx = max(0, start_line - 1)
                end_idx = min(len(lines), end_line)
                content = ''.join(lines[start_idx:end_idx])
                return f"Archivo: {file_path} (líneas {start_line}-{end_line})\n{content}"
            else:
                # Leer archivo completo sin limitación de caracteres
                content = ''.join(lines)
                return f"Archivo: {file_path}\n{content}"
                
        except Exception as e:
            return f"Error leyendo archivo {file_path}: {str(e)}"
    
    def find_files_by_pattern(self, pattern: str) -> str:
        """Encuentra archivos que coincidan con un patrón e incluye números de línea."""
        matching_files = []
        pattern_lower = pattern.lower()
        
        try:
            for root, dirs, files in os.walk(self.source_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.php', '.java', '.rb', '.go', '.ts', '.jsx', '.tsx')):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.source_path)
                        
                        # Buscar patrón en nombre de archivo
                        if pattern_lower in file.lower() or pattern_lower in rel_path.lower():
                            matching_files.append(f"{rel_path} (en nombre de archivo)")
                        elif len(matching_files) < 10:  # Limitar búsqueda en contenido
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    lines = f.readlines()
                                    
                                    # Buscar patrón en cada línea y registrar números de línea
                                    line_matches = []
                                    for line_num, line in enumerate(lines, 1):
                                        if pattern_lower in line.lower():
                                            line_matches.append(str(line_num))
                                            if len(line_matches) >= 5:  # Limitar a 5 coincidencias por archivo
                                                break
                                    
                                    if line_matches:
                                        lines_info = ", ".join(line_matches)
                                        if len(line_matches) >= 5:
                                            lines_info += "..."
                                        matching_files.append(f"{rel_path} (líneas: {lines_info})")
                            except:
                                continue
                
                if len(matching_files) >= 15:  # Limitar resultados
                    break
            
            if matching_files:
                return f"Archivos encontrados para '{pattern}':\n" + "\n".join(matching_files[:15])
            else:
                return f"No se encontraron archivos para el patrón '{pattern}'"
                
        except Exception as e:
            return f"Error buscando archivos: {str(e)}"