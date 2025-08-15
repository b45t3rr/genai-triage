"""Loading spinner utility for CLI operations."""

import time
import threading


class LoadingSpinner:
    """Animación de carga personalizada con símbolos giratorios."""
    
    def __init__(self, message: str = "Procesando..."):
        self.message = message
        self.spinner_chars = ['|', '/', '—', '\\']
        self.running = False
        self.thread = None
        self.current_char_index = 0
    
    def _spin(self):
        """Ejecuta la animación en un hilo separado."""
        while self.running:
            char = self.spinner_chars[self.current_char_index]
            # Usar print estándar para evitar problemas con Rich markup
            print(f"\r\033[1;34m{char}\033[0m {self.message}", end="", flush=True)
            self.current_char_index = (self.current_char_index + 1) % len(self.spinner_chars)
            time.sleep(0.2)
    
    def start(self):
        """Inicia la animación."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._spin, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Detiene la animación."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=0.5)
            # Limpiar la línea
            print("\r" + " " * (len(self.message) + 10) + "\r", end="", flush=True)
    
    def update_message(self, new_message: str):
        """Actualiza el mensaje del spinner."""
        self.message = new_message
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()