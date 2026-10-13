# The public demo's image (docs/demo.md): the UI built
# with tsc, then the Python server with the demo seed. Never app/data/
# (.dockerignore). Demo settings and secrets come from fly.toml and
# `fly secrets`, not from this file.

# 1. UI: TypeScript -> ui/dist/
FROM node:22-slim AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/tsconfig.json ./
COPY ui/src ./src
RUN npx tsc

# 2. Server
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py ./
COPY backend ./backend
COPY demo_seed ./demo_seed
COPY ui/index.html ui/login.html ./ui/
COPY ui/css ./ui/css
COPY ui/settings ./ui/settings
COPY --from=ui /ui/dist ./ui/dist

# The server only reads /app; sandboxes are written under /tmp.
RUN useradd --create-home demo
USER demo

EXPOSE 8080
CMD ["python", "-m", "server"]
