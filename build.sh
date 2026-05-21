#!/bin/bash

echo "🚀 Starting build process..."

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "📁 Creating directories..."
mkdir -p staticfiles media logs

echo "📄 Collecting static files..."
python manage.py collectstatic --noinput

echo "🗄️ Running migrations..."
python manage.py migrate

echo "✅ Build completed successfully!"