# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-builder
WORKDIR /frontend
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY index.html vite.config.ts tsconfig.json ./
COPY src ./src
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY main.py README.md railway.toml .env.example ./
COPY --from=frontend-builder /frontend/dist ./web_dist

EXPOSE 3000

CMD ["python", "main.py"]
