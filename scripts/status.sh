#!/bin/bash

echo "📊 DevOps Portfolio Status"
echo "============================"

# Загальна інформація
echo "🐳 Docker Information:"
docker --version
docker-compose --version
echo ""

# Статус контейнерів
echo "📦 Running Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🌐 Service Status:"

check_service() {
    if curl -f --connect-timeout 3 "$1" > /dev/null 2>&1; then
        echo "✅ $2: $1"
    else
        echo "❌ $2: $1 (недоступний)"
    fi
}

check_service "http://localhost" "WordPress"
check_service "http://localhost:3000" "Grafana" 
check_service "http://localhost:9090" "Prometheus"
check_service "http://localhost:8080" "Jenkins"
check_service "http://localhost:9093" "Alertmanager"

echo ""
echo "📈 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -6