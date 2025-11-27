pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                sh '''
                    # Видаляємо теку, якщо вона існує, і клонуємо репозиторій
                    rm -rf devops-portfolio
                    git clone https://github.com/RomanKurmash/devops-portfolio.git
                    cd devops-portfolio
                    pwd
                    ls -la
                '''
            }
        }
    }
}