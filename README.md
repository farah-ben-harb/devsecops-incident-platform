# DevSecOps Incident Platform

Production-style incident tracking API built with `FastAPI` and `PostgreSQL`, designed as the application repository of a broader DevSecOps and GitOps portfolio platform.

This repository focuses on the application layer:

- REST API for incident management
- PostgreSQL-backed persistence
- health, readiness, and Prometheus metrics endpoints
- automated tests
- container packaging
- Jenkins-driven CI and image publishing

The deployment layer lives in the companion repository:

- `gitops-delivery-platform`

## Architecture Summary

The end-to-end workflow for the full platform is:

1. Developers push changes to this repository
2. Jenkins runs CI checks including tests, secret scanning, dependency scanning, filesystem scanning, and optional SonarQube analysis
3. Jenkins builds the Docker image and scans it
4. Jenkins pushes the image to GitHub Container Registry
5. Jenkins updates the GitOps repository with the immutable image tag
6. Argo CD detects the GitOps change and deploys to Kubernetes
7. Prometheus scrapes application metrics and Grafana visualizes them

## Core Capabilities

- FastAPI REST API with OpenAPI documentation
- CRUD operations for incidents
- PostgreSQL integration using SQLAlchemy
- `/health` endpoint for liveness checks
- `/ready` endpoint for readiness and database reachability checks
- `/metrics` endpoint for Prometheus scraping
- request validation with Pydantic
- unit tests with `pytest`
- containerized local workflow with Docker Compose
- Jenkins pipeline with CI, security scanning, GHCR publishing, and GitOps update automation

## Technology Stack

- `FastAPI`
- `PostgreSQL`
- `SQLAlchemy`
- `Pydantic`
- `pytest`
- `Docker`
- `Jenkins`
- `Gitleaks`
- `OWASP Dependency-Check`
- `SonarQube` (optional stage)
- `Trivy`
- `GitHub Container Registry (GHCR)`

## API Endpoints

Base URL:

- `http://localhost:8000`

Available endpoints:

- `GET /health`
- `GET /ready`
- `GET /metrics`
- `GET /api/incidents`
- `POST /api/incidents`
- `GET /api/incidents/{incident_id}`
- `PUT /api/incidents/{incident_id}`
- `DELETE /api/incidents/{incident_id}`

Swagger UI:

- `http://localhost:8000/docs`

## Incident Data Model

Each incident includes:

- `title`
- `description`
- `severity`
- `status`
- `service_name`
- `created_at`
- `updated_at`

## Repository Structure

```text
app/
  api/
    routes/
  core/
  db/
  models/
  schemas/
  services/
  telemetry/
tests/
  unit/
Dockerfile
docker-compose.yml
Jenkinsfile
requirements.txt
```

## Local Development

### 1. Configure environment variables

Copy the example file and adjust values if needed:

```bash
cp .env.example .env
```

Key variables:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DATABASE_URL`

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run PostgreSQL locally

You can either use your own PostgreSQL instance or start the local container stack:

```bash
docker compose up -d postgres
```

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

## Local Docker Workflow

Run the full application stack with Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

Services:

- API on `8000`
- PostgreSQL on `5432`

## Validation Commands

Once the app is running:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/metrics
```

Example incident creation:

```bash
curl -X POST http://localhost:8000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{"title":"Database latency spike","description":"PostgreSQL response time increased","severity":"high","status":"open","service_name":"postgresql"}'
```

## Test Suite

Run unit tests:

```bash
pytest
```

## Observability

The application exposes Prometheus metrics at:

- `GET /metrics`

Key metrics include:

- `http_requests_total`
- `http_request_duration_seconds`
- `api_error_total`
- `incident_created_total`
- `app_uptime_seconds`

## Jenkins Pipeline

This repository includes a Jenkins pipeline intended for a remote Ubuntu Jenkins VM.

Pipeline stages:

- `Checkout`
- `Verify Toolchain`
- `Install Dependencies`
- `CI`
- `CD`

Inside `CI`, the pipeline runs:

- `Run Tests`
- `Gitleaks Scan`
- `OWASP Dependency-Check`
- `Trivy Filesystem Scan`
- `SonarQube Analysis` (optional)
- `Prepare Image Tags`
- `Build Docker Image`
- `Trivy Image Scan`

Inside `CD`, the pipeline runs:

- `Push Image To GHCR`
- `Update GitOps Repo`

## Security Gates

The CI pipeline includes:

- `Gitleaks` for secret scanning
- `OWASP Dependency-Check` for software composition and dependency vulnerability scanning
- `Trivy fs` for repository filesystem scanning
- `Trivy` for container image vulnerability scanning
- optional `SonarQube` analysis for code quality, maintainability, and coverage reporting
- immutable image tagging for traceability and rollback safety

Reports are archived by Jenkins under:

- `reports/`

Dependency-Check is executed through the official Docker image and scans the Python project using the tool's pip analyzer. Because the pip analyzer is marked experimental by OWASP, the pipeline enables experimental analyzers explicitly.

For stable NVD updates, the Jenkins pipeline expects:

- a Jenkins `Secret text` credential with ID `nvd-api-key`

The stage also persists Dependency-Check data in the Jenkins workspace so subsequent builds do not need to rebuild the vulnerability database from scratch every time.

## Container Image Publishing

The application image is published to:

- `ghcr.io/farah-ben-harb/devsecops-incident-platform-api`

Each successful pipeline publishes:

- `build-<jenkins-build-number>`
- `sha-<short-git-sha>`
- `latest`

Example:

- `ghcr.io/farah-ben-harb/devsecops-incident-platform-api:build-12`
- `ghcr.io/farah-ben-harb/devsecops-incident-platform-api:sha-a1b2c3d`
- `ghcr.io/farah-ben-harb/devsecops-incident-platform-api:latest`

The GitOps workflow uses the immutable `sha-<short-git-sha>` tag.

## Jenkins Credentials

### GHCR push credential

Create a Jenkins credential:

- Kind: `Username with password`
- ID: `ghcr-creds`
- Username: `farah-ben-harb`
- Password: GitHub Personal Access Token with package write access

Recommended scopes:

- `write:packages`
- `read:packages`

### GitOps repository push credential

Create a second Jenkins credential:

- Kind: `Username with password`
- ID: `gitops-repo-creds`
- Username: `farah-ben-harb`
- Password: GitHub Personal Access Token with repository write access

Recommended scope:

- `repo`

### SonarQube token credential

If you want to enable the SonarQube stage, create an additional Jenkins credential:

- Kind: `Secret text`
- ID: `sonar-token`
- Value: SonarQube user token

Also define the Jenkins environment variable:

- `SONAR_HOST_URL`

Then set the pipeline parameter:

- `ENABLE_SONARQUBE=true`

The repository already includes:

- `sonar-project.properties`

so the scanner can pick up sources, tests, coverage, and JUnit reports automatically.

### NVD API key credential for OWASP Dependency-Check

Create an additional Jenkins credential:

- Kind: `Secret text`
- ID: `nvd-api-key`
- Value: NVD API key

You can request an official NVD API key here:

- `https://nvd.nist.gov/developers/request-an-api-key`

### Optional email notifications

The pipeline supports optional email notifications through the `NOTIFY_EMAIL` parameter.

If Jenkins Mailer is configured, the pipeline sends a completion summary containing:

- build result
- build URL
- commit reference
- CI/CD summary

## Jenkins VM Requirements

Required tools on the Jenkins VM:

- Java 17
- Jenkins
- Docker
- Git
- Python 3
- `kubectl`
- `sonar-scanner` is not required locally because the pipeline uses the official scanner container image
- `trivy`

Python tooling install example:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip
```

Allow the Jenkins user to access Docker:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

## Related Repository

The GitOps and Kubernetes deployment manifests for this application live in:

- `gitops-delivery-platform`

That repository contains:

- Kubernetes manifests
- Kustomize overlay for `kind`
- Argo CD application definition
- Prometheus `ServiceMonitor`
- Grafana dashboard provisioning
