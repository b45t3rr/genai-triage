"""Herramientas de red para análisis dinámico de vulnerabilidades."""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin


class NetworkTool:
    """Herramienta para realizar pruebas de red y explotación de vulnerabilidades."""
    
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.parsed_url = urlparse(target_url)
        self.base_host = self.parsed_url.netloc
        self.base_scheme = self.parsed_url.scheme
    
    def curl_request(self, curl_args: str) -> str:
        """Realiza una petición HTTP usando curl con argumentos nativos.
        
        Args:
            curl_args: Argumentos de curl (ej: '-X POST -H "Content-Type: application/json" -d "{\"test\":\"data\"}" /api/endpoint')
        """
        try:
            # Limpiar argumentos de comillas simples extra
            curl_args = curl_args.strip().strip("'")
            
            # Si no se proporciona URL completa, construir con target_url
            import shlex
            try:
                args_list = shlex.split(curl_args)
            except ValueError:
                # Fallback si shlex falla
                args_list = curl_args.split()
            
            url_found = False
            final_url = None
            
            # Buscar si hay una URL completa en los argumentos
            for i, arg in enumerate(args_list):
                if arg.startswith('http'):
                    url_found = True
                    final_url = arg
                    break
                elif not arg.startswith('-') and i == len(args_list) - 1:
                    # El último argumento que no empieza con - es probablemente el endpoint
                    if arg.startswith('/'):
                        final_url = f"{self.target_url.rstrip('/')}{arg}"
                    else:
                        final_url = urljoin(self.target_url, arg)
                    args_list[i] = final_url
                    break
            
            # Si no se encontró URL, agregar target_url al final
            if not url_found and not final_url:
                final_url = self.target_url
                args_list.append(final_url)
            
            print(f"    🌐 Ejecutando: curl {curl_args}")
            print(f"    🎯 URL final: {final_url}")
            
            # Construir comando curl con argumentos base
            cmd = ['curl', '-s', '-i', '--max-time', '30', '--connect-timeout', '10'] + args_list
            
            # Ejecutar comando
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Interpretar códigos de error de curl
            if result.returncode == 0:
                # Extraer código de estado HTTP del output
                lines = result.stdout.split('\n')
                http_status = "200"  # Default
                for line in lines:
                    if line.startswith('HTTP/'):
                        parts = line.split()
                        if len(parts) >= 2:
                            http_status = parts[1]
                        break
                return f"Status Code: 0\nHTTP Status: {http_status}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            elif result.returncode == 3:
                return f"Status Code: 3\nError: URL malformada o problema de resolución DNS\nComando: curl {' '.join(cmd[1:])}\n\nSTDERR:\n{result.stderr}"
            elif result.returncode == 6:
                return f"Status Code: 6\nError: No se pudo resolver el host\nComando: curl {' '.join(cmd[1:])}\n\nSTDERR:\n{result.stderr}"
            elif result.returncode == 7:
                return f"Status Code: 7\nError: No se pudo conectar al host\nComando: curl {' '.join(cmd[1:])}\n\nSTDERR:\n{result.stderr}"
            elif result.returncode == 28:
                return f"Status Code: 28\nError: Timeout de operación\nComando: curl {' '.join(cmd[1:])}\n\nSTDERR:\n{result.stderr}"
            else:
                return f"Status Code: {result.returncode}\nError curl desconocido\nComando: curl {' '.join(cmd[1:])}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except subprocess.TimeoutExpired:
            return "Error: Timeout en la petición curl"
        except Exception as e:
            return f"Error ejecutando curl: {str(e)}"
    
    def wget_download(self, endpoint: str = "", output_file: Optional[str] = None, params: Optional[str] = None) -> str:
        """Descarga archivos usando wget."""
        try:
            # Construir URL completa
            if endpoint.startswith('http'):
                url = endpoint
            else:
                url = urljoin(self.target_url, endpoint)
            
            # Construir comando wget
            cmd = ['wget', '--timeout=30', '--tries=3', '-q']
            
            # Agregar archivo de salida
            if output_file:
                cmd.extend(['-O', output_file])
            else:
                cmd.append('-O-')  # Output a stdout
            
            # Agregar parámetros adicionales
            if params:
                cmd.extend(params.split())
            
            # Agregar URL
            cmd.append(url)
            
            # Ejecutar comando
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return f"Status Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except subprocess.TimeoutExpired:
            return "Error: Timeout en la descarga wget"
        except Exception as e:
            return f"Error ejecutando wget: {str(e)}"
    
    def nmap_scan(self, scan_type: str = "basic", ports: Optional[str] = None) -> str:
        """Realiza escaneo de puertos usando nmap."""
        try:
            host = self.base_host.split(':')[0]  # Remover puerto si existe
            
            # Construir comando nmap
            cmd = ['nmap']
            
            if scan_type == "basic":
                cmd.extend(['-sS', '-O', '-sV'])
            elif scan_type == "fast":
                cmd.extend(['-F'])
            elif scan_type == "comprehensive":
                cmd.extend(['-sS', '-sU', '-O', '-sV', '-sC'])
            elif scan_type == "vuln":
                cmd.extend(['--script=vuln'])
            
            # Agregar puertos específicos
            if ports:
                cmd.extend(['-p', ports])
            
            # Agregar host
            cmd.append(host)
            
            # Ejecutar comando
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return f"Status Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except subprocess.TimeoutExpired:
            return "Error: Timeout en el escaneo nmap"
        except Exception as e:
            return f"Error ejecutando nmap: {str(e)}"
    
    def ping_host(self, host: Optional[str] = None, count: int = 4) -> str:
        """Realiza ping al host objetivo."""
        try:
            # Usar el host proporcionado o el host base
            target_host = host if host else self.base_host.split(':')[0]
            
            cmd = ['ping', '-c', str(count), target_host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return f"Status Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except subprocess.TimeoutExpired:
            return "Error: Timeout en ping"
        except Exception as e:
            return f"Error ejecutando ping: {str(e)}"
    
    def telnet_connect(self, port: int = 80, timeout: int = 10) -> str:
        """Intenta conexión telnet al host y puerto especificado."""
        try:
            host = self.base_host.split(':')[0]
            
            # Usar timeout command para limitar la conexión telnet
            cmd = ['timeout', str(timeout), 'telnet', host, str(port)]
            result = subprocess.run(cmd, capture_output=True, text=True, input='\n')
            
            return f"Status Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except Exception as e:
            return f"Error ejecutando telnet: {str(e)}"
    
    def netcat_connect(self, port: int, data: Optional[str] = None, timeout: int = 10) -> str:
        """Realiza conexión usando netcat."""
        try:
            host = self.base_host.split(':')[0]
            
            cmd = ['nc', '-w', str(timeout), host, str(port)]
            
            input_data = data if data else '\n'
            result = subprocess.run(cmd, capture_output=True, text=True, input=input_data, timeout=timeout + 5)
            
            return f"Status Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except subprocess.TimeoutExpired:
            return "Error: Timeout en conexión netcat"
        except Exception as e:
            return f"Error ejecutando netcat: {str(e)}"
    
    def sql_injection_test(self, endpoint: str, parameter: str, payload: str) -> str:
        """Prueba payloads de SQL injection."""
        try:
            # Construir URL con payload
            if '?' in endpoint:
                url = f"{urljoin(self.target_url, endpoint)}&{parameter}={payload}"
            else:
                url = f"{urljoin(self.target_url, endpoint)}?{parameter}={payload}"
            
            # Realizar petición
            cmd = ['curl', '-s', '-i', '--max-time', '30', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return f"URL: {url}\nStatus Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except Exception as e:
            return f"Error en prueba SQL injection: {str(e)}"
    
    def xss_test(self, endpoint: str, parameter: str, payload: str) -> str:
        """Prueba payloads de XSS."""
        try:
            # Construir URL con payload
            if '?' in endpoint:
                url = f"{urljoin(self.target_url, endpoint)}&{parameter}={payload}"
            else:
                url = f"{urljoin(self.target_url, endpoint)}?{parameter}={payload}"
            
            # Realizar petición
            cmd = ['curl', '-s', '-i', '--max-time', '30', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return f"URL: {url}\nStatus Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except Exception as e:
            return f"Error en prueba XSS: {str(e)}"
    
    def directory_traversal_test(self, endpoint: str, payload: str) -> str:
        """Prueba payloads de directory traversal."""
        try:
            # Construir URL con payload
            url = urljoin(self.target_url, endpoint + payload)
            
            # Realizar petición
            cmd = ['curl', '-s', '-i', '--max-time', '30', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return f"URL: {url}\nStatus Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except Exception as e:
            return f"Error en prueba directory traversal: {str(e)}"
    
    def command_injection_test(self, endpoint: str, parameter: str, payload: str) -> str:
        """Prueba payloads de command injection."""
        try:
            # Realizar petición POST con payload
            data = f"{parameter}={payload}"
            
            cmd = ['curl', '-s', '-i', '--max-time', '30', '-X', 'POST', 
                   '-d', data, urljoin(self.target_url, endpoint)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return f"Endpoint: {endpoint}\nData: {data}\nStatus Code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
        except Exception as e:
            return f"Error en prueba command injection: {str(e)}"
    
    def check_service_availability(self, url: Optional[str] = None) -> str:
        """Verifica si el servicio objetivo está disponible."""
        try:
            # Usar la URL proporcionada o la URL base
            target_url = url if url else self.target_url
            
            # Realizar petición básica
            cmd = ['curl', '-s', '-I', '--max-time', '10', target_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return f"Servicio DISPONIBLE\n\nRespuesta:\n{result.stdout}"
            else:
                return f"Servicio NO DISPONIBLE\n\nError:\n{result.stderr}"
                
        except Exception as e:
            return f"Error verificando disponibilidad: {str(e)}"