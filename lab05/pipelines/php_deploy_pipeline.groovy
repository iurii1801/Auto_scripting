pipeline {
    agent { label 'ansible-agent' }

    environment {
        REPO_URL       = 'https://github.com/iurii1801/Auto_scripting.git'
        REPO_BRANCH    = 'lab05'
        ANSIBLE_DIR    = 'lab05/ansible'
        INVENTORY_FILE = 'hosts.ini'
        PLAYBOOK_FILE  = 'deploy_recipe_book.yml'
        ANSIBLE_HOST_KEY_CHECKING = 'False'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {

        stage('Checkout repo with PHP project') {
            steps {
                echo "Cloning repository with PHP project (branch: ${env.REPO_BRANCH})..."
                git branch: "${env.REPO_BRANCH}", url: "${env.REPO_URL}"
            }
        }

        stage('Deploy PHP project to test server') {
            steps {
                echo "Running Ansible deploy playbook ${env.PLAYBOOK_FILE}..."
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
            echo "PHP project has been successfully deployed to the test server."
        }
        failure {
            echo "Deployment failed. Check console output and Ansible logs."
        }
    }
}
