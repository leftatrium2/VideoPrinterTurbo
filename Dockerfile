FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY app/ app/
COPY webui/ webui/
COPY resource/ resource/
COPY config.example.toml config.toml

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[gemini]"

# Expose ports
EXPOSE 8080
EXPOSE 8501

# Default: start API server
CMD ["python", "main.py"]
