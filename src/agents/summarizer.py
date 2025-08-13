"""
Agente especializado en generar resúmenes de documentos
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from ..core.llm_manager import llm_manager

logger = logging.getLogger(__name__)


class BaseSummarizer(ABC):
    """Clase base para diferentes tipos de resumenes"""

    @abstractmethod
    async def generate_summary(self, content: str, **kwargs) -> str:
        """Generar resumen del contenido"""
        pass


class ExtractiveSummarizer(BaseSummarizer):
    """Resumidor extractivo - selecciona oraciones clave"""

    async def generate_summary(self, content: str, max_sentences: int = 5) -> str:
        """Generar resumen extractivo"""
        # Dividir en oraciones
        sentences = content.split(". ")

        # Seleccionar primeras y últimas oraciones (estrategia simple)
        if len(sentences) <= max_sentences:
            return content

        # Tomar primeras 3 y últimas 2 oraciones
        selected = sentences[:3] + sentences[-2:]
        return ". ".join(selected)


class AbstractiveSummarizer(BaseSummarizer):
    """Resumidor abstractivo usando LLM"""

    async def generate_summary(self, content: str, style: str = "ejecutivo") -> str:
        """Generar resumen abstractivo"""

        styles = {
            "ejecutivo": "Genera un resumen ejecutivo profesional y conciso",
            "técnico": "Genera un resumen técnico detallado",
            "académico": "Genera un resumen académico con metodología y conclusiones",
            "general": "Genera un resumen general accesible para cualquier audiencia",
        }

        style_prompt = styles.get(style, styles["general"])

        prompt = f"""
        {style_prompt} del siguiente contenido:
        
        {content}
        
        Instrucciones para el resumen:
        - Máximo 250 palabras
        - Identifica los puntos clave principales
        - Mantén la información más importante
        - Usa un lenguaje claro y conciso
        - Estructura la información de forma lógica
        
        Resumen:
        """

        return llm_manager.generate_response(prompt)


class DocumentSummarizer:
    """Orquestador de resúmenes de documentos"""

    def __init__(self):
        self.extractive = ExtractiveSummarizer()
        self.abstractive = AbstractiveSummarizer()

    async def generate_quick_summary(self, content: str) -> str:
        """Generar resumen rápido (extractivo)"""
        return await self.extractive.generate_summary(content, max_sentences=3)

    async def generate_comprehensive_summary(
        self, documents: List[str], style: str = "ejecutivo"
    ) -> str:
        """Generar resumen comprensivo de múltiples documentos"""

        # Combinar todos los documentos
        combined_content = "\n\n".join(documents)

        # Si el contenido es muy largo, hacer resumen jerárquico
        if len(combined_content) > 5000:
            return await self._hierarchical_summary(documents, style)
        else:
            return await self.abstractive.generate_summary(combined_content, style)

    async def generate_targeted_summary(
        self, documents: List[str], focus_query: str
    ) -> str:
        """Generar resumen enfocado en una consulta específica"""

        combined_content = "\n\n".join(documents)

        prompt = f"""
        Genera un resumen enfocado del siguiente contenido, prestando especial atención a: "{focus_query}"
        
        Contenido:
        {combined_content}
        
        Instrucciones:
        - Enfócate en la información relacionada con: {focus_query}
        - Máximo 200 palabras
        - Destaca los puntos más relevantes para la consulta
        - Si no hay información relevante, indícalo claramente
        
        Resumen enfocado:
        """

        return llm_manager.generate_response(prompt)

    async def _hierarchical_summary(
        self, documents: List[str], style: str = "ejecutivo"
    ) -> str:
        """Resumen jerárquico para documentos largos"""

        # Paso 1: Resumir cada documento individualmente
        individual_summaries = []
        for i, doc in enumerate(documents):
            if len(doc) > 2000:  # Solo resumir documentos largos
                summary = await self.abstractive.generate_summary(doc[:2000], style)
                individual_summaries.append(f"Documento {i+1}: {summary}")
            else:
                individual_summaries.append(f"Documento {i+1}: {doc}")

        # Paso 2: Resumir los resúmenes individuales
        combined_summaries = "\n\n".join(individual_summaries)

        prompt = f"""
        Genera un resumen final consolidado de los siguientes resúmenes de documentos:
        
        {combined_summaries}
        
        Instrucciones:
        - Crea un resumen coherente y unificado
        - Identifica temas comunes entre documentos
        - Máximo 300 palabras
        - Estilo: {style}
        - Mantén la información más relevante de cada documento
        
        Resumen consolidado:
        """

        return llm_manager.generate_response(prompt)

    async def generate_summary_by_sections(
        self, content: str, sections: List[str]
    ) -> Dict[str, str]:
        """Generar resúmenes por secciones específicas"""

        summaries = {}

        for section in sections:
            prompt = f"""
            Del siguiente contenido, extrae y resume la información relacionada con: "{section}"
            
            Contenido:
            {content}
            
            Instrucciones:
            - Enfócate únicamente en información sobre: {section}
            - Máximo 100 palabras por sección
            - Si no hay información relevante, responde "No encontrado"
            
            Resumen de {section}:
            """

            summary = llm_manager.generate_response(prompt)
            summaries[section] = summary

        return summaries

    async def generate_comparative_summary(
        self, doc1: str, doc2: str, comparison_aspect: str = ""
    ) -> str:
        """Generar resumen comparativo de dos documentos"""

        focus = f"enfocándote en {comparison_aspect}" if comparison_aspect else ""

        prompt = f"""
        Genera un resumen comparativo de los siguientes dos documentos {focus}:
        
        DOCUMENTO 1:
        {doc1}
        
        DOCUMENTO 2:
        {doc2}
        
        Instrucciones:
        - Identifica similitudes y diferencias clave
        - Estructura: Similitudes, Diferencias, Conclusiones
        - Máximo 250 palabras
        - Mantén un tono objetivo y analítico
        
        Resumen comparativo:
        """

        return llm_manager.generate_response(prompt)

    async def generate_bullet_summary(self, content: str, max_bullets: int = 7) -> str:
        """Generar resumen en formato de bullets"""

        prompt = f"""
        Convierte el siguiente contenido en un resumen de máximo {max_bullets} puntos clave:
        
        {content}
        
        Instrucciones:
        - Usa formato de bullets (•)
        - Cada bullet debe ser conciso pero informativo
        - Ordena por importancia
        - Máximo una línea por bullet
        
        Resumen en bullets:
        """

        return llm_manager.generate_response(prompt)

    def get_summary_stats(self, original_text: str, summary: str) -> Dict[str, Any]:
        """Obtener estadísticas del resumen"""

        original_words = len(original_text.split())
        summary_words = len(summary.split())
        compression_ratio = summary_words / original_words if original_words > 0 else 0

        return {
            "original_length": len(original_text),
            "summary_length": len(summary),
            "original_words": original_words,
            "summary_words": summary_words,
            "compression_ratio": compression_ratio,
            "compression_percentage": f"{(1 - compression_ratio) * 100:.1f}%",
        }
