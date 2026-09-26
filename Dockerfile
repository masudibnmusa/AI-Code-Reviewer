# ============================================================
# Dockerfile — Container configuration
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# System deps needed for some static analysis tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Node.js for ESLint (JS/TS linting)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g eslint

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/review_history data/config_rules

EXPOSE 8000

CMD ["python", "-m", "app.main"]