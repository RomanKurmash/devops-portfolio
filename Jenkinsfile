pipeline {
    agent any
    
    options {
        disableConcurrentBuilds()
        timeout(time: 20, unit: 'MINUTES')
        retry(1)
    }
    
    environment {
        INFRA_DIR = 'app-infrastructure'
        NETWORK_NAME = 'apps-net'
        // Використовуємо ОДИН проект, щоб Docker розумів логіку заміни контейнерів
        COMPOSE_PROJECT_NAME = 'devops-portfolio'
    }

    stages {
        stage('1. Setup & Secrets') {
            steps {
                cleanWs()
                echo '🚀 DevOps Portfolio CI/CD Pipeline'
                checkout scm
                
                withCredentials([file(credentialsId: 'devops-portfolio-env', variable: 'ENV_FILE')]) {
                    sh "cp \$ENV_FILE ${INFRA_DIR}/.env"
                }

                sh "docker network inspect ${NETWORK_NAME} >/dev/null 2>&1 || docker network create ${NETWORK_NAME}"
            }
        }
        
        stage('2. Force Cleanup') {
            steps {
                script {
                    echo "=== САНІТАРНА ОЧИСТКА ==="
                    // Список твоїх фіксованих імен контейнерів
                    def containers = [
                        'nginx-proxy', 'wordpress-app', 'mysql-db', 'loki', 'promtail', 'cloudflared-tunnel',
                        'grafana', 'prometheus', 'telegram-bot', 'mysql-exporter', 'node-exporter', 'nginx-exporter', 'alertmanager'
                    ]
                    
                    // Примусово видаляємо їх, щоб звільнити імена для нових проектів
                    sh "docker rm -f ${containers.join(' ')} || true"
                    sh "docker image prune -f"
                }
            }
        }

       stage('3. Deploy Infrastructure') {
            steps {
                sh """
                    echo "=== DEPLOYING STACKS ==="
                    cd ${INFRA_DIR}
                    
                    # Деплоїмо додатки
                    docker compose -f docker-compose.apps.yml up -d
                    
                    # Деплоїмо моніторинг (з перезбіркою без кешу)
                    docker compose -f docker-compose.monitoring.yml build --no-cache
                    docker compose -f docker-compose.monitoring.yml up -d --force-recreate
                """
            }
        }
        
        stage('4. Health Checks') {
            steps {
                script {
                    echo "--- Waiting for services to breathe (20s) ---"
                    sleep 20
                    
                    def containers = [
                        'nginx-proxy', 'wordpress-app', 'mysql-db', 
                        'grafana', 'prometheus', 'telegram-bot'
                    ]
                    
                    for (container in containers) {
                        sh "docker ps -a --filter name=^/${container}\$ --filter status=running --quiet | grep . || (echo '❌ ${container} is DOWN' && exit 1)"
                        echo "✅ ${container} is UP"
                    }
                }
            }
        }
    }
    
    post {
        success { echo "🎉 DEPLOYMENT SUCCESSFUL!" }
        failure { echo "🚨 DEPLOYMENT FAILED" }
    }
}