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
        BUILD_NUMBER = "${env.BUILD_ID}"
    }
    
    stages {
        stage('📥 Checkout & Environment') {
            steps {
                echo '🚀 DevOps Portfolio CI/CD Pipeline'
                checkout scm
                
                sh '''
                    echo "=== 🖥️ ENVIRONMENT ==="
                    echo "Build: #${BUILD_NUMBER}"
                    echo "OS: $(uname -a)"
                    echo "Workspace: $(pwd)"
                    echo "=== 🐳 DOCKER ==="
                    docker --version
                    docker-compose --version
                    echo "=== 📁 STRUCTURE ==="
                    find . -name "docker-compose*.yml" | head -10
                '''
            }
        }
        
        stage('🧹 Cleanup Previous') {
            steps {
                sh """
                    echo "=== 🧹 CLEANUP ==="
                    cd ${INFRA_DIR}
                    
                    # Зупиняємо старі контейнери
                    docker-compose -f docker-compose.apps.yml down --remove-orphans 2>/dev/null || echo "No previous apps"
                    docker-compose -f docker-compose.monitoring.yml down --remove-orphans 2>/dev/null || echo "No previous monitoring"
                    
                    # Очищаємо непотрібні образи
                    docker image prune -f 2>/dev/null || true
                """
            }
        }
        
        stage('🔧 Prepare Infrastructure') {
            steps {
                sh """
                    echo "=== 🔧 INFRASTRUCTURE SETUP ==="
                    cd ${INFRA_DIR}
                    
                    # Створюємо мережі
                    echo "📡 Creating networks..."
                    docker network create ${COMPOSE_PROJECT_NAME}_apps-net 2>/dev/null || echo "Apps network exists"
                    docker network create ${COMPOSE_PROJECT_NAME}_monitor-net 2>/dev/null || echo "Monitor network exists"
                    
                    # Створюємо необхідні директорії
                    mkdir -p nginx/ssl mysql-exporter
                    
                    # Фікс MySQL Exporter конфігурації
                    if [ -f "mysql-exporter/my.cnf" ]; then
                        echo "⚙️ Configuring MySQL Exporter..."
                        sed -i '1s/^[^a-zA-Z[]*//' mysql-exporter/my.cnf
                    fi
                    
                    echo "✅ Infrastructure ready"
                """
            }
        }
        
        stage('🚀 Deploy Applications') {
            steps {
                sh """
                    echo "=== 🚀 DEPLOYING APPLICATIONS ==="
                    cd ${INFRA_DIR}
                    
                    echo "📦 Starting WordPress stack..."
                    docker-compose -f docker-compose.apps.yml up -d --build
                    
                    echo "⏳ Waiting for applications (45s)..."
                    sleep 45
                    
                    echo "🔍 Applications status:"
                    docker-compose -f docker-compose.apps.yml ps
                    
                    # Логи для налагодження
                    echo "📝 Recent logs:"
                    docker-compose -f docker-compose.apps.yml logs --tail=5 2>/dev/null || echo "No logs yet"
                """
            }
        }
        
        stage('📊 Deploy Monitoring Stack') {
            steps {
                sh """
                    echo "=== 📊 DEPLOYING MONITORING ==="
                    cd ${INFRA_DIR}
                    
                    echo "📈 Starting monitoring services..."
                    docker-compose -f docker-compose.monitoring.yml up -d --build
                    
                    echo "⏳ Waiting for monitoring (30s)..."
                    sleep 30
                    
                    echo "🔍 Monitoring status:"
                    docker-compose -f docker-compose.monitoring.yml ps
                    
                    echo "📝 Monitoring logs:"
                    docker-compose -f docker-compose.monitoring.yml logs --tail=5 2>/dev/null || echo "No logs yet"
                """
            }
        }
        
        stage('✅ Health Checks & Validation') {
            steps {
                sh """
                    echo "=== ✅ HEALTH CHECKS ==="
                    cd ${INFRA_DIR}
                    
                    # Функція перевірки сервісів
                    check_service() {
                        local service=\$1
                        local port=\$2
                        local timeout=5
                        
                        if timeout \$timeout bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/\$port" 2>/dev/null; then
                            echo "✅ \$service (port:\$port) - HEALTHY"
                            return 0
                        else
                            echo "⚠️ \$service (port:\$port) - NOT RESPONDING"
                            return 1
                        fi
                    }
                    
                    echo "--- Service Availability ---"
                    check_service "WordPress" "80"
                    check_service "Grafana" "3000" 
                    check_service "Prometheus" "9090"
                    check_service "Alertmanager" "9093"
                    
                    echo ""
                    echo "--- Container Status ---"
                    echo "📦 APPLICATIONS:"
                    docker-compose -f docker-compose.apps.yml ps -a
                    echo ""
                    echo "📊 MONITORING:"
                    docker-compose -f docker-compose.monitoring.yml ps -a
                    
                    echo ""
                    echo "--- Resource Usage ---"
                    docker stats --no-stream --format "table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}" 2>/dev/null | head -10 || echo "Stats not available"
                """
            }
        }
        
        stage('📋 Generate Report') {
            steps {
                sh """
                    echo "=== 📋 DEPLOYMENT REPORT ==="
                    
                    echo "📊 FINAL STATUS"
                    echo "Build: #${BUILD_NUMBER}"
                    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
                    
                    cd ${INFRA_DIR}
                    echo ""
                    echo "🏗️ DEPLOYED SERVICES:"
                    docker-compose -f docker-compose.apps.yml config --services | while read service; do
                        echo "  • \${service}"
                    done
                    
                    echo ""
                    echo "📈 MONITORING SERVICES:"
                    docker-compose -f docker-compose.monitoring.yml config --services | while read service; do
                        echo "  • \${service}"
                    done
                    
                    echo ""
                    echo "🌐 ACCESS ENDPOINTS:"
                    echo "  WordPress:     http://localhost"
                    echo "  Grafana:       http://localhost:3000"
                    echo "  Prometheus:    http://localhost:9090"
                    echo "  Alertmanager:  http://localhost:9093"
                    echo "  Jenkins:       http://localhost:8080"
                    
                    echo ""
                    echo "🔧 MAINTENANCE COMMANDS:"
                    echo "  View logs:     cd ${INFRA_DIR} && docker-compose logs -f"
                    echo "  Stop all:      cd ${INFRA_DIR} && docker-compose -f docker-compose.apps.yml down && docker-compose -f docker-compose.monitoring.yml down"
                    echo "  Restart:       cd ${INFRA_DIR} && docker-compose restart"
                """
                
                // Збереження артефакту звіту
                sh """
                    cd ${INFRA_DIR}
                    echo "Deployment completed at $(date)" > deployment_report.txt
                    docker-compose -f docker-compose.apps.yml ps >> deployment_report.txt
                    docker-compose -f docker-compose.monitoring.yml ps >> deployment_report.txt
                """
                archiveArtifacts artifacts: 'app-infrastructure/deployment_report.txt', fingerprint: true
            }
        }
    }
    
    post {
        always {
            echo "=== 🏁 PIPELINE EXECUTION COMPLETE ==="
            sh """
                echo "⏱️ Duration: ${currentBuild.durationString}"
                echo "📊 Result: ${currentBuild.currentResult}"
            """
        }
        
        success {
            echo "✅ DEPLOYMENT SUCCESSFUL"
            echo "All services are deployed and running"
            
            // Можна додати сповіщення:
            // - Email
            // - Telegram/Slack
            // - Webhook
        }
        
        failure {
            echo "❌ DEPLOYMENT FAILED"
            echo "Check the logs above for details"
            
            sh """
                echo "--- ERROR DIAGNOSTICS ---"
                echo "Last container errors:"
                cd ${INFRA_DIR}
                docker-compose -f docker-compose.apps.yml logs --tail=20 2>/dev/null | grep -i "error\\|fail" | tail -5 || echo "No error logs"
                docker-compose -f docker-compose.monitoring.yml logs --tail=20 2>/dev/null | grep -i "error\\|fail" | tail -5 || echo "No error logs"
            """
        }
        
        unstable {
            echo "⚠️ DEPLOYMENT WITH WARNINGS"
            echo "Some services may not be fully healthy"
        }
        
        cleanup {
            echo "🧹 Cleanup completed"
        }
    }
}