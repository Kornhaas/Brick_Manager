#!/bin/bash
# Script to rebuild Docker container with permission fixes

echo "🔧 Rebuilding Brick Manager Docker Container"
echo "==========================================="
echo ""
echo "This will:"
echo "1. Stop the current container"
echo "2. Rebuild the image with permission fixes"
echo "3. Start the container with proper permissions"
echo ""

read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "📦 Stopping containers..."
docker-compose down

echo ""
echo "🏗️  Building new image (this may take a few minutes)..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting containers..."
docker-compose up -d

echo ""
echo "✅ Done! Checking container status..."
docker-compose ps

echo ""
echo "📋 Viewing logs (Ctrl+C to exit)..."
echo ""
docker-compose logs -f bricks-manager
