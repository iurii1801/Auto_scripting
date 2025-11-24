pipeline {
    agent { label 'ssh-agent' }

    environment {
        REPO_URL    = 'https://github.com/iurii1801/auto_scripting.git'
        REPO_BRANCH = 'lab05'
        // Путь к PHP-проекту внутри репозитория
        PROJECT_DIR = 'lab05/recipe-book'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout project') {
            steps {
                echo "Cloning auto_scripting repository (branch: ${env.REPO_BRANCH})..."
                git branch: "${env.REPO_BRANCH}", url: "${env.REPO_URL}"
            }
        }

        stage('Install Composer dependencies') {
            steps {
                echo "Installing Composer dependencies inside ${env.PROJECT_DIR}..."
                dir("${env.PROJECT_DIR}") {
                    sh '''
                        composer install --no-interaction --prefer-dist --no-progress
                    '''
                }
            }
        }

        stage('Run PHPUnit tests') {
            steps {
                echo "Running PHPUnit tests..."
                dir("${env.PROJECT_DIR}") {
                    sh '''
                        mkdir -p build/logs
                        ./vendor/bin/phpunit \
                          --colors=always \
                          --log-junit build/logs/junit.xml
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Archiving test reports..."
            archiveArtifacts artifacts: "${env.PROJECT_DIR}/build/logs/**/*.xml", fingerprint: true
            junit "${env.PROJECT_DIR}/build/logs/**/*.xml"
        }

        success {
            echo "Tests passed successfully!"
        }

        failure {
            echo "Tests failed! Check console output and reports."
        }
    }
}
