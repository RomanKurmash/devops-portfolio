pipeline {
    agent any
    
    options {
        disableConcurrentBuilds()
        timeout(time: 20, unit: 'MINUTES')
        retry(1)
    }
    
    environment {
    COMPOSE_PROJECT_NAME = 'devops-portfolio'
    INFRA_DIR = 'app-infrastructure'
    NETWORK_NAME = 'apps-net'
    // Ця магія змусить Docker Compose бачити правильні шляхи
    PWD = sh(script: 'pwd', returnStdout: true).trim() 
    }

    stages {
        stage('1. Setup & Secrets') {
            steps {
                cleanWs()
                echo '🚀 DevOps Portfolio CI/CD Pipeline'
                checkout scm
                
                // Ін'єкція секретів
                withCredentials([file(credentialsId: 'devops-portfolio-env', variable: 'ENV_FILE')]) {
                    sh "cp \$ENV_FILE ${INFRA_DIR}/.env"
                }

                // Створення спільної мережі, якщо її немає
                sh "docker network inspect ${NETWORK_NAME} >/dev/null 2>&1 || docker network create ${NETWORK_NAME}"
            }
        }
        
        stage('2. Smart Cleanup') {
            steps {
                sh """
                    echo "=== CLEANUP ==="
                    cd ${INFRA_DIR}
                    
                    # Зупиняємо контейнери БЕЗ видалення вольюмів (щоб дані WP лишилися)
                    docker compose -f docker-compose.apps.yml down --remove-orphans || true
                    docker compose -f docker-compose.monitoring.yml down --remove-orphans || true
                    
                    # Чистимо тільки "сміття" (невикористовувані образи)
                    docker image prune -f
                """
            }
        }

       stage('3. Deploy Infrastructure') {
            steps {
                sh """
                    echo "=== VERIFYING FILES ==="
                    ls -la ${INFRA_DIR}/config/loki/
                    
                    echo "=== DEPLOYING STACK ==="
                    cd ${INFRA_DIR}
                    
                    # Примусово видаляємо контейнери Loki/Promtail, якщо вони зависли
                    docker compose -f docker-compose.apps.yml stop loki promtail || true
                    docker compose -f docker-compose.apps.yml rm -f loki promtail || true
                    
                    # Запуск
                    docker compose -f docker-compose.apps.yml up -d
                    docker compose -f docker-compose.monitoring.yml up -d --build
                """
            }
        }
        
        stage('Deploy Monitoring') {
    steps {
        // Використовуємо твій Secret file з Jenkins Credentials
        withCredentials([file(credentialsId: 'devops-portfolio-env', variable: 'ENV_FILE')]) {
            script {
                // 1. Копіюємо секрети в папку, де лежить docker-compose
                sh "cp \$ENV_FILE app-infrastructure/.env"
                
                // 2. Очищення та збірка: --no-cache гарантує, що Docker не візьме старі шари
                // Ми прибираємо назву конкретного сервісу, щоб це подіяло на ВCI сервіси у файлі
                sh "docker compose -f app-infrastructure/docker-compose.monitoring.yml build --no-cache"
                
                // 3. Деплой: --force-recreate змушує Docker перестворити контейнери, 
                // навіть якщо конфіг не змінився (це оновить змінні оточення)
                // Додаємо --remove-orphans, щоб прибрати старі "хвости", про які тобі писав Docker раніше
                sh "docker compose -f app-infrastructure/docker-compose.monitoring.yml up -d --force-recreate --remove-orphans"
            }
        }
    }
}

        stage('5. Health Checks') {
            steps {
                script {
                    echo "--- Waiting for services to breathe (15s) ---"
                    sleep 15
                    
                    def containers = [
                        'nginx-proxy', 'wordpress-app', 'mysql-db', 
                        'grafana', 'prometheus', 'telegram-bot'
                    ]
                    
                    for (container in containers) {
                        sh "docker inspect -f '{{.State.Running}}' ${container} | grep true || (echo '❌ ${container} is DOWN' && exit 1)"
                        echo "✅ ${container} is UP"
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo "🎉 DEPLOYMENT SUCCESSFUL! Site: http://localhost"
            // Тут можна додати відправку повідомлення в телеграм через твій скрипт
        }
        failure {
            echo "🚨 DEPLOYMENT FAILED"
        }
    }
}