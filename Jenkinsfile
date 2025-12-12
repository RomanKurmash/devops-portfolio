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
                // 1. ОЧИЩЕННЯ: Видаляємо все старе сміття (в т.ч. помилкові папки Docker)
                cleanWs()
                
                echo 'DevOps Portfolio CI/CD Pipeline'
                checkout scm
                
                sh """
                    echo "=== ENVIRONMENT ==="
                    echo "Build: #${env.BUILD_NUMBER}"
                    echo "Workspace: \$(pwd)"
                    echo "=== DOCKER ==="
                    docker --version
                    docker-compose --version
                    
                    # Перевіряємо, чи Git справді стягнув файли конфігів
                    echo "=== CONFIG CHECK ==="
                    ls -la ${INFRA_DIR}/prometheus/ || echo "Prometheus folder missing"
                    ls -la ${INFRA_DIR}/alertmanager/ || echo "Alertmanager folder missing"
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
                    
                    # Видаляємо мережі
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
                    
                    echo "Creating folders..."
                    mkdir -p nginx/ssl mysql-exporter prometheus alertmanager
                    
                    # --- ВАЛІДАЦІЯ КОНФІГІВ ---
                    # Якщо файлу немає, ми зупиняємо пайплайн тут, а не чекаємо помилки Docker
                    if [ ! -f prometheus/prometheus.yml ]; then
                        echo "❌ ERROR: prometheus.yml not found! Git did not pull it."
                        exit 1
                    fi
                    
                    if [ ! -f alertmanager/alertmanager.yml ]; then
                         echo "❌ ERROR: alertmanager.yml not found! Git did not pull it."
                         exit 1
                    fi
                    # ---------------------------

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
                    docker-compose -f docker-compose.apps.yml build --no-cache nginx
                    docker-compose -f docker-compose.apps.yml up -d
                    
                    echo "Applications status:"
                    docker-compose -f docker-compose.apps.yml ps
                """
                
                script {
                    sh """
                        echo "Checking Nginx health..."
                        sleep 10
                        docker exec nginx-proxy nginx -t
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
                
                script {
                    sh """
                        wait_for_http() {
                            local service="\$1"
                            local url="\$2"
                            MAX_ATTEMPTS=20
                            ATTEMPT=1
                            while [ \$ATTEMPT -le \$MAX_ATTEMPTS ]; do
                                if curl -f -s -o /dev/null -m 5 \$url; then
                                    echo "Service \$service is UP (Attempt: \$ATTEMPT)"
                                    return 0
                                else
                                    echo "Waiting for \$service... (\$ATTEMPT/\$MAX_ATTEMPTS)"
                                    sleep 5
                                    ATTEMPT=\$((ATTEMPT + 1))
                                fi
                            done
                            echo "ERROR: Service \$service failed to start!"
                            exit 1
                        }

                        wait_for_http "Grafana" "http://127.0.0.1:3000"
                        wait_for_http "Prometheus" "http://127.0.0.1:9090"
                    """
                }

                sh """
                    echo "Monitoring logs:"
                    cd ${INFRA_DIR}
                    docker-compose -f docker-compose.monitoring.yml logs prometheus --tail=5 2>/dev/null || echo "No logs yet"
                """
            }
        }
        
        stage('6. Health Checks & Validation') {
            steps {
                sh """
                    echo "=== HEALTH CHECKS ==="
                    cd ${INFRA_DIR}
                    
                    check_service() {
                        local service="\$1"
                        local port="\$2"
                        if timeout 5 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/\$port" 2>/dev/null; then
                            echo "Service \$service (:\$port) - HEALTHY"
                            return 0
                        else
                            echo "Service \$service (:\$port) - NOT RESPONDING"
                            return 1
                        fi
                    }
                    
                    check_service "WordPress/Nginx" "80"
                    check_service "Grafana" "3000" 
                    check_service "Prometheus" "9090"
                    check_service "Alertmanager" "9093"
                    
                    echo ""
                    docker stats --no-stream --format "table {{.Name}}\\\\t{{.CPUPerc}}\\\\t{{.MemUsage}}" 2>/dev/null | head -10 || echo "Stats unavailable"
                """
            }
        }
        
        stage('7. Generate Report') {
            steps {
                sh """
                    echo "=== DEPLOYMENT REPORT ==="
                    cd ${INFRA_DIR}
                    
                    echo "Deployment completed at \$(date)" > deployment_report.txt
                    docker-compose -f docker-compose.apps.yml ps >> deployment_report.txt
                    docker-compose -f docker-compose.monitoring.yml ps >> deployment_report.txt
                """
                archiveArtifacts artifacts: "${INFRA_DIR}/deployment_report.txt", fingerprint: true
            }
        }
    }
    
    post {
        always {
            echo "Result: ${currentBuild.currentResult}"
        }
        success {
            echo "DEPLOYMENT SUCCESSFUL"
        }
        failure {
            echo "DEPLOYMENT FAILED"
            sh """
                echo "--- ERROR DIAGNOSTICS ---"
                cd ${INFRA_DIR} || true
                echo "LAST LOGS:"
                docker-compose -f docker-compose.monitoring.yml logs --tail=20 2>/dev/null || true
            """
        }
    }
}