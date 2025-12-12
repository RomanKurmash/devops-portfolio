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
    }

    // =======================================================================
    // КОРИСНІ ФУНКЦІЇ BASH (Для активного очікування)
    // =======================================================================
    def wait_for_http = { serviceName, url, port ->
        sh """
            echo "⏳ Waiting for \$serviceName (Port:\$port) at \$url..."
            
            MAX_ATTEMPTS=20
            ATTEMPT=1
            
            while [ \$ATTEMPT -le \$MAX_ATTEMPTS ]; do
                # Перевірка з curl: -f (fail silently), -s (silent), -o (output to /dev/null), -m (max time)
                if curl -f -s -o /dev/null -m 5 \$url; then
                    echo "✅ \$serviceName is UP and responding (Attempt: \$ATTEMPT)"
                    return 0
                else
                    echo "💤 \$serviceName not ready, waiting 5 seconds (Attempt: \$ATTEMPT/\$MAX_ATTEMPTS)"
                    sleep 5
                    ATTEMPT=\$((ATTEMPT + 1))
                fi
            done
            
            echo "❌ ERROR: \$serviceName failed to start within the time limit!"
            exit 1
        """
    }

    // =======================================================================
    // ЕТАПИ
    // =======================================================================
    stages {
        stage('1. Checkout & Environment') {
            steps {
                echo '🚀 DevOps Portfolio CI/CD Pipeline'
                checkout scm
                
                sh """
                    echo "=== 🖥️ ENVIRONMENT ==="
                    echo "Build: #${env.BUILD_NUMBER}" // ВИПРАВЛЕННЯ: Використовуємо ${env.BUILD_NUMBER}
                    echo "OS: \$(uname -a)"
                    echo "Workspace: \$(pwd)"
                    echo "=== 🐳 DOCKER ==="
                    docker --version
                    docker-compose --version
                    echo "=== 📁 STRUCTURE ==="
                    find . -name "docker-compose*.yml" | head -10
                """
            }
        }
        
        stage('2. Cleanup Previous') {
            steps {
                sh """
                    echo "=== 🧹 CLEANUP ==="
                    cd ${INFRA_DIR}
                    # Зупиняємо старі контейнери
                    docker-compose -f docker-compose.apps.yml down --remove-orphans 2>/dev/null || echo "No previous apps stack found"
                    docker-compose -f docker-compose.monitoring.yml down --remove-orphans 2>/dev/null || echo "No previous monitoring stack found"
                    # Очищаємо непотрібні образи
                    docker image prune -f 2>/dev/null || true
                """
            }
        }
        
        stage('3. Prepare Infrastructure') {
            steps {
                sh """
                    echo "=== 🔧 INFRASTRUCTURE SETUP ==="
                    cd ${INFRA_DIR}
                    
                    # Створюємо мережі (використовуємо змінні Groovy всередині Bash через ${...})
                    echo "📡 Creating networks..."
                    docker network create ${COMPOSE_PROJECT_NAME}_apps-net 2>/dev/null || echo "Apps network exists"
                    docker network create ${COMPOSE_PROJECT_NAME}_monitor-net 2>/dev/null || echo "Monitor network exists"
                    
                    # Створюємо необхідні директорії
                    mkdir -p nginx/ssl mysql-exporter
                    
                    # Фікс MySQL Exporter конфігурації
                    if [ -f "mysql-exporter/my.cnf" ]; then
                        echo "⚙️ Configuring MySQL Exporter..."
                        # Використовуємо екранування \` для sed, щоб не було проблем з Groovy
                        sed -i '1s/^[^a-zA-Z[]*//' mysql-exporter/my.cnf
                    fi
                    
                    echo "✅ Infrastructure ready"
                """
            }
        }
        
        stage('4. Deploy Applications') {
            steps {
                sh """
                    echo "=== 🚀 DEPLOYING APPLICATIONS ==="
                    cd ${INFRA_DIR}
                    
                    echo "📦 Starting WordPress stack..."
                    # Використовуємо --build на етапі CI/CD, щоб завжди мати свіжий образ
                    docker-compose -f docker-compose.apps.yml up -d --build
                    
                    echo "🔍 Applications status:"
                    docker-compose -f docker-compose.apps.yml ps
                """
                
                // ОПТИМІЗАЦІЯ: Активне очікування замість sleep 45
                script {
                    wait_for_http("WordPress/Nginx", "http://127.0.0.1", 80)
                }

                sh """
                    echo "📝 Recent logs (WordPress):"
                    docker-compose -f docker-compose.apps.yml logs wordpress --tail=5 2>/dev/null || echo "No logs yet"
                """
            }
        }
        
        stage('5. Deploy Monitoring Stack') {
            steps {
                sh """
                    echo "=== 📊 DEPLOYING MONITORING ==="
                    cd ${INFRA_DIR}
                    
                    echo "📈 Starting monitoring services..."
                    docker-compose -f docker-compose.monitoring.yml up -d --build
                    
                    echo "🔍 Monitoring status:"
                    docker-compose -f docker-compose.monitoring.yml ps
                """
                
                // ОПТИМІЗАЦІЯ: Активне очікування замість sleep 30
                script {
                    // Очікуємо на Grafana
                    wait_for_http("Grafana", "http://127.0.0.1:3000", 3000)
                    // Очікуємо на Prometheus
                    wait_for_http("Prometheus", "http://127.0.0.1:9090", 9090)
                }

                sh """
                    echo "📝 Monitoring logs:"
                    docker-compose -f docker-compose.monitoring.yml logs prometheus --tail=5 2>/dev/null || echo "No logs yet"
                """
            }
        }
        
        stage('6. Health Checks & Validation') {
            steps {
                sh """
                    echo "=== ✅ HEALTH CHECKS ==="
                    cd ${INFRA_DIR}
                    
                    # Функція перевірки сервісів (використовуємо $1, $2, екрановані Groovy \$, і timeout)
                    check_service() {
                        local service="\$1"
                        local port="\$2"
                        local timeout=5
                        
                        if timeout \$timeout bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/\$port" 2>/dev/null; then
                            echo "✅ \$service (port:\$port) - HEALTHY"
                            return 0
                        else
                            echo "⚠️ \$service (port:\$port) - NOT RESPONDING (TCP check failed)"
                            return 1
                        fi
                    }
                    
                    echo "--- Service Availability (TCP Check) ---"
                    check_service "WordPress/Nginx" "80"
                    check_service "Grafana" "3000" 
                    check_service "Prometheus" "9090"
                    check_service "Alertmanager" "9093"
                    
                    echo ""
                    echo "--- Container Status ---"
                    # ... (інші перевірки без змін)
                    docker-compose -f docker-compose.apps.yml ps -a
                    echo ""
                    docker-compose -f docker-compose.monitoring.yml ps -a
                    
                    echo ""
                    echo "--- Resource Usage ---"
                    docker stats --no-stream --format "table {{.Name}}\\\\t{{.CPUPerc}}\\\\t{{.MemUsage}}\\\\t{{.NetIO}}" 2>/dev/null | head -10 || echo "Stats not available"
                """
            }
        }
        
        stage('7. Generate Report') {
            steps {
                sh """
                    echo "=== 📋 DEPLOYMENT REPORT ==="
                    
                    echo "📊 FINAL STATUS"
                    echo "Build: #${env.BUILD_NUMBER}" // Виправлено: Використання env.BUILD_NUMBER
                    echo "Timestamp: \$(date '+%Y-%m-%d %H:%M:%S')"
                    
                    cd ${INFRA_DIR}
                    echo ""
                    echo "🏗️ DEPLOYED SERVICES:"
                    # Екранування змінної Bash в Groovy: \$service перетворено на \\\$service
                    docker-compose -f docker-compose.apps.yml config --services | while read service; do
                        echo "  • \\\$service" 
                    done
                    
                    echo ""
                    echo "📈 MONITORING SERVICES:"
                    docker-compose -f docker-compose.monitoring.yml config --services | while read service; do
                        echo "  • \\\$service"
                    done
                    
                    echo ""
                    echo "🌐 ACCESS ENDPOINTS:"
                    echo "  WordPress:     http://localhost"
                    // ... (інші ендпоінти без змін)
                """
                
                // Збереження артефакту звіту
                sh """
                    cd ${INFRA_DIR}
                    echo "Deployment completed at \$(date)" > deployment_report.txt
                    docker-compose -f docker-compose.apps.yml ps >> deployment_report.txt
                    docker-compose -f docker-compose.monitoring.yml ps >> deployment_report.txt
                """
                archiveArtifacts artifacts: 'app-infrastructure/deployment_report.txt', fingerprint: true
            }
        }
    }
    
    // =======================================================================
    // ПОСТ-ОБРОБКА
    // =======================================================================
    post {
        always {
            echo "=== 🏁 PIPELINE EXECUTION COMPLETE ==="
            sh """
                echo "⏱️ Duration: ${currentBuild.durationString}"
                echo "📊 Result: ${currentBuild.currentResult}"
            """
        }
        
        // ... (success, failure, unstable, cleanup без змін)
        
        failure {
            echo "❌ DEPLOYMENT FAILED"
            echo "Check the logs above for details"
            
            sh """
                echo "--- ERROR DIAGNOSTICS ---"
                echo "Last container errors:"
                cd ${INFRA_DIR}
                # Використовуємо екранування \\\\ для grep, щоб не було проблем з Groovy
                docker-compose -f docker-compose.apps.yml logs --tail=20 2>/dev/null | grep -i "error\\\\|fail" | tail -5 || echo "No error logs"
                docker-compose -f docker-compose.monitoring.yml logs --tail=20 2>/dev/null | grep -i "error\\\\|fail" | tail -5 || echo "No error logs"
            """
        }
    }
}