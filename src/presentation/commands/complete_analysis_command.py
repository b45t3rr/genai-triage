"""Complete analysis command implementation."""

from typing import Optional, Dict, Any
from rich.panel import Panel
from .base_command import BaseCommand
from ..utils.loading_spinner import LoadingSpinner


class CompleteAnalysisCommand(BaseCommand):
    """Command for complete security analysis workflow."""
    
    def execute(
        self,
        pdf: str,
        source: str,
        url: str,
        output: Optional[str] = None,
        model: str = "openai",
        temperature: float = 0.1,
        verbose: bool = False,
        mongodb: bool = False
    ) -> Dict[str, Any]:
        """Execute complete security analysis."""
        
        provider, model_name = self._parse_model_parameter(model)
        
        if verbose:
            self._display_verbose_info({
                "Archivo PDF": pdf,
                "Código fuente": source,
                "URL objetivo": url,
                "Proveedor LLM": provider,
                "Modelo": model_name or "Por defecto",
                "Temperatura": temperature,
                "Archivo de salida": output or "No especificado",
                "MongoDB": "Sí" if mongodb else "No"
            })
        
        try:
            # Create complete analysis use case
            from ...application.use_cases import CompleteSecurityAnalysisUseCase
            
            complete_use_case = self.factory.create_complete_analysis_use_case(
                provider=provider,
                model_name=model_name,
                temperature=temperature
            )
            
            with LoadingSpinner("Realizando análisis completo...") as spinner:
                spinner.update_message("Fase 1: Análisis de PDF...")
                # Execute complete analysis
                result = complete_use_case.execute(pdf, source, url)
                
                spinner.update_message("Fase 2: Análisis estático...")
                # Additional phases handled by use case
                
                spinner.update_message("Fase 3: Análisis dinámico...")
                # Final processing
                
                spinner.update_message("Generando reporte consolidado...")
            
            # Display results
            self._display_complete_results(result)
            
            # Save results
            if output:
                self._save_to_file(result, output)
            
            if mongodb:
                self._save_to_mongodb(result, "complete_analysis")
            
            return result
            
        except Exception as e:
            self._handle_error(e, "de análisis completo")
            raise
    
    def _display_complete_results(self, result: Dict[str, Any]) -> None:
        """Display complete analysis results."""
        from rich.table import Table
        
        # Display summary
        detailed_analysis = result.get("detailed_analysis", {})
        triage_report = detailed_analysis.get("triage_report", {})
        vulnerabilities = triage_report.get("vulnerabilities", [])
        
        self.console.print(Panel(
            f"📊 **Análisis Completo Finalizado**\n"
            f"📄 **PDF:** Analizado\n"
            f"🔍 **Código:** Escaneado\n"
            f"🌐 **Aplicación:** Probada\n"
            f"⚠️ **Total vulnerabilidades:** {len(vulnerabilities)}",
            title="Resumen del Análisis Completo",
            border_style="magenta"
        ))
        
        # Display detailed vulnerabilities
        if vulnerabilities:
            self.console.print("\n" + "="*100)
            self.console.print("📋 **INFORME DETALLADO DE VULNERABILIDADES**", style="bold blue")
            self.console.print("="*100 + "\n")
            
            for i, vuln in enumerate(vulnerabilities, 1):
                self._display_detailed_vulnerability_panel(vuln, i)
                if i < len(vulnerabilities):
                    self.console.print("\n")
        
        self.console.print("\n🎉 Análisis completo finalizado exitosamente", style="green bold")
    
    def _display_detailed_vulnerability_panel(self, vuln: Dict[str, Any], vuln_number: int) -> None:
        """Display detailed vulnerability panel with technical evidence."""
        from rich.text import Text
        
        # Extract vulnerability data
        vuln_id = vuln.get('id_vulnerabilidad', f'VUL-{vuln_number:03d}')
        nombre = vuln.get('nombre', 'Vulnerabilidad sin nombre')
        severidad_triage = vuln.get('severidad_triage', 'N/A').upper()
        prioridad = vuln.get('prioridad', 'N/A')
        justificacion_severidad = vuln.get('justificacion_severidad', 'No disponible')
        impacto_real = vuln.get('impacto_real', 'No especificado')
        evidencias = vuln.get('evidencias', [])
        recomendaciones = vuln.get('recomendaciones', [])
        
        # Create panel title
        panel_title = f"{vuln_number}. {nombre}"
        
        # Build panel content
        content_lines = []
        content_lines.append(f"ID: {vuln_id}")
        content_lines.append(f"Severidad: {severidad_triage} | Prioridad: {prioridad} | Estado: VULNERABLE")
        content_lines.append("")
        
        # Description
        content_lines.append("Descripción:")
        descripcion = vuln.get('descripcion_original', 'No disponible')
        content_lines.append(self._wrap_text(descripcion, 100))
        content_lines.append("")
        
        # Severity justification
        content_lines.append("Justificación de Severidad:")
        content_lines.append(self._wrap_text(justificacion_severidad, 100))
        content_lines.append("")
        
        # Real impact
        content_lines.append("Impacto Real:")
        content_lines.append(self._wrap_text(impacto_real, 100))
        content_lines.append("")
        
        # Analysis explanation
        content_lines.append("Explicación del Estado:")
        estado_explicacion = self._generate_analysis_explanation(vuln, evidencias)
        content_lines.append(estado_explicacion)
        content_lines.append("")
        
        # Evidence section
        if evidencias:
            content_lines.append("Evidencias:")
            for i, evidencia in enumerate(evidencias, 1):
                evidencia_text = self._format_evidence(evidencia, i)
                content_lines.append(evidencia_text)
            content_lines.append("")
        
        # Recommendations section
        if recomendaciones:
            content_lines.append("Recomendaciones:")
            for i, rec in enumerate(recomendaciones, 1):
                rec_text = self._format_recommendation(rec, i)
                content_lines.append(rec_text)
        
        # Create and display panel
        panel_content = "\n".join(content_lines)
        self.console.print(Panel(
            panel_content,
            title=panel_title,
            border_style="red",
            padding=(1, 2)
        ))
    
    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width."""
        import textwrap
        return "\n".join(textwrap.wrap(text, width=width))
    
    def _generate_analysis_explanation(self, vuln: Dict[str, Any], evidencias: list) -> str:
        """Generate detailed explanation of how the vulnerability was confirmed."""
        explanation_parts = []
        
        # Analyze dynamic evidence
        dynamic_evidence = [ev for ev in evidencias if ev.get('tipo_evidencia') in ['respuesta_http', 'archivo']]
        if dynamic_evidence:
            dynamic_details = []
            for ev in dynamic_evidence:
                if ev.get('tipo_evidencia') == 'respuesta_http':
                    if ev.get('ubicacion'):
                        dynamic_details.append(f"pruebas HTTP en {ev.get('ubicacion')}")
                    else:
                        dynamic_details.append("pruebas de respuesta HTTP")
                elif ev.get('tipo_evidencia') == 'archivo':
                    dynamic_details.append(f"análisis de archivos ({ev.get('ubicacion', 'ubicación no especificada')})")
            
            if dynamic_details:
                explanation_parts.append(f"análisis dinámico mediante {', '.join(dynamic_details)}")
        
        # Analyze static evidence
        static_evidence = [ev for ev in evidencias if ev.get('tipo_evidencia') in ['código', 'configuración']]
        if static_evidence:
            static_details = []
            for ev in static_evidence:
                if ev.get('tipo_evidencia') == 'código':
                    if ev.get('ubicacion'):
                        static_details.append(f"revisión de código en {ev.get('ubicacion')}")
                    else:
                        static_details.append("análisis de código fuente")
                elif ev.get('tipo_evidencia') == 'configuración':
                    static_details.append(f"análisis de configuración ({ev.get('ubicacion', 'ubicación no especificada')})")
            
            if static_details:
                explanation_parts.append(f"análisis estático mediante {', '.join(static_details)}")
        
        # Build final explanation
        if explanation_parts:
            base_text = f"Vulnerabilidad confirmada por {' y '.join(explanation_parts)}"
            
            # Add evidence count for context
            total_evidence = len(evidencias)
            if total_evidence > 1:
                base_text += f". Se encontraron {total_evidence} evidencias que confirman la vulnerabilidad"
            elif total_evidence == 1:
                base_text += f". Se encontró 1 evidencia que confirma la vulnerabilidad"
                
            return base_text
        else:
            return "Vulnerabilidad confirmada por análisis de triage"
    
    def _format_evidence(self, evidencia: Dict[str, Any], index: int) -> str:
        """Format evidence for display with detailed technical information."""
        tipo = evidencia.get('tipo_evidencia', 'desconocido')
        descripcion = evidencia.get('descripcion', 'Sin descripción')
        contenido = evidencia.get('contenido', '')
        ubicacion = evidencia.get('ubicacion', '')
        criticidad = evidencia.get('criticidad_evidencia', 'medio')
        
        # Start with basic description and criticality
        evidence_text = f"  {index}. [{tipo.upper()}] {descripcion}"
        if criticidad:
            evidence_text += f" [Criticidad: {criticidad.upper()}]"
        
        # Add detailed technical information based on evidence type
        if tipo == 'respuesta_http' and contenido:
            evidence_text += "\n     📡 Detalles HTTP:"
            # Format HTTP content for better readability
            if '\\n' in contenido:
                # Replace escaped newlines with actual newlines for better formatting
                formatted_content = contenido.replace('\\n', '\n')
                # Limit content length but show key parts
                if len(formatted_content) > 500:
                    lines = formatted_content.split('\n')
                    # Show first few lines and last few lines
                    if len(lines) > 10:
                        key_lines = lines[:5] + ['     [... contenido truncado ...]'] + lines[-3:]
                        formatted_content = '\n'.join(key_lines)
                evidence_text += f"\n     {formatted_content}"
            else:
                evidence_text += f"\n     {contenido}"
            
            if ubicacion:
                evidence_text += f"\n     🎯 Endpoint: {ubicacion}"
                
        elif tipo == 'código' and contenido:
            evidence_text += "\n     💻 Código/Payload:"
            # Format code content
            if len(contenido) > 300:
                evidence_text += f"\n     {contenido[:300]}..."
            else:
                evidence_text += f"\n     {contenido}"
            
            if ubicacion:
                evidence_text += f"\n     📁 Ubicación: {ubicacion}"
                
        elif tipo == 'archivo' and ubicacion:
            evidence_text += f"\n     📄 Archivo: {ubicacion}"
            if contenido:
                evidence_text += f"\n     📋 Contenido: {contenido[:200]}{'...' if len(contenido) > 200 else ''}"
                
        elif tipo == 'configuración':
            if contenido:
                evidence_text += f"\n     ⚙️ Configuración: {contenido}"
            if ubicacion:
                evidence_text += f"\n     📍 Ubicación: {ubicacion}"
        
        # Add location info if not already included
        elif ubicacion and not any(x in evidence_text.lower() for x in ['endpoint:', 'ubicación:', 'archivo:']):
            evidence_text += f"\n     📍 Ubicación: {ubicacion}"
            
        # Add content if not already included and it's short enough
        elif contenido and len(contenido) < 150 and 'contenido:' not in evidence_text.lower():
            evidence_text += f"\n     📋 Detalles: {contenido}"
        
        return evidence_text
    
    def _format_recommendation(self, recomendacion: Dict[str, Any], index: int) -> str:
        """Format recommendation for display."""
        tipo = recomendacion.get('tipo', 'correctiva').upper()
        descripcion = recomendacion.get('descripcion', 'Sin descripción')
        
        # Map recommendation types to Spanish
        tipo_map = {
            'INMEDIATA': 'INMEDIATA',
            'IMMEDIATE': 'INMEDIATA', 
            'CORRECTIVA': 'CORRECTIVA',
            'CORRECTIVE': 'CORRECTIVA',
            'PREVENTIVA': 'PREVENTIVA',
            'PREVENTIVE': 'PREVENTIVA',
            'MITIGACIÓN': 'MITIGACIÓN',
            'MITIGATION': 'MITIGACIÓN'
        }
        
        tipo_display = tipo_map.get(tipo, tipo)
        return f"  {index}. [{tipo_display}] {descripcion}"