# Public Crawler — The Law of Data Drainage

This repository contains a complete **production-ready** (developer-deliverable) package for a public-data crawler + explorer UI,
presented as **"The Law of Data Drainage"** — a system that collects, filters, structures and visualizes public web data.

**What you get in this package**:
- Backend (FastAPI) with an ethical crawler, SQLite storage, API endpoints, and Dockerfile.
- Frontend (React) — explorer UI component to load/export and interact with crawled data.
- Production docker-compose (nginx + backend + certbot hooks) and nginx configuration.
- Deployment helper script `deploy.sh` and security guidelines.
- `DOSSIER.md` — presentation, architecture, features, security, and deployment guide (human readable).
- `backend/.env.example` — template for secrets.
- LICENSE (MIT)

**Important legal & ethical notice:** Use this system only on domains you own or are authorized to crawl. Respect site Terms of Service, robots.txt, and privacy laws (GDPR, etc.).

---

## Quick start (local, developer)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (dev)
```bash
cd frontend
yarn install
yarn start
# open http://localhost:3000
```

For production, review `docker-compose.prod.yml`, `nginx/` and `deploy.sh` in the root of this package.

