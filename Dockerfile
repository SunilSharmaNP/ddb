FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*


RUN playwright install chromium
RUN playwright install-deps chromium

COPY pyproject.toml .

RUN pip install --no-cache-dir uv && \
    uv pip install --system -e .

COPY . .

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


RUN mkdir -p /app/downloads && \
    chmod 755 /app/downloads

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
