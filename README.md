# DevSecOps Incident Platform

`DevSecOps Incident Platform` is a production-style FastAPI service for managing operational incidents. It is the application repository in a larger portfolio project that will later add Jenkins CI, security scanning, GHCR publishing, Kubernetes manifests, Argo CD GitOps delivery, and Prometheus/Grafana monitoring.

## Phase 1 Scope

- FastAPI REST API with OpenAPI docs
- PostgreSQL-backed incident CRUD
- `/health`, `/ready`, and `/metrics`
- Request validation with Pydantic
- Unit tests with `pytest`
- Dockerfile and local `docker-compose` workflow

## API Overview

Base URL: `http://localhost:8000`

- `GET /health`
- `GET /ready`
- `GET /metrics`
- `GET /api/incidents`
- `POST /api/incidents`
- `GET /api/incidents/{incident_id}`
- `PUT /api/incidents/{incident_id}`
- `DELETE /api/incidents/{incident_id}`

Swagger UI is available at `http://localhost:8000/docs`.

## Incident Model

Each incident includes:

- `title`
- `description`
- `severity`
- `status`
- `service_name`
- `created_at`
- `updated_at`

## Local Development

1. Copy `.env.example` to `.env`.
2. Update the PostgreSQL password if needed.
3. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Run the API:

```bash
uvicorn app.main:app --reload
```

## Local Docker Workflow

```bash
cp .env.example .env
docker compose up --build
```

The API will be available on port `8000`, and PostgreSQL will be exposed on `5432`.

## Running Tests

```bash
pytest
```

## Jenkins Pipeline v3

The repository now includes a Jenkins pipeline for the remote Ubuntu Jenkins VM with CI, DevSecOps security gates, and GHCR publishing.

Current pipeline stages:

- `Checkout`
- `Verify Toolchain`
- `Install Dependencies`
- `Run Tests`
- `Gitleaks Scan`
- `Dependency Vulnerability Scan`
- `Prepare Image Tags`
- `Build Docker Image`
- `Trivy Image Scan`
- `Push Image To GHCR`
- `Set GHCR Package Public`

The current pipeline now publishes container images after all quality and security checks pass. Later phases will add:

- GitOps repository update

### Scan Tools Used

- `Gitleaks` scans the repository for hardcoded secrets.
- `pip-audit` scans Python dependencies for known vulnerabilities.
- `Trivy` scans the built container image for high and critical vulnerabilities.
- Docker pushes the image to `ghcr.io` using Jenkins-managed credentials.

The pipeline archives the generated reports in the Jenkins build artifacts under `reports/`.

After the push, Jenkins also calls the GitHub Packages API to set the newly published container package visibility to `public`, so anonymous pulls from `ghcr.io` work without needing a login.

### Image Tags Produced

Each successful pipeline run publishes:

- `build-<jenkins-build-number>`
- `sha-<short-git-sha>`
- `latest`

Example:

- `ghcr.io/farah-ben-harb/devsecops-incident-platform-api:build-12`
- `ghcr.io/farah-ben-harb/devsecops-incident-platform-api:sha-a1b2c3d`
- `ghcr.io/farah-ben-harb/devsecops-incident-platform-api:latest`

## GHCR Package Note

The image is intentionally published under a dedicated package namespace:

- `ghcr.io/farah-ben-harb/devsecops-incident-platform-api`

This avoids issues with older private package state from early test pushes and ensures the package is created with repository metadata labels from the beginning.

## Jenkins Credential For GHCR

Create a Jenkins credential with:

- Kind: `Username with password`
- ID: `ghcr-creds`
- Username: your GitHub username, `farah-ben-harb`
- Password: a GitHub Personal Access Token with package write access

The pipeline uses that credential to run `docker login ghcr.io` and push the image tags.

## Jenkins VM Prerequisites

Before running the pipeline on the Ubuntu VM, make sure these are installed in addition to Jenkins and Docker:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip
```

The Jenkins service user must also be able to access Docker:

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

## Repository Structure

```text
app/
  api/
  core/
  db/
  models/
  schemas/
  services/
  telemetry/
tests/
Dockerfile
docker-compose.yml
requirements.txt
```

## Upcoming Phases

- Jenkins pipeline with tests and Docker build
- Gitleaks, dependency, and Trivy scans
- GHCR image publishing
- GitOps manifest updates in a separate repo
- Argo CD deployment to `kind`
- Prometheus and Grafana dashboards
