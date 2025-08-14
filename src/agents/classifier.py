"""
Agente especializado en clasificación de documentos por temas
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
import re

from langchain.schema import Document
from core.llm_manager import llm_manager

logger = logging.getLogger(__name__)


class TopicClassifier:
    """Agente para clasificar documentos por temas y categorías"""

    def __init__(self):
        self.predefined_categories = {
            "business": [
                "negocio",
                "empresa",
                "comercial",
                "ventas",
                "marketing",
                "strategy",
            ],
            "technical": [
                "técnico",
                "technology",
                "sistema",
                "software",
                "desarrollo",
                "programming",
            ],
            "legal": [
                "legal",
                "ley",
                "contrato",
                "regulación",
                "compliance",
                "derecho",
            ],
            "financial": [
                "financiero",
                "dinero",
                "presupuesto",
                "costo",
                "investment",
                "budget",
            ],
            "academic": [
                "académico",
                "investigación",
                "estudio",
                "análisis",
                "research",
                "university",
            ],
            "healthcare": [
                "salud",
                "médico",
                "hospital",
                "patient",
                "treatment",
                "medicina",
            ],
            "education": [
                "educación",
                "enseñanza",
                "estudiante",
                "curso",
                "learning",
                "school",
            ],
            "government": [
                "gobierno",
                "público",
                "política",
                "policy",
                "administrative",
                "state",
            ],
        }

    async def classify_documents_by_topics(self, documents: List[Document]) -> str:
        """Clasificar documentos por temas principales"""

        # Extraer textos y metadatos
        doc_texts = [
            (doc.page_content, doc.metadata.get("source_file", "unknown"))
            for doc in documents
        ]

        # Agrupar por archivo fuente
        files_content = defaultdict(list)
        for text, source in doc_texts:
            files_content[source].append(text)

        # Clasificar cada archivo
        file_classifications = {}
        for filename, chunks in files_content.items():
            combined_text = " ".join(chunks)
            classification = await self._classify_single_document(
                combined_text, filename
            )
            file_classifications[filename] = classification

        # Generar reporte de clasificación
        return await self._generate_classification_report(file_classifications)

    async def _classify_single_document(
        self, content: str, filename: str
    ) -> Dict[str, Any]:
        """Clasificar un documento individual"""

        # Clasificación por LLM
        llm_classification = await self._llm_topic_classification(content, filename)

        # Clasificación por palabras clave
        keyword_classification = self._keyword_classification(content)

        # Extracción de temas específicos
        specific_topics = await self._extract_specific_topics(content)

        return {
            "filename": filename,
            "llm_classification": llm_classification,
            "keyword_categories": keyword_classification,
            "specific_topics": specific_topics,
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
        }

    async def _llm_topic_classification(
        self, content: str, filename: str
    ) -> Dict[str, Any]:
        """Clasificación usando LLM"""

        prompt = f"""
        Analiza el siguiente documento y clasifícalo por temas y categorías:
        
        **Documento**: {filename}
        **Contenido**: {content[:1500]}...
        
        Proporciona la clasificación en el siguiente formato:
        
        ## CATEGORÍA PRINCIPAL
        [Una categoría principal: Business, Technical, Legal, Financial, Academic, Healthcare, Education, Government, u Otro]
        
        ## TEMAS ESPECÍFICOS
        [Lista de 3-5 temas específicos identificados]
        
        ## NIVEL DE ESPECIALIZACIÓN
        [General, Intermedio, o Avanzado]
        
        ## AUDIENCIA OBJETIVO
        [Descripción de la audiencia objetivo]
        
        ## PALABRAS CLAVE
        [5-8 palabras clave principales]
        
        Clasificación:
        """

        response = llm_manager.generate_response(prompt)

        # Parsear respuesta
        return self._parse_llm_classification(response)

    def _parse_llm_classification(self, llm_response: str) -> Dict[str, Any]:
        """Parsear respuesta del LLM para extraer clasificación estructurada"""

        classification = {
            "primary_category": "Unknown",
            "specific_topics": [],
            "specialization_level": "General",
            "target_audience": "General",
            "keywords": [],
            "raw_response": llm_response,
        }

        # Extraer categoría principal
        category_match = re.search(
            r"CATEGORÍA PRINCIPAL\s*[:\-]?\s*([^\n]+)", llm_response, re.IGNORECASE
        )
        if category_match:
            classification["primary_category"] = category_match.group(1).strip()

        # Extraer temas específicos
        topics_section = re.search(
            r"TEMAS ESPECÍFICOS\s*[:\-]?(.*?)(?=##|$)",
            llm_response,
            re.IGNORECASE | re.DOTALL,
        )
        if topics_section:
            topics_text = topics_section.group(1)
            topics = [
                topic.strip().strip("•-*")
                for topic in topics_text.split("\n")
                if topic.strip()
            ]
            classification["specific_topics"] = [t for t in topics if len(t) > 3][:5]

        # Extraer nivel de especialización
        level_match = re.search(
            r"NIVEL DE ESPECIALIZACIÓN\s*[:\-]?\s*([^\n]+)", llm_response, re.IGNORECASE
        )
        if level_match:
            classification["specialization_level"] = level_match.group(1).strip()

        # Extraer audiencia objetivo
        audience_match = re.search(
            r"AUDIENCIA OBJETIVO\s*[:\-]?\s*([^\n]+)", llm_response, re.IGNORECASE
        )
        if audience_match:
            classification["target_audience"] = audience_match.group(1).strip()

        # Extraer palabras clave
        keywords_section = re.search(
            r"PALABRAS CLAVE\s*[:\-]?(.*?)(?=##|$)",
            llm_response,
            re.IGNORECASE | re.DOTALL,
        )
        if keywords_section:
            keywords_text = keywords_section.group(1)
            keywords = [
                kw.strip().strip("•-*,") for kw in keywords_text.split() if kw.strip()
            ]
            classification["keywords"] = keywords[:8]

        return classification

    def _keyword_classification(self, content: str) -> Dict[str, float]:
        """Clasificación basada en palabras clave predefinidas"""

        content_lower = content.lower()
        category_scores = {}

        for category, keywords in self.predefined_categories.items():
            score = 0
            for keyword in keywords:
                score += content_lower.count(keyword.lower())

            # Normalizar por longitud del documento
            normalized_score = score / len(content.split()) * 1000
            category_scores[category] = normalized_score

        return category_scores

    async def _extract_specific_topics(self, content: str) -> List[str]:
        """Extraer temas específicos del contenido"""

        prompt = f"""
        Extrae los temas específicos más importantes del siguiente texto:
        
        {content[:1000]}...
        
        Instrucciones:
        - Lista entre 3-7 temas específicos
        - Sé preciso y descriptivo
        - Evita términos muy generales
        - Un tema por línea
        
        Temas específicos:
        """

        response = llm_manager.generate_response(prompt)

        # Extraer temas de la respuesta
        topics = []
        for line in response.split("\n"):
            topic = line.strip().strip("•-*0123456789.")
            if len(topic) > 3 and topic not in topics:
                topics.append(topic)

        return topics[:7]

    async def _generate_classification_report(
        self, classifications: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generar reporte consolidado de clasificación"""

        # Análisis estadístico
        all_categories = [
            c["llm_classification"]["primary_category"]
            for c in classifications.values()
        ]
        category_counts = Counter(all_categories)

        all_topics = []
        for c in classifications.values():
            all_topics.extend(c["llm_classification"]["specific_topics"])
        topic_counts = Counter(all_topics)

        # Construir reporte
        report_sections = []

        # Resumen ejecutivo
        report_sections.append("# 📊 REPORTE DE CLASIFICACIÓN DE DOCUMENTOS\n")
        report_sections.append(
            f"**Total de documentos analizados**: {len(classifications)}\n"
        )

        # Distribución por categorías
        report_sections.append("## 📈 DISTRIBUCIÓN POR CATEGORÍAS\n")
        for category, count in category_counts.most_common():
            percentage = (count / len(classifications)) * 100
            report_sections.append(
                f"- **{category}**: {count} documentos ({percentage:.1f}%)"
            )

        # Temas más frecuentes
        report_sections.append("\n## 🔍 TEMAS MÁS FRECUENTES\n")
        for topic, count in topic_counts.most_common(10):
            report_sections.append(f"- {topic} ({count} menciones)")

        # Clasificación por documento
        report_sections.append("\n## 📄 CLASIFICACIÓN POR DOCUMENTO\n")
        for filename, classification in classifications.items():
            llm_class = classification["llm_classification"]
            report_sections.append(
                f"""
### 📋 {filename}
- **Categoría**: {llm_class["primary_category"]}
- **Nivel**: {llm_class["specialization_level"]}
- **Audiencia**: {llm_class["target_audience"]}
- **Temas**: {", ".join(llm_class["specific_topics"])}
- **Palabras clave**: {", ".join(llm_class["keywords"])}
            """
            )

        # Análisis de diversidad temática
        report_sections.append("\n## 🌟 ANÁLISIS DE DIVERSIDAD TEMÁTICA\n")

        diversity_analysis = await self._analyze_thematic_diversity(classifications)
        report_sections.append(diversity_analysis)

        return "\n".join(report_sections)

    async def _analyze_thematic_diversity(
        self, classifications: Dict[str, Dict[str, Any]]
    ) -> str:
        """Analizar diversidad temática del conjunto de documentos"""

        categories = [
            c["llm_classification"]["primary_category"]
            for c in classifications.values()
        ]
        unique_categories = len(set(categories))

        all_topics = []
        for c in classifications.values():
            all_topics.extend(c["llm_classification"]["specific_topics"])
        unique_topics = len(set(all_topics))

        # Calcular métricas de diversidad
        category_diversity = unique_categories / len(categories) if categories else 0
        topic_diversity = unique_topics / len(all_topics) if all_topics else 0

        analysis = f"""
**Diversidad de categorías**: {category_diversity:.2f} ({unique_categories} categorías únicas)
**Diversidad de temas**: {topic_diversity:.2f} ({unique_topics} temas únicos)

**Interpretación**:
"""

        if category_diversity > 0.7:
            analysis += "- ✅ Alta diversidad categórica - conjunto muy variado"
        elif category_diversity > 0.4:
            analysis += "- 📊 Diversidad categórica moderada - buena variedad"
        else:
            analysis += "- 🎯 Baja diversidad categórica - conjunto especializado"

        if topic_diversity > 0.6:
            analysis += "\n- ✅ Alta diversidad temática - amplio rango de temas"
        elif topic_diversity > 0.3:
            analysis += "\n- 📊 Diversidad temática moderada - temas relacionados"
        else:
            analysis += "\n- 🎯 Baja diversidad temática - enfoque específico"

        return analysis

    async def classify_by_custom_categories(
        self, documents: List[Document], custom_categories: List[str]
    ) -> Dict[str, List[str]]:
        """Clasificar documentos usando categorías personalizadas"""

        # Agrupar por archivo
        files_content = defaultdict(list)
        for doc in documents:
            source = doc.metadata.get("source_file", "unknown")
            files_content[source].append(doc.page_content)

        # Clasificar cada archivo según categorías personalizadas
        results = defaultdict(list)

        for filename, chunks in files_content.items():
            combined_text = " ".join(chunks)

            prompt = f"""
            Clasifica el siguiente documento según estas categorías específicas: {", ".join(custom_categories)}
            
            **Documento**: {filename}
            **Contenido**: {combined_text[:1000]}...
            
            Instrucciones:
            - Selecciona UNA categoría principal de la lista proporcionada
            - Si no encaja en ninguna, indica "Otro"
            - Justifica brevemente tu elección
            
            Categoría seleccionada:
            """

            response = llm_manager.generate_response(prompt)

            # Extraer categoría de la respuesta
            for category in custom_categories:
                if category.lower() in response.lower():
                    results[category].append(filename)
                    break
            else:
                results["Otro"].append(filename)

        return dict(results)

    async def generate_topic_hierarchy(self, documents: List[Document]) -> str:
        """Generar jerarquía de temas encontrados"""

        # Extraer todos los textos
        all_texts = [doc.page_content for doc in documents]
        combined_text = " ".join(all_texts)

        prompt = f"""
        Analiza el siguiente conjunto de textos y genera una jerarquía de temas organizados:
        
        {combined_text[:2000]}...
        
        Crea una estructura jerárquica de temas con el formato:
        
        # TEMA PRINCIPAL 1
        ## Subtema 1.1
        ### Detalle 1.1.1
        ### Detalle 1.1.2
        ## Subtema 1.2
        
        # TEMA PRINCIPAL 2
        ## Subtema 2.1
        
        Instrucciones:
        - Máximo 4 temas principales
        - 2-3 subtemas por tema principal
        - Detalles específicos cuando sea relevante
        
        Jerarquía de temas:
        """

        return llm_manager.generate_response(prompt)

    def get_classification_stats(
        self, classifications: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Obtener estadísticas de clasificación"""

        if not classifications:
            return {"error": "No classifications available"}

        # Contar categorías
        categories = [
            c["llm_classification"]["primary_category"]
            for c in classifications.values()
        ]
        category_counts = Counter(categories)

        # Contar niveles de especialización
        levels = [
            c["llm_classification"]["specialization_level"]
            for c in classifications.values()
        ]
        level_counts = Counter(levels)

        # Contar palabras clave únicas
        all_keywords = []
        for c in classifications.values():
            all_keywords.extend(c["llm_classification"]["keywords"])
        unique_keywords = len(set(all_keywords))

        return {
            "total_documents": len(classifications),
            "unique_categories": len(category_counts),
            "category_distribution": dict(category_counts),
            "specialization_levels": dict(level_counts),
            "unique_keywords": unique_keywords,
            "most_common_keywords": dict(Counter(all_keywords).most_common(10)),
        }
