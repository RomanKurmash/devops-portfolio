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
                    docker-compose -f docker-compose.apps.yml down --remove-orphans || true
                    docker-compose -f docker-compose.monitoring.yml down --remove-orphans || true
                    
                    # Чистимо тільки "сміття" (невикористовувані образи)
                    docker image prune -f
                """
            }
        }

        stage('3. Deploy Infrastructure') {
            steps {
                sh """
                    echo "=== DEPLOYING STACK ==="
                    cd ${INFRA_DIR}
                    
                    # Запуск Додатків
                    docker-compose -f docker-compose.apps.yml up -d
                    
                    # Запуск Моніторингу з перезбіркою бота
                    docker-compose -f docker-compose.monitoring.yml up -d --build
                """
            }
        }
        
        stage('4. Health Checks') {
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