# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🔧 Initializing database..."\n\
python init_db.py\n\
if [ $? -eq 0 ]; then\n\
    echo "✅ Database initialized successfully"\n\
    echo "🚀 Starting application..."\n\
    uvicorn chat_app.interface.app:app --host 0.0.0.0 --port 8000\n\
else\n\
    echo "❌ Database initialization failed"\n\
    exit 1\n\
fi' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
