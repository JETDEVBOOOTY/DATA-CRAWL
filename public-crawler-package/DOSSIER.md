# The Law of Data Drainage — Dossier

## Executive Summary
In nature, water follows a law of drainage: many sources converge into structured rivers and lakes. Data on the public web behaves similarly — dispersed, noisy, and often overwhelming. The **Law of Data Drainage** is a metaphor and a product: a secure, ethical system that collects public information, filters noise, structures content, and visualizes insights in an intuitive interface.

## Key Features
- Ethical crawling: whitelist required, robots.txt respected, rate limiting and domain politeness.
- Scalable asynchronous crawler based on aiohttp.
- SQLite storage (optionally swap for PostgreSQL for production).
- FastAPI backend exposing secure endpoints to control crawl and retrieve results.
- React frontend explorer with filters, grouping, TTS, CSV export, and JSONL import.
- Production-ready deployment assets: nginx reverse proxy, Let's Encrypt certbot hooks, docker-compose prod file.

## Architecture (high level)
- Crawler (async) → parses HTML → extracts title, text, links → stores item in DB.
- Backend exposes REST API for control and retrieval, and runs the crawler in background tasks.
- Frontend interacts with API (or local JSONL) to present interactive dashboards and search.

## Security & Compliance
- API key protection for sensitive endpoints (start/stop crawl).
- TLS termination via nginx + Let's Encrypt.
- Rate limiting (nginx + app-level), CORS restricted, input validation, and logs auditing.
- Guidance for GDPR: data retention policy, deletion endpoint, consent & legal assessment recommended.

## Deployment Overview
- Recommended: Ubuntu 22.04 server, Docker & Docker Compose v2, domain name.
- Use `docker-compose.prod.yml`, configure `backend/.env`, generate certs with certbot, use `deploy.sh` for automations.
- For scaling: replace SQLite with PostgreSQL, or run backend as multiple replicas behind load balancer, use object storage for backups.

## Use Cases
- OSINT and public research (ethically and legally authorized).
- Competitive monitoring, brand monitoring, public opinion analysis.
- Aggregating public open-data and presenting consolidated insights visually.

## Next Steps & Roadmap
- Add authentication & role-based access to UI (2FA for admin).
- Replace SQLite with PostgreSQL + full-text search (PGroonga or Elasticsearch).
- Add semantic search (embeddings) and named-entity extraction pipeline.
- Add scheduled crawling with job queue (Redis + RQ/Celery) and quota management.

