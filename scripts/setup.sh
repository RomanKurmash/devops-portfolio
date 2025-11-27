#!/bin/bash

set -e  # Зупинитись при помилці

echo "🚀 DevOps Portfolio Setup Script"
echo "===================================="

# Перевірка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не встановлено. Будь ласка, встановіть Docker перш ніж продовжувати."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не встановлено. Будь ласка, встановіть Docker Compose."
    exit 1
fi

echo "✅ Docker та Docker Compose доступні"

# Створення необхідних директорій
echo "📁 Створення директорій..."
mkdir -p app-infrastructure/ssl
mkdir -p app-infrastructure/grafana/provisioning
mkdir -p app-infrastructure/grafana/dashboards

# Створення прикладів конфігураційних файлів
echo "⚙️  Створення прикладів конфігураційних файлів..."

# Приклад .env файлу
if [ ! -f .env ]; then
    cat > .env.example << EOF
# Додаткові змінні оточення
COMPOSE_PROJECT_NAME=devops-portfolio
MYSQL_ROOT_PASSWORD=rootpassword
GF_SECURITY_ADMIN_PASSWORD=admin
EOF
    echo "📄 Створено .env.example"
fi

# Перевірка прав на Docker
if ! docker ps > /dev/null 2>&1; then
    echo "⚠️  Потрібні права для роботи з Docker. Спробуйте:"
    echo "   sudo usermod -aG docker \$USER"
    echo "   newgrp docker"
    exit 1
fi

echo "✅ Налаштування завершено!"
echo ""
echo "Наступні кроки:"
echo "1. Перегляньте .env.example та створіть .env файл при необхідності"
echo "2. Запустіть: ./scripts/deploy.sh"
echo "3. Перевірте: ./scripts/status.sh"