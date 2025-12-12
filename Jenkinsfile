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

    stages {
        stage('1. Checkout & Environment') {
            steps {
                echo 'DevOps Portfolio CI/CD Pipeline'
                checkout scm
                
                sh """
                    echo "=== ENVIRONMENT ==="
                    echo "Build: #${env.BUILD_NUMBER}"
                    echo "OS: \$(uname -a)"
                    echo "Workspace: \$(pwd)"
                    echo "=== DOCKER ==="
                    docker --version
                    docker-compose --version
                    echo "=== STRUCTURE ==="
                    find . -name "docker-compose*.yml" | head -10
                """
            }
        }
        
        stage('2. Cleanup Previous') {
            steps {
                sh """
                    echo "=== CLEANUP ==="
                    cd ${INFRA_DIR}
                    
                    # Зупиняємо контейнери
                    docker-compose -f docker-compose.apps.yml down --remove-orphans || true
                    docker-compose -f docker-compose.monitoring.yml down --remove-orphans || true
                    
                    # !ВАЖЛИВО: Видаляємо старі мережі, які ми створили вручну, щоб вони не заважали
                    docker network rm devops-portfolio_apps-net || true
                    docker network rm devops-portfolio_monitor-net || true
                    
                    docker image prune -f
                """
            }
        }

        stage('3. Prepare Infrastructure') {
            steps {
                sh """
                    echo "=== INFRASTRUCTURE SETUP ==="
                    cd ${INFRA_DIR}
                    
                    # --- ВИПРАВЛЕННЯ ПОМИЛКИ DOCKER ---
                    # Якщо prometheus.yml існує як папка (через помилку монтування), видаляємо її
                    if [ -d prometheus/prometheus.yml ]; then
                        echo "Deleting directory 'prometheus.yml' created by Docker..."
                        rm -rf prometheus/prometheus.yml
                    fi
                    # ----------------------------------

                    echo "Creating folders..."
                    mkdir -p nginx/ssl mysql-exporter prometheus
                    
                    if [ -f mysql-exporter/my.cnf ]; then
                        echo "Configuring MySQL Exporter..."
                        sed -i '1s/^[^a-zA-Z[]*//' mysql-exporter/my.cnf
                    fi
                    
                    echo "Infrastructure ready"
                """
            }
        }
        
        stage('4. Deploy Applications') {
    steps {
        sh """
            echo "=== DEPLOYING APPLICATIONS ==="
            cd ${INFRA_DIR}
            
            echo "Starting WordPress stack..."
            # Перезбираємо Nginx без кешу, щоб підтягнути нові конфіги
            docker-compose -f docker-compose.apps.yml build --no-cache nginx
            docker-compose -f docker-compose.apps.yml up -d
            
            echo "Applications status:"
            docker-compose -f docker-compose.apps.yml ps
        """
        
        script {
            sh """
                echo "Checking Nginx health..."
                
                # Даємо час на ініціалізацію
                sleep 10
                
                # Перевіряємо конфігурацію (про всяк випадок)
                docker exec nginx-proxy nginx -t
                
                # FIX: Використовуємо 127.0.0.1 замість localhost, щоб Alpine не ломився через IPv6
                docker exec nginx-proxy wget --spider -q http://127.0.0.1 || exit 1
            """
        }

        sh """
            echo "Recent logs (WordPress):"
            cd ${INFRA_DIR}
            docker-compose -f docker-compose.apps.yml logs wordpress --tail=5 2>/dev/null || echo "No logs yet"
        """
    }
}
        
        stage('5. Deploy Monitoring Stack') {
            steps {
                sh """
                    echo "=== DEPLOYING MONITORING ==="
                    cd ${INFRA_DIR}
                    
                    echo "Starting monitoring services..."
                    docker-compose -f docker-compose.monitoring.yml up -d --build
                    
                    echo "Monitoring status:"
                    docker-compose -f docker-compose.monitoring.yml ps
                """
                
                // ОПТИМІЗАЦІЯ: Активне очікування замість sleep 30
                script {
                    sh """
                        # Функція активного очікування (дублюємо, щоб бути впевненими, що вона доступна)
                        wait_for_http() {
                            local service="\$1"
                            local url="\$2"
                            
                            MAX_ATTEMPTS=20
                            ATTEMPT=1
                            
                            while [ \$ATTEMPT -le \$MAX_ATTEMPTS ]; do
                                if curl -f -s -o /dev/null -m 5 \$url; then
                                    echo "Service \$service is UP and responding (Attempt: \$ATTEMPT)"
                                    return 0
                                else
                                    echo "Service \$service not ready, waiting 5 seconds (Attempt: \$ATTEMPT/\$MAX_ATTEMPTS)"
                                    sleep 5
                                    ATTEMPT=\$((ATTEMPT + 1))
                                fi
                            done
                            
                            echo "ERROR: Service \$service failed to start within the time limit!"
                            exit 1
                        }

                        # Очікуємо на Grafana та Prometheus
                        wait_for_http "Grafana" "http://127.0.0.1:3000"
                        wait_for_http "Prometheus" "http://127.0.0.1:9090"
                    """
                }

                sh """
                    echo "Monitoring logs:"
                    docker-compose -f docker-compose.monitoring.yml logs prometheus --tail=5 2>/dev/null || echo "No logs yet"
                """
            }
        }
        
        stage('6. Health Checks & Validation') {
            steps {
                sh """
                    echo "=== HEALTH CHECKS ==="
                    cd ${INFRA_DIR}
                    
                    # Функція перевірки сервісів
                    check_service() {
                        local service="\$1"
                        local port="\$2"
                        local timeout=5
                        
                        if timeout \$timeout bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/\$port" 2>/dev/null; then
                            echo "Service \$service (port:\$port) - HEALTHY"
                            return 0
                        else
                            echo "Service \$service (port:\$port) - NOT RESPONDING (TCP check failed)"
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
                    echo "=== DEPLOYMENT REPORT ==="
                    
                    echo "FINAL STATUS"
                    echo "Build: #${env.BUILD_NUMBER}"
                    echo "Timestamp: \$(date '+%Y-%m-%d %H:%M:%S')"
                    
                    cd ${INFRA_DIR}
                    echo ""
                    echo "DEPLOYED SERVICES:"
                    docker-compose -f docker-compose.apps.yml config --services | while read service; do
                        echo "  • \\\$service" 
                    done
                    
                    echo ""
                    echo "MONITORING SERVICES:"
                    docker-compose -f docker-compose.monitoring.yml config --services | while read service; do
                        echo "  • \\\$service"
                    done
                    
                    echo ""
                    echo "ACCESS ENDPOINTS:"
                    echo "  WordPress:     http://localhost"
                    echo "  Grafana:       http://localhost:3000"
                    echo "  Prometheus:    http://localhost:9090"
                    echo "  Alertmanager:  http://localhost:9093"
                    echo "  Jenkins:       http://localhost:8080"
                    
                    echo ""
                    echo "MAINTENANCE COMMANDS:"
                    echo "  View logs:     cd ${INFRA_DIR} && docker-compose logs -f"
                    echo "  Stop all:      cd ${INFRA_DIR} && docker-compose -f docker-compose.apps.yml down && docker-compose -f docker-compose.monitoring.yml down"
                    echo "  Restart:       cd ${INFRA_DIR} && docker-compose restart"
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
    
    post {
        always {
            echo "=== PIPELINE EXECUTION COMPLETE ==="
            sh """
                echo "Duration: ${currentBuild.durationString}"
                echo "Result: ${currentBuild.currentResult}"
            """
        }
        
        success {
            echo "DEPLOYMENT SUCCESSFUL"
            echo "All services are deployed and running"
        }
        
        failure {
            echo "DEPLOYMENT FAILED"
            echo "Check the logs above for details"
            
            sh '''
                    echo "--- ERROR DIAGNOSTICS ---"
                    cd app-infrastructure
                    echo "LOGS FOR NGINX:"
                    docker-compose -f docker-compose.apps.yml logs --tail=50 nginx

                    echo "LOGS FOR WORDPRESS:"
                    docker-compose -f docker-compose.apps.yml logs --tail=20 wordpress
            '''
        }
        
        unstable {
            echo "DEPLOYMENT WITH WARNINGS"
            echo "Some services may not be fully healthy"
        }
        
        cleanup {
            echo "Cleanup completed"
        }
    }
}