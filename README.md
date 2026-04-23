# FastAPI Deployment with Docker + Nginx

A production-ready FastAPI deployment template using Docker and Nginx as a reverse proxy, with Prometheus metrics and rate limiting included.

---

## Architecture

```
Client → Host :8080 → VM → Nginx :80 → Docker :8000 → FastAPI
```

---

## Prerequisites

- Python 3.11+
- Docker
- Nginx
- A Linux VM (e.g. VirtualBox) if testing host → guest access

---

## Endpoints

| Route      | Description               |
|------------|---------------------------|
| `/predict` | Run model inference       |
| `/health`  | Liveness check            |
| `/ready`   | Readiness check           |
| `/metrics` | Prometheus-format metrics |

---

## Features

- FastAPI application with `/predict`, `/health`, `/ready`, `/metrics`
- Dockerised service with auto-restart
- Nginx reverse proxy
- Rate limiting and logging
- Prometheus metrics

---

## Run Locally (Without Docker)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Test:**

```bash
curl http://localhost:8000/health
```

---

## Run with Docker

```bash
docker build -t my-api .

# --restart unless-stopped auto-restarts the container unless manually stopped
docker run -d --restart unless-stopped -p 8000:8000 my-api
```

**Test:**

```bash
curl http://localhost:8000/health
```

---

## Nginx Configuration

Edit your Nginx config:

```bash
sudo nano /etc/nginx/sites-available/default
```

Paste the following:

```nginx
server {
    listen 80;

    location / {
        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

Validate and apply:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**Test:**

```bash
curl http://localhost/health
```

---

## Access from Host Machine

In VirtualBox, configure port forwarding:

- **Host:** `8080` → **Guest:** `80`

**Test from your host machine:**

```bash
curl http://localhost:8080/health
```

---

## Monitoring

Exposes Prometheus-format metrics at `/metrics`:

```bash
curl http://localhost/metrics
```