# Use Python 3.11 slim as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service_account.json \
    PORT=8080 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

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
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright with browsers
RUN playwright install --with-deps chromium && \
    playwright install chromium && \
    chmod -R 777 /ms-playwright

# Create necessary directories with proper permissions
RUN mkdir -p /app/credentials && \
    mkdir -p /app/images && \
    mkdir -p /app/user_data && \
    mkdir -p /var/log/supervisor

# Copy application code
COPY . .

# Ensure config directory exists and has proper permissions
RUN mkdir -p /app/app/config && \
    chmod -R 777 /app

# Setup supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Verify config file exists
RUN ls -la /app/app/config/users.json || echo "Config file missing!"

# Set the entrypoint
CMD ["/usr/bin/supervisord"]