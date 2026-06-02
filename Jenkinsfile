pipeline {
    agent any
    environment {
        INFRA_DIR = 'app-infrastructure'
        NETWORK_NAME = 'apps-net'
        COMPOSE_PROJECT_NAME = 'devops-portfolio'
    }

    stages {
        stage('1. Подготовка') {
            steps {
                cleanWs()
                checkout scm
                withCredentials([file(credentialsId: 'devops-portfolio-env', variable: 'ENV_FILE')]) {
                    sh "cp \$ENV_FILE ${INFRA_DIR}/.env"
                }
                sh "docker network inspect monitor-net >/dev/null 2>&1 || docker network create monitor-net"
                sh "docker network inspect apps-net >/dev/null 2>&1 || docker network create apps-net"
            }
        }
        
        stage('2. Очистка конфліктів') {
            steps {
                sh """
                    cd ${INFRA_DIR}
                    docker compose -f docker-compose.apps.yml down --remove-orphans || true
                    docker compose -f docker-compose.monitoring.yml down --remove-orphans || true
                    docker rm -f mysql-exporter node-exporter nginx-exporter telegram-bot prometheus grafana mysql-db wordpress-app nginx-proxy ai-adapter || true
                """
            }
        }

        stage('3. Full Deploy') {
            steps {
                sh """
                    cd ${INFRA_DIR}
                    docker compose -f docker-compose.apps.yml up -d --force-recreate
                    docker compose -f docker-compose.monitoring.yml build --no-cache
                    docker compose -f docker-compose.monitoring.yml up -d --force-recreate
                """
            }
        }

        stage('4. Generate PDFs') {
            steps {
                sh """
                    docker run --rm -v \$(pwd):/workspace -w /workspace python:3.12-slim sh -c "pip install --no-cache-dir markdown xhtml2pdf requests && python3 scripts/export_pdf.py"
                """
            }
        }

        stage('5. Health Checks') {
            steps {
                script {
                    sleep 25
                    def containers = ['nginx-proxy', 'mysql-db', 'prometheus', 'telegram-bot', 'mysql-exporter', 'ai-adapter']
                    for (c in containers) {
                        sh "docker ps -f name=^/${c}\$ -f status=running --quiet | grep . || (echo '❌ ${c} is DOWN' && exit 1)"
                    }
                }
            }
        }
    }
}