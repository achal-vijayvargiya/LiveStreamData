# Use Python 3.11 slim as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    GOOGLE_APPLICATION_CREDENTIALS=credentials/service_account.json

# Install system dependencies required for Playwright and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libxkbcommon0 \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

# Create and set non-root user
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash appuser \
    && mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

# Create and set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies and Playwright
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium \
    && playwright install-deps \
    && rm -rf ~/.cache/pip ~/.cache/ms-playwright

# Copy application code
COPY . .

# Create credentials directory
RUN mkdir -p credentials && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set the entrypoint
CMD ["python", "main.py"]