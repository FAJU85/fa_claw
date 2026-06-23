FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for Open Claw
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for persistent storage
RUN mkdir -p /data && chmod 755 /data

# Default command to run the Open Claw headless daemon
CMD ["python", "main.py"]
