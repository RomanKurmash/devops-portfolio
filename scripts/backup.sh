#!/bin/bash

# DevOps Portfolio Backup Script
# Простий та ефективний бекап інфраструктури

set -e  

# Конфігурація
BACKUP_DIR="./backups"
MYSQL_CONTAINER="mysql-db"
WORDPRESS_CONTAINER="wordpress-app"
RETENTION_DAYS=7
TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BACKUP_NAME="portfolio_backup_$TIMESTAMP"

# Кольори для виводу
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"; exit 1; }

# Створюємо директорію бекапів
mkdir -p $BACKUP_DIR

log "🚀 Starting DevOps Portfolio Backup: $BACKUP_NAME"

# 1. Бекап MySQL бази даних
log "📦 Backing up MySQL database..."
if docker exec $MYSQL_CONTAINER mysqldump -uroot -prootpassword wordpress 2>/dev/null > "$BACKUP_DIR/$BACKUP_NAME.sql"; then
    log "✅ MySQL backup: $BACKUP_NAME.sql ($(du -h "$BACKUP_DIR/$BACKUP_NAME.sql" | cut -f1))"
else
    error "Failed to backup MySQL"
fi

# 2. Бекап WordPress файлів
log "📁 Backing up WordPress files..."
if docker exec $WORDPRESS_CONTAINER tar czf - /var/www/html 2>/dev/null > "$BACKUP_DIR/$BACKUP_NAME-wp-files.tar.gz"; then
    log "✅ WordPress files backup completed"
else
    error "Failed to backup WordPress files"
fi

# 3. Бекап конфігурацій Docker
log "⚙️ Backing up Docker configurations..."
tar czf "$BACKUP_DIR/$BACKUP_NAME-configs.tar.gz" \
    docker-compose.yml \
    nginx/ \
    prometheus/ \
    grafana/ \
    alertmanager/ \
    scripts/ \
    mysql-exporter/ 2>/dev/null || warn "Some configs missing"

# 4. Створюємо основний архів
log "📦 Creating main archive..."
tar czf "$BACKUP_DIR/$BACKUP_NAME-full.tar.gz" \
    -C $BACKUP_DIR \
    "$BACKUP_NAME.sql" \
    "$BACKUP_NAME-wp-files.tar.gz" \
    "$BACKUP_NAME-configs.tar.gz"

# 5. Очистка тимчасових файлів
log "🧹 Cleaning temporary files..."
rm -f "$BACKUP_DIR/$BACKUP_NAME.sql" \
      "$BACKUP_DIR/$BACKUP_NAME-wp-files.tar.gz" \
      "$BACKUP_DIR/$BACKUP_NAME-configs.tar.gz"

# 6. Очистка старих бекапів
log "🗑️ Removing backups older than $RETENTION_DAYS days..."
find $BACKUP_DIR -name "portfolio_backup_*" -type f -mtime +$RETENTION_DAYS -delete

# 7. Фінальна статистика
FINAL_FILE="$BACKUP_DIR/$BACKUP_NAME-full.tar.gz"
log "🎉 Backup completed successfully!"
echo -e "${BLUE}=== BACKUP SUMMARY ===${NC}"
echo "📁 File: $(basename $FINAL_FILE)"
echo "💾 Size: $(du -h $FINAL_FILE | cut -f1)"
echo "📅 Created: $(date)"
echo "📍 Location: $FINAL_FILE"
echo -e "${BLUE}======================${NC}"

# 8. Нотифікація в Telegram (опційно)
#send_telegram_notification() {
#    local message="✅ DevOps Portfolio Backup Completed
#📦 Name: $BACKUP_NAME  
#💾 Size: $(du -h $FINAL_FILE | cut -f1)
#📅 Date: $(date +'%Y-%m-%d %H:%M:%S')"
    
#    curl -s -X POST "https://api.telegram.org/bot8422673774:AAEAnEm-aQmsMncyuUPPIt081vbasiJvZ_0/sendMessage" \
#        -d "chat_id=874334948" \
#        -d "text=$message" >/dev/null 2>&1 && log "📱 Notification sent to Telegram"
#}

# Викликаємо нотифікацію
#send_telegram_notification