"""Herramientas de red para análisis dinámico de vulnerabilidades."""

import subprocess
import json
import tempfile
import os
import requests
import urllib3
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin, parse_qs
import shlex

# Deshabilitar advertencias SSL para pruebas de penetración
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NetworkTool:
    """Herramienta para realizar pruebas de red y explotación de vulnerabilidades."""
    
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.parsed_url = urlparse(target_url)
        self.base_host = self.parsed_url.netloc
        self.base_scheme = self.parsed_url.scheme
    
    def curl_request(self, curl_args: str) -> str:
        """Realiza una petición HTTP usando requests (simulando curl).
        
        Args:
            curl_args: Argumentos de curl (ej: '-X POST -H "Content-Type: application/json" -d "{\"test\":\"data\"}" /api/endpoint')
        """
        try:
            # Limpiar argumentos de comillas simples extra
            curl_args = curl_args.strip().strip("'")
            
            # Parsear argumentos de curl
            try:
                args_list = shlex.split(curl_args)
            except ValueError:
                # Fallback si shlex falla
                args_list = curl_args.split()
            
            # Valores por defecto
            method = 'GET'
            headers = {}
            data = None
            json_data = None
            params = None
            cookies = {}
            final_url = None
            
            # Parsear argumentos
            i = 0
            while i < len(args_list):
                arg = args_list[i]
                
                if arg == '-X' and i + 1 < len(args_list):
                    method = args_list[i + 1].upper()
                    i += 2
                elif arg == '-H' and i + 1 < len(args_list):
                    header = args_list[i + 1]
                    if ':' in header:
                        key, value = header.split(':', 1)
                        headers[key.strip()] = value.strip()
                    i += 2
                elif arg == '-d' and i + 1 < len(args_list):
                    data = args_list[i + 1]
                    # Si parece JSON, intentar parsearlo
                    if data.strip().startswith('{') and data.strip().endswith('}'):
                        try:
                            json_data = json.loads(data)
                            data = None
                        except json.JSONDecodeError:
                            pass
                    i += 2
                elif arg == '-b' and i + 1 < len(args_list):
                    # Parsear cookies
                    cookie_str = args_list[i + 1]
                    for cookie in cookie_str.split(';'):
                        if '=' in cookie:
                            key, value = cookie.split('=', 1)
                            cookies[key.strip()] = value.strip()
                    i += 2
                elif arg == '-v' or arg == '--verbose':
                    # Ignorar flag verbose
                    i += 1
                elif not arg.startswith('-'):
                    # Es la URL o endpoint
                    if arg.startswith('http'):
                        final_url = arg
                    else:
                        endpoint = arg.strip("'")
                        if endpoint.startswith('/'):
                            final_url = f"{self.target_url.rstrip('/')}{endpoint}"
                        else:
                            final_url = urljoin(self.target_url, endpoint)
                    i += 1
                else:
                    i += 1
            
            # Si no se encontró URL, usar target_url
            if not final_url:
                final_url = self.target_url
            
            print(f"    🌐 Ejecutando petición HTTP: {method} {final_url}")
            print(f"    📋 Headers: {headers}")
            if data:
                print(f"    📦 Data: {data[:100]}..." if len(str(data)) > 100 else f"    📦 Data: {data}")
            if json_data:
                print(f"    📦 JSON: {json_data}")
            
            # Realizar petición con requests
            session = requests.Session()
            session.verify = False  # Deshabilitar verificación SSL para pruebas
            
            response = session.request(
                method=method,
                url=final_url,
                headers=headers,
                data=data,
                json=json_data,
                params=params,
                cookies=cookies,
                timeout=30,
                allow_redirects=True
            )
            
            # Construir respuesta similar a curl
            response_headers = '\n'.join([f"{k}: {v}" for k, v in response.headers.items()])
            
            stdout = f"HTTP/{response.raw.version/10:.1f} {response.status_code} {response.reason}\n"
            stdout += response_headers + "\n\n"
            stdout += response.text
            
            return f"Status Code: 0\nHTTP Status: {response.status_code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n"
            
        except requests.exceptions.ConnectionError as e:
            return f"Status Code: 7\nError: No se pudo conectar al host\nURL: {final_url}\n\nSTDERR:\n{str(e)}"
        except requests.exceptions.Timeout as e:
            return f"Status Code: 28\nError: Timeout de operación\nURL: {final_url}\n\nSTDERR:\n{str(e)}"
        except requests.exceptions.RequestException as e:
            return f"Status Code: 3\nError: Error en la petición HTTP\nURL: {final_url}\n\nSTDERR:\n{str(e)}"
        except Exception as e:
            return f"Error ejecutando petición HTTP: {str(e)}"
    
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
            base_url = urljoin(self.target_url, endpoint)
            params = {parameter: payload}
            
            # Realizar petición con requests
            session = requests.Session()
            session.verify = False
            
            response = session.get(base_url, params=params, timeout=30)
            
            # Construir respuesta similar a curl
            response_headers = '\n'.join([f"{k}: {v}" for k, v in response.headers.items()])
            stdout = f"HTTP/{response.raw.version/10:.1f} {response.status_code} {response.reason}\n"
            stdout += response_headers + "\n\n"
            stdout += response.text
            
            return f"URL: {response.url}\nStatus Code: 0\nHTTP Status: {response.status_code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n"
            
        except requests.exceptions.RequestException as e:
            return f"Error en prueba SQL injection: {str(e)}"
        except Exception as e:
            return f"Error en prueba SQL injection: {str(e)}"
    
    def xss_test(self, endpoint: str, parameter: str, payload: str) -> str:
        """Prueba payloads de XSS."""
        try:
            # Construir URL con payload
            base_url = urljoin(self.target_url, endpoint)
            params = {parameter: payload}
            
            # Realizar petición con requests
            session = requests.Session()
            session.verify = False
            
            response = session.get(base_url, params=params, timeout=30)
            
            # Construir respuesta similar a curl
            response_headers = '\n'.join([f"{k}: {v}" for k, v in response.headers.items()])
            stdout = f"HTTP/{response.raw.version/10:.1f} {response.status_code} {response.reason}\n"
            stdout += response_headers + "\n\n"
            stdout += response.text
            
            return f"URL: {response.url}\nStatus Code: 0\nHTTP Status: {response.status_code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n"
            
        except requests.exceptions.RequestException as e:
            return f"Error en prueba XSS: {str(e)}"
        except Exception as e:
            return f"Error en prueba XSS: {str(e)}"
    
    def directory_traversal_test(self, endpoint: str, payload: str) -> str:
        """Prueba payloads de directory traversal."""
        try:
            # Construir URL con payload
            url = urljoin(self.target_url, endpoint + payload)
            
            # Realizar petición con requests
            session = requests.Session()
            session.verify = False
            
            response = session.get(url, timeout=30)
            
            # Construir respuesta similar a curl
            response_headers = '\n'.join([f"{k}: {v}" for k, v in response.headers.items()])
            stdout = f"HTTP/{response.raw.version/10:.1f} {response.status_code} {response.reason}\n"
            stdout += response_headers + "\n\n"
            stdout += response.text
            
            return f"URL: {url}\nStatus Code: 0\nHTTP Status: {response.status_code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n"
            
        except requests.exceptions.RequestException as e:
            return f"Error en prueba directory traversal: {str(e)}"
        except Exception as e:
            return f"Error en prueba directory traversal: {str(e)}"
    
    def command_injection_test(self, endpoint: str, parameter: str, payload: str) -> str:
        """Prueba payloads de command injection."""
        try:
            # Realizar petición POST con payload
            url = urljoin(self.target_url, endpoint)
            data = {parameter: payload}
            
            # Realizar petición con requests
            session = requests.Session()
            session.verify = False
            
            response = session.post(url, data=data, timeout=30)
            
            # Construir respuesta similar a curl
            response_headers = '\n'.join([f"{k}: {v}" for k, v in response.headers.items()])
            stdout = f"HTTP/{response.raw.version/10:.1f} {response.status_code} {response.reason}\n"
            stdout += response_headers + "\n\n"
            stdout += response.text
            
            return f"Endpoint: {endpoint}\nData: {data}\nStatus Code: 0\nHTTP Status: {response.status_code}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n"
            
        except requests.exceptions.RequestException as e:
            return f"Error en prueba command injection: {str(e)}"
        except Exception as e:
            return f"Error en prueba command injection: {str(e)}"
    
    def check_service_availability(self, url: Optional[str] = None) -> str:
        """Verifica si el servicio objetivo está disponible."""
        try:
            # Usar la URL proporcionada o la URL base
            target_url = url if url else self.target_url
            
            # Realizar petición HEAD con requests
            session = requests.Session()
            session.verify = False
            
            response = session.head(target_url, timeout=10)
            
            # Construir respuesta similar a curl
            response_headers = '\n'.join([f"{k}: {v}" for k, v in response.headers.items()])
            stdout = f"HTTP/{response.raw.version/10:.1f} {response.status_code} {response.reason}\n"
            stdout += response_headers
            
            return f"Servicio DISPONIBLE\n\nRespuesta:\n{stdout}"
                
        except requests.exceptions.RequestException as e:
            return f"Servicio NO DISPONIBLE\n\nError:\n{str(e)}"
        except Exception as e:
            return f"Error verificando disponibilidad: {str(e)}"