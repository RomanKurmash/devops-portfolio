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
                cleanWs()
                echo 'DevOps Portfolio CI/CD Pipeline'
                checkout scm
                
                // === МАГІЯ ТУТ ===
                // Ми дістаємо секретний файл з Jenkins і кладемо його як .env
                withCredentials([file(credentialsId: 'devops-portfolio-env', variable: 'ENV_FILE')]) {
                    sh """
                        # Копіюємо секретний файл у потрібне місце
                        cp \$ENV_FILE ${INFRA_DIR}/.env
                        
                        echo "✅ .env file injected successfully"
                    """
                }
                // =================
                
                sh """
                    echo "=== ENVIRONMENT ==="
                    echo "Build: #${env.BUILD_NUMBER}"
                    echo "Workspace: \$(pwd)"
                    echo "=== DOCKER ==="
                    docker --version
                    docker-compose --version
                    
                    # Перевіряємо, чи файл на місці (не показуючи вміст!)
                    ls -la ${INFRA_DIR}/.env
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
                    # Більше не треба білдити nginx, ми качаємо готовий образ
                    docker-compose -f docker-compose.apps.yml up -d
                    
                    echo "Applications status:"
                    docker-compose -f docker-compose.apps.yml ps
                """
                
                script {
                    sh """
                        echo "Checking Nginx Proxy health..."
                        # Чекаємо 10 секунд
                        sleep 10
                        
                        # Перевіряємо, чи контейнер запущений (найбезпечніший метод)
                        if [ "\$(docker inspect -f '{{.State.Running}}' nginx-proxy 2>/dev/null)" = "true" ]; then
                            echo "✅ Nginx Proxy is RUNNING"
                        else
                            echo "❌ Nginx Proxy failed to start"
                            docker logs nginx-proxy --tail 20
                            exit 1
                        fi
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
                    # Додаємо --build, щоб точно перезібрався бот
                    docker-compose -f docker-compose.monitoring.yml up -d --build
                    
                    echo "Monitoring status:"
                    docker-compose -f docker-compose.monitoring.yml ps
                """
                
                script {
                    sh """
                        echo "Checking Grafana readiness via logs..."
                        # Чекаємо до 60 секунд, поки в логах не з'явиться повідомлення про успішний старт HTTP сервера
                        timeout 60s bash -c 'until docker logs grafana 2>&1 | grep -q "HTTP Server Listen"; do echo "Waiting for Grafana..."; sleep 2; done'
                        
                        echo "Checking Prometheus readiness via logs..."
                        timeout 60s bash -c 'until docker logs prometheus 2>&1 | grep -q "Server is ready to receive web requests"; do echo "Waiting for Prometheus..."; sleep 2; done'
                        
                        echo "✅ Monitoring services are up!"
                    """
                }

                sh """
                    echo "Monitoring logs snippet:"
                    docker logs grafana --tail 5
                """
            }
        }
        
        stage('6. Health Checks & Validation') {
            steps {
                sh """
                    echo "=== HEALTH CHECKS ==="
                    cd ${INFRA_DIR}
                    
                    # Функція перевірки статусу контейнера
                    check_container_status() {
                        local name="\$1"
                        # Використовуємо docker inspect, щоб перевірити, чи контейнер Running=true
                        if [ "\$(docker inspect -f '{{.State.Running}}' \$name 2>/dev/null)" = "true" ]; then
                            echo "✅ Container \$name is RUNNING"
                        else
                            echo "❌ Container \$name is NOT RUNNING or missing"
                            exit 1
                        fi
                    }
                    
                    echo "--- Service Status Verification ---"
                    check_container_status "nginx-proxy"
                    check_container_status "wordpress-app"
                    check_container_status "mysql-db"
                    
                    check_container_status "grafana"
                    check_container_status "prometheus"
                    check_container_status "alertmanager"
                    check_container_status "telegram-bot"
                    
                    echo ""
                    echo "--- Resource Usage ---"
                    # Виводимо статистику споживання ресурсів
                    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -15
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