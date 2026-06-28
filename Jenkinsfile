pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        APP_IMAGE = "ghcr.io/farah-ben-harb/devsecops-incident-platform-api"
        BUILD_IMAGE_TAG = "build-${BUILD_NUMBER}"
        VENV_DIR = ".venv"
        REPORTS_DIR = "reports"
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
                    trivy --version
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    set -eu
                    mkdir -p "${REPORTS_DIR}"
                    python3 -m venv "${VENV_DIR}"
                    . "${VENV_DIR}/bin/activate"
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pip-audit
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

        stage('Gitleaks Scan') {
            steps {
                sh '''
                    set -eu
                    mkdir -p "${REPORTS_DIR}"
                    docker run --rm \
                      -v "$PWD:/workspace" \
                      zricethezav/gitleaks:latest \
                      detect \
                      --source /workspace \
                      --redact \
                      --exit-code 1 \
                      --report-format sarif \
                      --report-path /workspace/${REPORTS_DIR}/gitleaks.sarif
                '''
            }
        }

        stage('Dependency Vulnerability Scan') {
            steps {
                sh '''
                    set -eu
                    . "${VENV_DIR}/bin/activate"
                    pip-audit \
                      -r requirements.txt \
                      --format json \
                      --output "${REPORTS_DIR}/pip-audit.json"
                '''
            }
        }

        stage('Prepare Image Tags') {
            steps {
                script {
                    env.GIT_SHA_SHORT = sh(script: 'git rev-parse --short=7 HEAD', returnStdout: true).trim()
                    env.SHA_IMAGE_TAG = "sha-${env.GIT_SHA_SHORT}"
                    env.LATEST_IMAGE_TAG = "latest"
                }
                echo "Image tags prepared: ${BUILD_IMAGE_TAG}, ${SHA_IMAGE_TAG}, ${LATEST_IMAGE_TAG}"
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -eu
                    docker build \
                      -t "${APP_IMAGE}:${BUILD_IMAGE_TAG}" \
                      -t "${APP_IMAGE}:${SHA_IMAGE_TAG}" \
                      -t "${APP_IMAGE}:${LATEST_IMAGE_TAG}" \
                      .
                '''
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    set -eu
                    trivy image \
                      --severity HIGH,CRITICAL \
                      --ignore-unfixed \
                      --exit-code 1 \
                      --format json \
                      --output "${REPORTS_DIR}/trivy-image.json" \
                      "${APP_IMAGE}:${BUILD_IMAGE_TAG}"
                '''
            }
        }

        stage('Push Image To GHCR') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'ghcr-creds',
                        usernameVariable: 'GHCR_USERNAME',
                        passwordVariable: 'GHCR_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        printf '%s' "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
                        docker push "${APP_IMAGE}:${BUILD_IMAGE_TAG}"
                        docker push "${APP_IMAGE}:${SHA_IMAGE_TAG}"
                        docker push "${APP_IMAGE}:${LATEST_IMAGE_TAG}"
                        docker logout ghcr.io
                    '''
                }
            }
        }

        stage('Verify Public Registry Access') {
            steps {
                sh '''
                    set -eu
                    docker logout ghcr.io || true
                    docker manifest inspect "${APP_IMAGE}:${BUILD_IMAGE_TAG}" > /dev/null
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: false, testResults: 'reports/pytest.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/*'
        }
        success {
            echo "Build completed with CI, security scans, and GHCR push."
            echo "Published tags: ${APP_IMAGE}:${BUILD_IMAGE_TAG}, ${APP_IMAGE}:${SHA_IMAGE_TAG}, ${APP_IMAGE}:${LATEST_IMAGE_TAG}"
        }
    }
}
