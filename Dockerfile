FROM python:3.12-slim

LABEL org.opencontainers.image.title="devsecops-incident-platform" \
      org.opencontainers.image.description="FastAPI incident tracker showcasing DevSecOps CI, security scanning, and GitOps delivery." \
      org.opencontainers.image.source="https://github.com/farah-ben-harb/devsecops-incident-platform" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
