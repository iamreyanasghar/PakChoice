# ============================================
# Dockerfile for buypakistani Django Application
# ============================================

# Base image with Python
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# - build-essential: for compiling Python packages
# - default-libmysqlclient-dev: for PyMySQL/MySQL client
# - pkg-config: for building some packages
# - libjpeg62-turbo-dev, zlib1g-dev: for Pillow image processing
# - curl: for downloading Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt gunicorn

# Install Node.js dependencies and build Tailwind CSS via django-tailwind
COPY theme/ theme/
RUN npm install --prefix theme/static_src && python manage.py tailwind build

# Copy project files
COPY . .

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media/users/avatars

# Make entrypoint script executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose the port Gunicorn will run on
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]

# Run Gunicorn
# --workers 3: number of worker processes (2-4 per CPU core is typical)
# --bind 0.0.0.0:8000: listen on all interfaces
# --access-logfile -: log to stdout
# --error-logfile -: log errors to stdout
CMD ["gunicorn", \
     "--workers", "3", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "buypakistani.wsgi:application"]
