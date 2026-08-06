# Ledgerline — AI-Powered Credit Risk Analyzer & Loan Decision System

A clean monolithic application: one FastAPI backend, one React + TypeScript
frontend, one PostgreSQL database. See `/docs` in the project conversation
for the full architecture plan.

**Module 1 (this delivery):** project foundation — backend + frontend
scaffolding, database connection, Alembic migrations, and full JWT
authentication (register, login, `/me`, role-based access) with a working
UI (login, register, protected dashboard).

## Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or use the provided `docker-compose.yml`)

## 1. Start PostgreSQL

```bash
docker compose up -d
```

This starts a single Postgres 16 container on port 5432 with the credentials
already wired into `backend/.env.example`. If you'd rather use a local
Postgres install, just point `DATABASE_URL` at it instead.

## 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # adjust values if needed
alembic upgrade head            # creates the users table
uvicorn app.main:app --reload   # http://localhost:8000
```

API docs (Swagger UI) are available at `http://localhost:8000/docs` once
the server is running.

Run the backend test suite:

```bash
pytest -v
```

## 3. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env            # adjust VITE_API_URL if needed
npm run dev                     # http://localhost:5173
```

## 4. Try it

1. Open `http://localhost:5173`
2. Register an account (choose "Applicant" or "Bank staff")
3. You're redirected straight to the dashboard, already logged in
4. Refresh the page — the session persists (JWT is validated against `/auth/me`)
5. Log out, then log back in with the same credentials

## Project structure

See the folder tree in the project conversation for the complete Module 1
layout, or run `find backend/app frontend/src -type f` from the project root.

## What's deliberately not here yet

This is Module 1 of a staged build. Loan applications, ML scoring, SHAP
explainability, the Groq-powered explanation service, and the staff review
queue are built in later modules, on top of this foundation.
