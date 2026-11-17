# Multi-Agent E-commerce Product Trust Intelligence System
# Problem Statement PS-11 (VESIT AAI&EA Course Project)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code and assets
COPY agents/ /app/agents/
COPY static/ /app/static/
COPY tests/ /app/tests/
COPY cli.py /app/
COPY mcp_server.py /app/
COPY streamlit_app.py /app/
COPY antigravity_mcp_config.json /app/
COPY README.md /app/

# Create data directory for persistent SQLite database
RUN mkdir -p /app/data

# Expose Streamlit web port (8501) and MCP communication port (8000)
EXPOSE 8501
EXPOSE 8000

# Health check to ensure Streamlit server is running properly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Launch the Streamlit Enterprise Dashboard by default
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
