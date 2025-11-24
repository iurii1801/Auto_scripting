pipeline {
    agent { label 'ansible-agent' }

    environment {
        REPO_URL       = 'https://github.com/iurii1801/Auto_scripting.git'
        REPO_BRANCH    = 'lab05'
        ANSIBLE_DIR    = 'lab05/ansible'
        INVENTORY_FILE = 'hosts.ini'
        PLAYBOOK_FILE  = 'setup_test_server.yml'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout Ansible repo') {
            steps {
                echo "Cloning repository with Ansible playbook (branch: ${env.REPO_BRANCH})..."
                git branch: "${env.REPO_BRANCH}", url: "${env.REPO_URL}"
            }
        }

        stage('Run Ansible playbook') {
            steps {
                echo "Running Ansible playbook ${env.PLAYBOOK_FILE}..."
                dir("${env.ANSIBLE_DIR}") {
                    sh """
                        ansible-playbook -i ${env.INVENTORY_FILE} ${env.PLAYBOOK_FILE}
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Ansible setup completed successfully!"
        }

        failure {
            echo "Ansible setup failed. Check console output for details."
        }
    }
}
