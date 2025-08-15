"""Herramienta para análisis de código usando Semgrep."""

import subprocess
import json
import os
from typing import Dict, Any, List


class SemgrepAnalyzerTool:
    """Herramienta para análisis de código usando Semgrep."""
    
    def __init__(self, source_path: str):
        self.source_path = source_path
    
    def analyze_code_pattern(self, query: str) -> str:
        """Analiza patrones de código usando Semgrep."""
        try:
            # Parsear la consulta para extraer el patrón y el lenguaje
            parts = query.split(',', 1)
            if len(parts) != 2:
                return "Error: Formato incorrecto. Use: 'patrón,lenguaje' (ej: 'eval(...),python')"
            
            pattern = parts[0].strip()
            language = parts[1].strip().lower()
            
            # Mapear lenguajes comunes
            lang_map = {
                'python': 'python',
                'py': 'python',
                'javascript': 'javascript',
                'js': 'javascript',
                'php': 'php',
                'java': 'java',
                'go': 'go',
                'ruby': 'ruby',
                'rb': 'ruby',
                'typescript': 'typescript',
                'ts': 'typescript'
            }
            
            semgrep_lang = lang_map.get(language, language)
            
            # Crear regla temporal de Semgrep
            rule = {
                "rules": [{
                    "id": "custom-pattern-search",
                    "pattern": pattern,
                    "message": f"Patrón encontrado: {pattern}",
                    "languages": [semgrep_lang],
                    "severity": "INFO"
                }]
            }
            
            # Escribir regla temporal
            rule_file = os.path.join(self.source_path, '.semgrep_temp_rule.yml')
            with open(rule_file, 'w') as f:
                import yaml
                yaml.dump(rule, f)
            
            try:
                # Ejecutar Semgrep
                cmd = [
                    'semgrep',
                    '--config', rule_file,
                    '--json',
                    '--no-git-ignore',
                    self.source_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    try:
                        findings = json.loads(result.stdout)
                        return self._format_semgrep_results(findings, pattern)
                    except json.JSONDecodeError:
                        return f"Semgrep ejecutado pero no se pudo parsear JSON: {result.stdout}"
                else:
                    return f"Error ejecutando Semgrep: {result.stderr}"
                    
            finally:
                # Limpiar archivo temporal
                if os.path.exists(rule_file):
                    os.remove(rule_file)
                    
        except subprocess.TimeoutExpired:
            return "Error: Timeout ejecutando Semgrep (>30s)"
        except ImportError:
            return "Error: PyYAML no está instalado. Instale con: pip install PyYAML"
        except Exception as e:
            return f"Error en análisis de patrones: {str(e)}"
    
    def _format_semgrep_results(self, findings: Dict[str, Any], pattern: str) -> str:
        """Formatea los resultados de Semgrep."""
        if not findings.get('results'):
            return f"No se encontraron coincidencias para el patrón: {pattern}"
        
        results = findings['results']
        formatted_results = []
        
        for result in results[:10]:  # Limitar a 10 resultados
            file_path = result.get('path', 'Desconocido')
            start_line = result.get('start', {}).get('line', 'N/A')
            end_line = result.get('end', {}).get('line', 'N/A')
            code = result.get('extra', {}).get('lines', 'Código no disponible')
            
            # Hacer la ruta relativa al directorio fuente
            rel_path = os.path.relpath(file_path, self.source_path) if os.path.isabs(file_path) else file_path
            
            formatted_results.append(
                f"📍 {rel_path}:{start_line}-{end_line}\n"
                f"```\n{code}\n```\n"
            )
        
        summary = f"🔍 Encontradas {len(results)} coincidencias para '{pattern}':\n\n"
        return summary + "\n".join(formatted_results)
    
    def run_security_scan(self) -> str:
        """Ejecuta un escaneo de seguridad completo usando reglas predefinidas de Semgrep."""
        try:
            cmd = [
                'semgrep',
                '--config=auto',
                '--json',
                '--no-git-ignore',
                self.source_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                try:
                    findings = json.loads(result.stdout)
                    return self._format_security_results(findings)
                except json.JSONDecodeError:
                    return f"Escaneo ejecutado pero no se pudo parsear JSON: {result.stdout}"
            else:
                return f"Error ejecutando escaneo de seguridad: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Timeout ejecutando escaneo de seguridad (>60s)"
        except Exception as e:
            return f"Error en escaneo de seguridad: {str(e)}"
    
    def _format_security_results(self, findings: Dict[str, Any]) -> str:
        """Formatea los resultados del escaneo de seguridad."""
        if not findings.get('results'):
            return "✅ No se encontraron problemas de seguridad."
        
        results = findings['results']
        
        # Agrupar por severidad
        by_severity = {'ERROR': [], 'WARNING': [], 'INFO': []}
        
        for result in results:
            severity = result.get('extra', {}).get('severity', 'INFO')
            by_severity.setdefault(severity, []).append(result)
        
        formatted_results = []
        
        for severity in ['ERROR', 'WARNING', 'INFO']:
            if by_severity[severity]:
                icon = {'ERROR': '🚨', 'WARNING': '⚠️', 'INFO': 'ℹ️'}[severity]
                formatted_results.append(f"\n{icon} {severity} ({len(by_severity[severity])} problemas):")
                
                for result in by_severity[severity][:5]:  # Limitar a 5 por severidad
                    file_path = result.get('path', 'Desconocido')
                    line = result.get('start', {}).get('line', 'N/A')
                    message = result.get('extra', {}).get('message', 'Sin mensaje')
                    rule_id = result.get('check_id', 'unknown-rule')
                    
                    rel_path = os.path.relpath(file_path, self.source_path) if os.path.isabs(file_path) else file_path
                    
                    formatted_results.append(
                        f"  📍 {rel_path}:{line}\n"
                        f"     {message} ({rule_id})"
                    )
        
        total_issues = len(results)
        summary = f"🔒 Escaneo de seguridad completado - {total_issues} problemas encontrados:\n"
        
        return summary + "\n".join(formatted_results)