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
        // Розділяємо імена проектів, щоб уникнути конфліктів orphans
        APPS_PROJECT = 'portfolio-apps'
        MON_PROJECT = 'portfolio-monitoring'
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
        
        stage('2. Smart Cleanup') {
            steps {
                sh """
                    echo "=== CLEANUP ==="
                    cd ${INFRA_DIR}
                    docker compose -p ${APPS_PROJECT} -f docker-compose.apps.yml down --remove-orphans || true
                    docker compose -p ${MON_PROJECT} -f docker-compose.monitoring.yml down --remove-orphans || true
                    docker image prune -f
                """
            }
        }

       stage('3. Deploy Apps') {
            steps {
                sh """
                    echo "=== DEPLOYING APPS STACK ==="
                    cd ${INFRA_DIR}
                    docker compose -p ${APPS_PROJECT} -f docker-compose.apps.yml up -d --force-recreate
                """
            }
        }
        
        stage('4. Deploy Monitoring') {
            steps {
                sh """
                    echo "=== DEPLOYING MONITORING STACK ==="
                    cd ${INFRA_DIR}
                    docker compose -p ${MON_PROJECT} -f docker-compose.monitoring.yml build --no-cache
                    docker compose -p ${MON_PROJECT} -f docker-compose.monitoring.yml up -d --force-recreate --remove-orphans
                """
            }
        }

        stage('5. Health Checks') {
            steps {
                script {
                    echo "--- Waiting for services to breathe (20s) ---"
                    sleep 20
                    
                    def containers = [
                        'nginx-proxy', 'wordpress-app', 'mysql-db', 
                        'grafana', 'prometheus', 'telegram-bot'
                    ]
                    
                    for (container in containers) {
                        sh "docker ps -a --filter name=${container} --filter status=running --quiet | grep . || (echo '❌ ${container} is DOWN' && exit 1)"
                        echo "✅ ${container} is UP"
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo "🎉 DEPLOYMENT SUCCESSFUL!"
        }
        failure {
            echo "🚨 DEPLOYMENT FAILED"
        }
    }
}