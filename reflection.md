# Reflect & Post-Analysis

A review of failures, constraints, and decisions made during this deployment.

---

## What Worked

- Dockerised FastAPI application ran consistently across reboots
- Nginx successfully rerouted traffic from port 80 → 8000
- Port forwarding enabled external access from the host machine
- All monitoring endpoints (`/health`, `/ready`, `/metrics`) functioned correctly

---

## What Failed

| Issue | Root Cause |
|-------|------------|
| Nginx config syntax errors | Unfamiliarity with Nginx config requirements |
| Port forwarding misconfigured | Virtualisation adds a network layer that must be mapped manually |
| Container not persisting after reboot | `--restart unless-stopped` flag omitted initially |

---

## Performance

| Environment         | Latency|
|---------------------|--------|
| Local (bare Python) | ~100ms |
| VM (Docker + Nginx) | ~780ms |

The ~680ms overhead is expected given the path a request travels:
```
WSL → Windows → VirtualBox → VM → Nginx → Docker → FastAPI
```

Each boundary (hypervisor, reverse proxy, container runtime) adds latency. This is a local dev environment concern, not a production architecture concern.

---

## Key Lessons

- **Deployment is layered** — running code is the easy part; networking, persistence, and routing each need deliberate configuration
- **Reverse proxies decouple concerns** — Nginx handling public access means the application doesn't need to care about ports or SSL
- **Persistence must be explicit** — containers are ephemeral by default; reliability requires a restart policy

---

## What I'd Do Differently

- Set `--restart unless-stopped` from the start
- Run `nginx -t` to validate config *before* restarting the service
- Plan port mapping and forwarding *before* deployment, **not during**
- Test each layer independently and in sequence rather than all at once

---

## Next Steps

- [ ] Add TLS (HTTPS) via Nginx + Certbot
- [ ] Deploy to a real cloud VM (e.g. AWS EC2, DigitalOcean)
- [ ] Integrate a CI/CD pipeline to automate build and deployment
- [ ] Improve observability — structured logging and alerting