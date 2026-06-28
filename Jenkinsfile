pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        APP_IMAGE = "ghcr.io/farah-ben-harb/devsecops-incident-platform"
        BUILD_IMAGE_TAG = "build-${BUILD_NUMBER}"
        VENV_DIR = ".venv"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Toolchain') {
            steps {
                sh '''
                    set -eu
                    python3 --version
                    pip3 --version
                    docker --version
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv "${VENV_DIR}"
                    . "${VENV_DIR}/bin/activate"
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    set -eu
                    mkdir -p reports
                    . "${VENV_DIR}/bin/activate"
                    pytest --junitxml=reports/pytest.xml
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -eu
                    docker build \
                      -t "${APP_IMAGE}:${BUILD_IMAGE_TAG}" \
                      .
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: false, testResults: 'reports/pytest.xml'
        }
        success {
            echo "Build completed. Docker image available as ${APP_IMAGE}:${BUILD_IMAGE_TAG}"
        }
    }
}

