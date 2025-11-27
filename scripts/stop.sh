#!/bin/bash

echo "🛑 DevOps Portfolio Stop Script"
echo "================================"

echo "⏹️  Зупинка всіх сервісів..."

# Зупинка моніторингу
cd app-infrastructure
docker-compose -f docker-compose.monitoring.yml down
cd ..

# Зупинка додатків
cd app-infrastructure  
docker-compose -f docker-compose.apps.yml down
cd ..

# Зупинка Jenkins
cd jenkins-server
docker-compose down
cd ..

echo "✅ Всі сервіси зупинено"
echo ""
echo "💾 Дані збережено в Docker volumes"
echo "🚀 Для повторного запуску виконайте: ./scripts/deploy.sh"