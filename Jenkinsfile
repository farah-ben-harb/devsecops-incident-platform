pipeline {
    agent any

    options {
        timestamps()
    }

    parameters {
        booleanParam(
            name: 'RUN_CD',
            defaultValue: true,
            description: 'Push the container image to GHCR and update the GitOps repository after CI succeeds.'
        )
        booleanParam(
            name: 'ENABLE_SONARQUBE',
            defaultValue: false,
            description: 'Run SonarQube analysis when SONAR_HOST_URL and sonar-token are configured.'
        )
        string(
            name: 'NOTIFY_EMAIL',
            defaultValue: '',
            trim: true,
            description: 'Optional email address to notify after the pipeline completes.'
        )
    }

    environment {
        APP_IMAGE = "ghcr.io/farah-ben-harb/devsecops-incident-platform-api"
        BUILD_IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITOPS_REPO_URL = "https://github.com/farah-ben-harb/gitops-delivery-platform.git"
        GITOPS_REPO_BRANCH = "main"
        GITOPS_REPO_DIR = "gitops-repo"
        REPORTS_DIR = "reports"
        ODC_IMAGE = "owasp/dependency-check:12.2.2"
        SONAR_SCANNER_IMAGE = "sonarsource/sonar-scanner-cli:11"
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
                    pip install pytest-cov
                '''
            }
        }

        stage('CI') {
            stages {
                stage('Run Tests') {
                    steps {
                        sh '''
                            set -eu
                            mkdir -p "${REPORTS_DIR}"
                            . "${VENV_DIR}/bin/activate"
                            pytest \
                              --cov=app \
                              --cov-report=xml:${REPORTS_DIR}/coverage.xml \
                              --junitxml=${REPORTS_DIR}/pytest.xml
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

                stage('OWASP Dependency-Check') {
                    steps {
                        withCredentials([
                            string(credentialsId: 'nvd-api-key', variable: 'NVD_API_KEY')
                        ]) {
                            sh '''
                                set -eu
                                mkdir -p "${REPORTS_DIR}" .dependency-check-data
                                docker run --rm \
                                  -v "$PWD:/src" \
                                  -v "$PWD/${REPORTS_DIR}:/report" \
                                  -v "$PWD/.dependency-check-data:/odc-data" \
                                  "${ODC_IMAGE}" \
                                  --scan /src \
                                  --project "devsecops-incident-platform" \
                                  --out /report \
                                  --data /odc-data \
                                  --format JSON \
                                  --format HTML \
                                  --failOnCVSS 7 \
                                  --enableExperimental \
                                  --nvdApiKey "${NVD_API_KEY}"
                            '''
                        }
                    }
                }

                stage('Trivy Filesystem Scan') {
                    steps {
                        sh '''
                            set -eu
                            trivy fs \
                              --severity HIGH,CRITICAL \
                              --ignore-unfixed \
                              --exit-code 1 \
                              --format json \
                              --output "${REPORTS_DIR}/trivy-fs.json" \
                              .
                        '''
                    }
                }

                stage('SonarQube Analysis') {
                    when {
                        expression {
                            return params.ENABLE_SONARQUBE && env.SONAR_HOST_URL?.trim()
                        }
                    }
                    steps {
                        withCredentials([
                            string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')
                        ]) {
                            sh '''
                                set -eu
                                docker run --rm \
                                  -e SONAR_HOST_URL="${SONAR_HOST_URL}" \
                                  -e SONAR_TOKEN="${SONAR_TOKEN}" \
                                  -v "$PWD:/usr/src" \
                                  -w /usr/src \
                                  "${SONAR_SCANNER_IMAGE}"
                            '''
                        }
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
            }
        }

        stage('CD') {
            when {
                expression {
                    return params.RUN_CD
                }
            }
            stages {
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
                                docker manifest inspect "${APP_IMAGE}:${BUILD_IMAGE_TAG}" > /dev/null
                                docker manifest inspect "${APP_IMAGE}:${SHA_IMAGE_TAG}" > /dev/null
                                docker manifest inspect "${APP_IMAGE}:${LATEST_IMAGE_TAG}" > /dev/null
                                docker logout ghcr.io
                            '''
                        }
                    }
                }

                stage('Update GitOps Repo') {
                    steps {
                        withCredentials([
                            usernamePassword(
                                credentialsId: 'gitops-repo-creds',
                                usernameVariable: 'GITOPS_USERNAME',
                                passwordVariable: 'GITOPS_TOKEN'
                            )
                        ]) {
                            sh '''
                                set -eu
                                rm -rf "${GITOPS_REPO_DIR}"
                                git clone --branch "${GITOPS_REPO_BRANCH}" "${GITOPS_REPO_URL}" "${GITOPS_REPO_DIR}"
                                cd "${GITOPS_REPO_DIR}"
                                export TARGET_TAG="${SHA_IMAGE_TAG}"
                                python3 - <<'PY'
from pathlib import Path
import os

path = Path("overlays/local-kind/kustomization.yaml")
lines = path.read_text(encoding="utf-8").splitlines()
target_tag = os.environ["TARGET_TAG"]

for index, line in enumerate(lines):
    if line.strip().startswith("newTag:"):
        previous = line.split(":", 1)[1].strip()
        lines[index] = f"    newTag: {target_tag}"
        path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
        print(f"Updated GitOps image tag from {previous} to {target_tag}")
        break
else:
    raise SystemExit("newTag field not found in overlays/local-kind/kustomization.yaml")
PY
                                git config user.name "Jenkins"
                                git config user.email "jenkins@local"
                                git add overlays/local-kind/kustomization.yaml
                                if git diff --cached --quiet; then
                                  echo "No GitOps changes detected."
                                  exit 0
                                fi
                                git commit -m "chore: deploy ${SHA_IMAGE_TAG}"
                                git remote set-url origin "https://${GITOPS_USERNAME}:${GITOPS_TOKEN}@github.com/farah-ben-harb/gitops-delivery-platform.git"
                                git push origin "${GITOPS_REPO_BRANCH}"
                            '''
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/pytest.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/*'
            script {
                if (params.NOTIFY_EMAIL?.trim()) {
                    def result = currentBuild.currentResult ?: 'UNKNOWN'
                    def subject = "[Jenkins] ${env.JOB_NAME} #${env.BUILD_NUMBER} - ${result}"
                    def body = """\
Job: ${env.JOB_NAME}
Build: #${env.BUILD_NUMBER}
Result: ${result}
Build URL: ${env.BUILD_URL}
Git commit: ${env.GIT_COMMIT ?: 'n/a'}

Pipeline summary:
- CI: tests, Gitleaks, OWASP Dependency-Check, Trivy filesystem scan, SonarQube (optional), Docker build, Trivy image scan
- CD: GHCR push and GitOps repository update (when RUN_CD=true)
""".stripIndent()

                    try {
                        mail to: params.NOTIFY_EMAIL, subject: subject, body: body
                    } catch (err) {
                        echo "Email notification skipped or failed: ${err.message}"
                    }
                }
            }
        }
        success {
            echo "Build completed with CI, security scans, optional SonarQube analysis, GHCR push, and GitOps repo update."
            echo "Published tags: ${APP_IMAGE}:${BUILD_IMAGE_TAG}, ${APP_IMAGE}:${SHA_IMAGE_TAG}, ${APP_IMAGE}:${LATEST_IMAGE_TAG}"
        }
    }
}
