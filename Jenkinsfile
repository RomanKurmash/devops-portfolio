pipeline {
    agent any
    
    options {
        disableConcurrentBuilds()
        timeout(time: 20, unit: 'MINUTES')
    }
    
    environment {
        COMPOSE_PROJECT_NAME = 'devops-portfolio'
        INFRA_DIR = 'app-infrastructure'
    }
    
    stages {
        stage('📥 Checkout & Setup') {
            steps {
                echo '🚀 Starting CI/CD Pipeline from SCM'
                
                script {
                    // Автоматичний checkout через SCM - НЕ ДОДАВАТИ ДОДАТКОВИЙ GIT CHECKOUT
                    echo "Workspace: ${env.WORKSPACE}"
                }
                
                sh '''
                    echo "=== 📁 WORKSPACE CONTENTS ==="
                    pwd
                    ls -la
                    echo "=== 🐳 DOCKER CHECK ==="
                    docker --version
                    docker-compose --version
                    docker ps
                '''
            }
        }
        
        stage('🚀 Deploy Stack') {
            steps {
                sh """
                    echo "=== 🚀 DEPLOYING STACK ==="
                    cd ${INFRA_DIR}
                    
                    # Створюємо мережі
                    docker network create ${COMPOSE_PROJECT_NAME}_apps-net 2>/dev/null || echo "Network exists"
                    docker network create ${COMPOSE_PROJECT_NAME}_monitor-net 2>/dev/null || echo "Network exists"
                    
                    # Запускаємо додатки
                    docker-compose -f docker-compose.apps.yml up -d
                    sleep 30
                    
                    # Запускаємо моніторинг
                    docker-compose -f docker-compose.monitoring.yml up -d  
                    sleep 20
                    
                    # Перевіряємо статус
                    echo "=== STATUS ==="
                    docker-compose -f docker-compose.apps.yml ps
                    docker-compose -f docker-compose.monitoring.yml ps
                """
            }
        }
    }
    
    post {
        success {
            echo "✅ PIPELINE SUCCESS"
            sh """
                echo "=== QUICK ACCESS ==="
                echo "WordPress: http://localhost"
                echo "Grafana: http://localhost:3000"
                echo "Prometheus: http://localhost:9090"
            """
        }
        failure {
            echo "❌ PIPELINE FAILED"
        }
    }
}