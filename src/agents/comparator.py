"""
Agente especializado en comparación de documentos
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from ..core.llm_manager import llm_manager

logger = logging.getLogger(__name__)


class DocumentComparator:
    """Agente para comparar documentos y encontrar similitudes/diferencias"""

    def __init__(self):
        self.comparison_templates = {
            "general": "comparación general",
            "methodology": "metodologías utilizadas",
            "conclusions": "conclusiones y resultados",
            "data": "datos y estadísticas",
            "recommendations": "recomendaciones",
            "timeline": "cronologías y fechas",
            "costs": "costos y presupuestos",
            "technical": "aspectos técnicos",
        }

    async def compare_documents(
        self, documents: Dict[str, List[str]], focus_aspect: str = ""
    ) -> str:
        """Comparar múltiples documentos"""

        if len(documents) < 2:
            return "Se necesitan al menos 2 documentos para hacer una comparación."

        # Preparar contenido de documentos
        doc_contents = {}
        for filename, chunks in documents.items():
            doc_contents[filename] = " ".join(chunks)

        # Detectar tipo de comparación
        comparison_type = self._detect_comparison_type(focus_aspect)

        # Generar comparación según el tipo
        if len(documents) == 2:
            return await self._compare_two_documents(
                doc_contents, comparison_type, focus_aspect
            )
        else:
            return await self._compare_multiple_documents(
                doc_contents, comparison_type, focus_aspect
            )

    def _detect_comparison_type(self, focus_aspect: str) -> str:
        """Detectar el tipo de comparación basado en la consulta"""

        focus_lower = focus_aspect.lower()

        for comp_type, keywords in {
            "methodology": ["metodología", "método", "enfoque", "approach"],
            "conclusions": ["conclusión", "resultado", "finding", "outcome"],
            "data": ["datos", "estadísticas", "números", "data", "statistics"],
            "recommendations": ["recomendación", "sugerencia", "recommendation"],
            "timeline": ["tiempo", "fecha", "cronología", "timeline"],
            "costs": ["costo", "precio", "presupuesto", "cost", "budget"],
            "technical": ["técnico", "technology", "implementación"],
        }.items():
            if any(keyword in focus_lower for keyword in keywords):
                return comp_type

        return "general"

    async def _compare_two_documents(
        self, documents: Dict[str, str], comparison_type: str, focus_aspect: str
    ) -> str:
        """Comparar exactamente dos documentos"""

        doc_names = list(documents.keys())
        doc1_name, doc2_name = doc_names[0], doc_names[1]
        doc1_content, doc2_content = documents[doc1_name], documents[doc2_name]

        focus_instruction = (
            f"enfocándote específicamente en {focus_aspect}" if focus_aspect else ""
        )

        prompt = f"""
        Realiza una comparación detallada entre los siguientes dos documentos {focus_instruction}:
        
        **DOCUMENTO A: {doc1_name}**
        {doc1_content}
        
        **DOCUMENTO B: {doc2_name}**
        {doc2_content}
        
        Estructura tu comparación de la siguiente manera:
        
        ## 📋 RESUMEN EJECUTIVO
        - Breve descripción de cada documento
        - Propósito principal de cada uno
        
        ## 🔍 SIMILITUDES CLAVE
        - Temas o conceptos compartidos
        - Enfoques similares
        - Datos o conclusiones coincidentes
        
        ## ⚡ DIFERENCIAS PRINCIPALES
        - Enfoques distintos
        - Datos contradictorios
        - Perspectivas diferentes
        
        ## 📊 ANÁLISIS COMPARATIVO
        - Fortalezas y debilidades de cada documento
        - Complementariedad entre ambos
        
        ## 💡 CONCLUSIONES
        - Síntesis de los hallazgos
        - Recomendaciones basadas en la comparación
        
        Mantén un tono objetivo y analítico.
        """

        return llm_manager.generate_response(prompt)

    async def _compare_multiple_documents(
        self, documents: Dict[str, str], comparison_type: str, focus_aspect: str
    ) -> str:
        """Comparar múltiples documentos (3 o más)"""

        doc_summaries = []
        for name, content in documents.items():
            # Crear resumen breve de cada documento
            summary = content[:500] + "..." if len(content) > 500 else content
            doc_summaries.append(f"**{name}**: {summary}")

        focus_instruction = f"enfocándote en {focus_aspect}" if focus_aspect else ""

        prompt = f"""
        Realiza una comparación sistemática de los siguientes {len(documents)} documentos {focus_instruction}:
        
        {chr(10).join(doc_summaries)}
        
        Estructura tu análisis comparativo de la siguiente manera:
        
        ## 📑 MATRIZ COMPARATIVA
        Crea una comparación estructurada documento por documento:
        
        ## 🔗 PATRONES COMUNES
        - Temas que aparecen en múltiples documentos
        - Enfoques compartidos
        - Datos o conclusiones consistentes
        
        ## 🌟 ELEMENTOS ÚNICOS
        - Aspectos exclusivos de cada documento
        - Aportes distintivos
        - Perspectivas originales
        
        ## 📈 ANÁLISIS DE CONSISTENCIA
        - Nivel de alineación entre documentos
        - Contradicciones o discrepancias
        - Grado de complementariedad
        
        ## 🎯 SÍNTESIS FINAL
        - Panorama general consolidado
        - Recomendaciones para usar conjunto de documentos
        
        Mantén objetividad y proporciona análisis equilibrado.
        """

        return llm_manager.generate_response(prompt)

    async def compare_specific_aspects(
        self, documents: Dict[str, str], aspects: List[str]
    ) -> Dict[str, str]:
        """Comparar aspectos específicos entre documentos"""

        comparisons = {}

        for aspect in aspects:
            prompt = f"""
            Compara el siguiente aspecto específico entre los documentos: **{aspect}**
            
            DOCUMENTOS:
            {chr(10).join([f"**{name}**: {content[:400]}..." for name, content in documents.items()])}
            
            Instrucciones:
            - Enfócate únicamente en: {aspect}
            - Identifica cómo cada documento aborda este aspecto
            - Señala similitudes y diferencias
            - Máximo 150 palabras
            
            Comparación de {aspect}:
            """

            comparison = llm_manager.generate_response(prompt)
            comparisons[aspect] = comparison

        return comparisons

    async def generate_compatibility_analysis(self, documents: Dict[str, str]) -> str:
        """Analizar compatibilidad y complementariedad entre documentos"""

        prompt = f"""
        Analiza la compatibilidad y potencial de integración entre los siguientes documentos:
        
        {chr(10).join([f"**{name}**: {content[:300]}..." for name, content in documents.items()])}
        
        Proporciona un análisis de:
        
        ## 🤝 COMPATIBILIDAD
        - Grado de alineación entre documentos
        - Conflictos o contradicciones identificadas
        - Nivel de coherencia conceptual
        
        ## 🔄 COMPLEMENTARIEDAD
        - Cómo se complementan los documentos
        - Vacíos que cada uno llena respecto a los otros
        - Valor agregado del conjunto
        
        ## 📋 ESTRATEGIA DE INTEGRACIÓN
        - Recomendaciones para usar documentos conjuntamente
        - Orden de prioridad o lectura sugerido
        - Advertencias sobre posibles conflictos
        
        Análisis de compatibilidad:
        """

        return llm_manager.generate_response(prompt)

    async def find_contradictions(self, documents: Dict[str, str]) -> str:
        """Encontrar contradicciones entre documentos"""

        prompt = f"""
        Identifica contradicciones, inconsistencias o conflictos entre los siguientes documentos:
        
        {chr(10).join([f"**{name}**: {content[:400]}..." for name, content in documents.items()])}
        
        Estructura tu análisis así:
        
        ## ⚠️ CONTRADICCIONES IDENTIFICADAS
        - Lista específica de conflictos encontrados
        - Documentos involucrados en cada contradicción
        
        ## 📊 DATOS CONFLICTIVOS
        - Números, fechas o estadísticas que no coinciden
        - Metodologías que se contradicen
        
        ## 🤔 PERSPECTIVAS DIVERGENTES
        - Diferentes puntos de vista sobre el mismo tema
        - Conclusiones opuestas
        
        ## 💡 RECOMENDACIONES
        - Cómo resolver o manejar las contradicciones
        - Investigación adicional necesaria
        
        Si no hay contradicciones significativas, indícalo claramente.
        """

        return llm_manager.generate_response(prompt)

    async def generate_evolution_analysis(self, documents: Dict[str, str]) -> str:
        """Analizar evolución o progresión entre documentos (si tienen orden temporal)"""

        prompt = f"""
        Analiza la evolución, progresión o desarrollo temático entre los siguientes documentos:
        
        {chr(10).join([f"**{name}**: {content[:300]}..." for name, content in documents.items()])}
        
        Estructura el análisis evolutivo:
        
        ## 📈 PROGRESIÓN IDENTIFICADA
        - Evolución de conceptos o ideas
        - Desarrollo de metodologías
        - Cambios en enfoques o perspectivas
        
        ## 🔄 CONTINUIDAD Y CAMBIOS
        - Elementos que se mantienen constantes
        - Aspectos que han evolucionado
        - Nuevas incorporaciones
        
        ## 🎯 TENDENCIAS OBSERVADAS
        - Dirección del cambio
        - Patrones de desarrollo
        - Maduración de ideas
        
        ## 🔮 IMPLICACIONES
        - Significado de la evolución observada
        - Proyecciones futuras basadas en la progresión
        
        Análisis evolutivo:
        """

        return llm_manager.generate_response(prompt)

    def get_comparison_metrics(self, documents: Dict[str, str]) -> Dict[str, Any]:
        """Obtener métricas cuantitativas de la comparación"""

        doc_lengths = {name: len(content) for name, content in documents.items()}
        doc_word_counts = {
            name: len(content.split()) for name, content in documents.items()
        }

        return {
            "total_documents": len(documents),
            "document_names": list(documents.keys()),
            "character_counts": doc_lengths,
            "word_counts": doc_word_counts,
            "average_length": sum(doc_lengths.values()) / len(doc_lengths),
            "length_variance": self._calculate_length_variance(
                list(doc_lengths.values())
            ),
            "size_similarity": self._calculate_size_similarity(
                list(doc_lengths.values())
            ),
        }

    def _calculate_length_variance(self, lengths: List[int]) -> float:
        """Calcular varianza de longitudes"""
        if len(lengths) < 2:
            return 0

        mean = sum(lengths) / len(lengths)
        variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
        return variance

    def _calculate_size_similarity(self, lengths: List[int]) -> float:
        """Calcular similitud de tamaños (0-1, siendo 1 muy similares)"""
        if len(lengths) < 2:
            return 1.0

        max_len = max(lengths)
        min_len = min(lengths)

        if max_len == 0:
            return 1.0

        return min_len / max_len
