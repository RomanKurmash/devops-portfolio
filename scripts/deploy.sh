#!/bin/bash

set -e

echo "🚀 DevOps Portfolio Deployment Script"
echo "========================================="

# Кольори для виводу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функції для кольорового виводу
error() { echo -e "${RED}❌ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

# Перевірка наявності docker-compose файлів
check_compose_files() {
    local files=(
        "jenkins-server/docker-compose.yml"
        "app-infrastructure/docker-compose.apps.yml"
        "app-infrastructure/docker-compose.monitoring.yml"
    )
    
    for file in "${files[@]}"; do
        if [ ! -f "$file" ]; then
            error "Файл $file не знайдено"
            exit 1
        fi
    done
    success "Всі docker-compose файли знайдено"
}

# Створення Docker мереж
create_networks() {
    info "Створення Docker мереж..."
    
    # Мережа для додатків
    if ! docker network inspect app-infrastructure_apps-net > /dev/null 2>&1; then
        docker network create app-infrastructure_apps-net
        success "Створено мережу app-infrastructure_apps-net"
    else
        info "Мережа app-infrastructure_apps-net вже існує"
    fi
    
    # Мережа для Jenkins
    if ! docker network inspect jenkins-server_jenkins-net > /dev/null 2>&1; then
        docker network create jenkins-server_jenkins-net
        success "Створено мережу jenkins-server_jenkins-net"
    else
        info "Мережа jenkins-server_jenkins-net вже існує"
    fi
}

# Запуск Jenkins
deploy_jenkins() {
    info "Запуск Jenkins..."
    cd jenkins-server
    docker-compose up -d
    cd ..
    success "Jenkins запущено"
}

# Запуск додатків
deploy_apps() {
    info "Запуск додатків (WordPress, MySQL, Nginx)..."
    cd app-infrastructure
    docker-compose -f docker-compose.apps.yml up -d
    cd ..
    success "Додатки запущено"
}

# Запуск моніторингу
deploy_monitoring() {
    info "Запуск системи моніторингу..."
    cd app-infrastructure
    docker-compose -f docker-compose.monitoring.yml up -d
    cd ..
    success "Моніторинг запущено"
}

# Очікування готовності сервісів
wait_for_services() {
    info "Очікування готовності сервісів..."
    sleep 30
    
    # Перевірка основних сервісів
    services=(
        "http://localhost"
        "http://localhost:3000"
        "http://localhost:9090"
        "http://localhost:8080"
    )
    
    for service in "${services[@]}"; do
        if curl -f --connect-timeout 5 "$service" > /dev/null 2>&1; then
            success "$service - доступний"
        else
            info "$service - ще не готовий"
        fi
    done
}

# Головна функція
main() {
    echo "🔍 Перевірка необхідних файлів..."
    check_compose_files
    
    echo "🌐 Налаштування мереж..."
    create_networks
    
    echo "📦 Запуск сервісів..."
    deploy_jenkins
    sleep 10
    
    deploy_apps
    sleep 20
    
    deploy_monitoring
    
    echo "⏳ Очікування ініціалізації..."
    wait_for_services
    
    echo ""
    success "🚀 ВСЕ ЗАПУЩЕНО!"
    echo ""
    echo "🌐 Доступні сервіси:"
    echo "   WordPress:  http://localhost"
    echo "   Grafana:    http://localhost:3000 (admin/admin)"
    echo "   Prometheus: http://localhost:9090"
    echo "   Jenkins:    http://localhost:8080"
    echo "   Alertmanager: http://localhost:9093"
    echo ""
    echo "📊 Перевірити статус: ./scripts/status.sh"
    echo "🛑 Зупинити все:      ./scripts/stop.sh"
}

# Виклик головної функції
main