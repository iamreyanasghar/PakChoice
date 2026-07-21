#!/bin/bash
# ============================================
# Docker Entrypoint Script
# ============================================
# This script runs INSIDE the container when it starts.
# It performs setup tasks before launching the app.
# ============================================

set -e  # Exit immediately if any command fails

echo "=========================================="
echo "🚀 Starting boycott_pk container..."
echo "=========================================="

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until python -c "import pymysql; pymysql.connect(host='${DB_HOST}', user='${DB_USER}', passwd='${DB_PASSWORD}', db='${DB_NAME}')" 2>/dev/null; do
    echo "   Database not ready yet, waiting 2 seconds..."
    sleep 2
done
echo "✅ Database is ready!"

# Run Django migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput
echo "✅ Migrations complete!"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput
echo "✅ Static files collected!"

echo "=========================================="
echo "🎉 Setup complete! Starting Gunicorn..."
echo "=========================================="

# Execute the main command (from Dockerfile CMD)
exec "$@"
