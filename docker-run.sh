#!/bin/bash
set -e

echo "🐳 Starting DigitalFTE on Docker..."
echo ""

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Start Docker Desktop and try again."
    exit 1
fi

echo "📦 Starting containers..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 15

echo ""
echo "✅ Containers Running:"
docker-compose ps

echo ""
echo "📊 Access Odoo:"
echo "   http://localhost:8069"
echo ""
echo "📝 Default credentials:"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "🔍 View logs:"
echo "   docker-compose logs -f odoo"
echo ""
echo "🛑 Stop containers:"
echo "   docker-compose down"
