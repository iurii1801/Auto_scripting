pipeline {
    agent { label 'ssh-agent' }

    environment {
        REPO_URL    = 'https://github.com/iurii1801/auto_scripting.git'
        REPO_BRANCH = 'lab05'
        PPROJECT_DIR = 'lab05/recipe-book'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout project') {
            steps {
                echo "Cloning auto_scripting repository..."
                git branch: "${REPO_BRANCH}", url: "${REPO_URL}"
            }
        }

        stage('Install Composer dependencies') {
            steps {
                echo "Installing Composer dependencies inside ${PROJECT_DIR}..."
                sh """
                    cd ${PROJECT_DIR}
                    composer install --no-interaction --prefer-dist --no-progress
                """
            }
        }

        stage('Run PHPUnit tests') {
            steps {
                echo "Running PHPUnit tests..."
                sh """
                    cd ${PROJECT_DIR}
                    mkdir -p build/logs
                    ./vendor/bin/phpunit \
                        --colors=always \
                        --log-junit build/logs/junit.xml
                """
            }
        }
    }

    post {
        always {
            echo "Archiving test reports..."
            archiveArtifacts artifacts: "${PROJECT_DIR}/build/logs/**/*.xml", fingerprint: true
            junit "${PROJECT_DIR}/build/logs/**/*.xml"
        }

        success {
            echo "Tests passed successfully!"
        }

        failure {
            echo "Tests failed! Check console output and reports."
        }
    }
}
