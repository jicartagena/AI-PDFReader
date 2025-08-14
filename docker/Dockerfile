FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY .env.example .env

# Crear directorios necesarios
RUN mkdir -p data/uploads data/temp data/chroma_db

# Exponer puerto
EXPOSE 8501

# Script de inicio
COPY docker/start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
