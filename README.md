# Ledgerline — AI-Powered Credit Risk & Loan Decisioning Platform

A full-stack loan origination and credit-risk platform: applicants submit
loan applications and get an AI-generated, explainable risk assessment
immediately; staff review flagged applications, verify supporting
documents, and record auditable decisions; admins get portfolio-level
analytics. Built as a single, clean monolith — one FastAPI backend, one
React frontend, one PostgreSQL database — deliberately avoiding
microservices, message queues, or third-party infrastructure that a
project at this scale doesn't need.

## Problem being solved

Manual loan underwriting is slow and inconsistent, and pure black-box
ML scoring is a compliance risk — a rejected applicant is entitled to
know why. Ledgerline addresses both: a trained scikit-learn model
produces a risk score, but **SHAP explainability** surfaces the specific
factors behind every prediction, and a human reviewer always makes the
final call — the model recommends, it never decides.

## Key features

- **JWT authentication + role-based access control** — `applicant`,
  `staff`, `admin` roles enforced on every protected endpoint, not just
  hidden in the UI
- **Loan application management** — single-page submission form,
  applicant status tracking, full application history
- **AI credit-risk prediction** — a `GradientBoostingClassifier` trained
  on a documented synthetic dataset (`ml-training/train.py`), producing a
  0–100 risk score, LOW/MEDIUM/HIGH category, and an APPROVE/REVIEW/REJECT
  recommendation, computed synchronously on submission
- **Explainable AI** — SHAP `TreeExplainer` returns the top contributing
  factors (and direction) behind every individual prediction, shown to
  both the applicant and staff
- **Staff review & decision workflow** — a validated state machine
  (`scored → manual_review → approved/rejected`) with reviewer identity,
  timestamp, and notes recorded on every decision; double-approval and
  post-decision edits are blocked server-side (409, not silently allowed)
- **Document upload + OCR + verification** — applicants upload ID/income/
  bank-statement documents (JPEG/PNG/PDF); the backend sniffs real file
  content (not the client's declared MIME type) before accepting anything,
  runs OCR via Tesseract/pypdf synchronously, and staff verify or reject
  each document independently of the loan decision
- **Analytics dashboard** — staff/admin-only aggregate stats (status
  breakdown, approval rate, risk distribution, 30-day submission trend),
  computed with grouped SQL aggregates, not in-memory counting
- **Audit logging** — an append-only trail recording who did what, to
  which resource, and when, across loan submissions, decisions, and
  document actions; staff/admin-only, filterable by action/resource/actor

## Architecture overview
React + TS (Vite) ──HTTP/JWT──▶ FastAPI (single process)
│
┌──────────────┼──────────────────┐
▼ ▼ ▼
PostgreSQL Local file storage Offline ML pipeline
(SQLAlchemy (uploaded documents, (ml-training/train.py + Alembic) never DB-stored, → model.pkl, loaded
never statically once at startup)
served)

Every service module follows the same layering established from Module 3
onward: a thin router → a business-logic service (validates, orchestrates,
persists) → optionally a lower-level mechanics module (`ml_service.py`,
`ocr_service.py`, `file_storage.py`) that knows nothing about HTTP or the
database.

## Tech stack

**Backend:** FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, `python-jose`
(JWT), `passlib`/bcrypt, scikit-learn, SHAP, pytesseract, pypdf, Pillow,
pytest

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, recharts, axios,
react-router-dom, lucide-react

**Infra:** Docker Compose (PostgreSQL only — the backend and frontend run
directly, by design; see "Docker & PostgreSQL setup" below)

## Modules

| # | Module | Status |
|---|---|---|
| 1 | Project setup, JWT auth, PostgreSQL, Docker | Done |
| 2 | Applicant profiles + loan application CRUD | Done |
| 3 | AI credit-risk scoring engine + SHAP explainability | Done |
| 4 | Staff review / approval / rejection decision workflow | Done |
| 5 | Document upload + OCR + verification | Done |
| 6 | Admin/approval workflow | Covered by Module 4 — audited and confirmed no separate functionality was missing |
| 7 | Analytics dashboard | Done |
| 8 | Audit logging | Done |
| 9 | Final testing, deployment readiness, documentation | Done |

## Project structure
credit-risk-analyzer/
├── backend/
│ ├── app/
│ │ ├── core/ # security.py, file_storage.py — low-level, HTTP-agnostic utilities
│ │ ├── models/ # SQLAlchemy ORM models
│ │ ├── schemas/ # Pydantic request/response schemas
│ │ ├── routers/ # FastAPI route handlers (thin — delegate to services)
│ │ ├── services/ # business logic (auth, loans, scoring, review, documents, analytics, audit)
│ │ ├── ml/ # trained model.pkl + metadata (gitignored artifact, see below)
│ │ ├── config.py
│ │ ├── database.py
│ │ ├── dependencies.py
│ │ └── main.py
│ ├── alembic/versions/ # 0001 → 0006, linear migration chain
│ └── tests/ # 113 tests across 8 test files
├── frontend/
│ └── src/
│ ├── api/ # one file per backend resource
│ ├── components/ # ui/ (primitives), loans/, documents/ (feature components)
│ ├── pages/
│ └── types/
├── ml-training/ # offline: generates synthetic data, trains + exports the model
└── docker-compose.yml # PostgreSQL only

## Local setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or the provided `docker-compose.yml`)
- **Tesseract OCR** — a system binary, not a Python package (see below)

### 1. Database
```bash
docker compose up -d
```

### 2. Train the ML model (one-time)
```bash
cd ml-training
pip install -r requirements.txt
python train.py
# writes backend/app/ml/model.pkl + model_metadata.json
```

### 3. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # adjust values as needed
alembic upgrade head
uvicorn app.main:app --reload   # http://localhost:8000
```

### 4. Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev                     # http://localhost:5173
```

## Environment variables

**`backend/.env`**
| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | JWT signing secret — generate your own, never use the example value |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRE_MINUTES` | Access token lifetime |
| `FRONTEND_ORIGIN` | Allowed CORS origin (single origin, not wildcarded) |
| `GROQ_API_KEY` | Reserved for a future LLM explanation layer — not currently used by any code path |
| `DOCUMENT_STORAGE_DIR` | Local path for uploaded documents (default `storage/documents`) |
| `MAX_DOCUMENT_SIZE_BYTES` | Upload size limit (default 10 MB) |

**`frontend/.env`**
| Variable | Purpose |
|---|---|
| `VITE_API_URL` | Backend base URL, e.g. `http://localhost:8000/api/v1` |

## Tesseract OCR — required system dependency

Document OCR uses `pytesseract`, which is only a Python wrapper — the
actual OCR engine must be installed separately and be on your `PATH`.
**The Tesseract binary itself is never committed to this repository.**

- **Windows:** install via the [UB-Mannheim Tesseract build](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS:** `brew install tesseract`
- **Linux:** `apt install tesseract-ocr`

If Tesseract isn't installed, image uploads will fail OCR gracefully
(the document still uploads, marked `ocr_failed` — see Module 5's
verification flow) rather than crashing the request.

## Alembic migrations

```bash
alembic upgrade head                              # apply all migrations
alembic revision --autogenerate -m "description"  # new migration
alembic downgrade -1                               # rollback one step
alembic current                                    # show current revision
```

Current chain: `0001` → `0002` → `0003` → `0004` → `0005` → `0006` (linear,
single head — users → applicants/loans → risk fields → review workflow →
documents → audit logs).

## Running tests

```bash
cd backend
pytest -v
```

113 tests across authentication, applicants, loans, ML scoring, staff
review, documents, analytics, and audit logging. No frontend test runner
is configured — frontend correctness is verified via `tsc -b` and
`npm run build`, consistent with how this project has been verified at
every module.

## Building the frontend

```bash
cd frontend
npm run build
```

## Docker & PostgreSQL setup

`docker-compose.yml` runs **PostgreSQL only** — this is a deliberate
architectural choice, not an oversight: the backend and frontend are
simple enough to run directly (`uvicorn`, `npm run dev`), and adding
container orchestration for a two-process app would be complexity without
benefit. Swap in a different `DATABASE_URL` if you'd rather use a local
Postgres install.

## API documentation

Interactive Swagger UI is available at `http://localhost:8000/docs` once
the backend is running (FastAPI auto-generated, always in sync with the
actual route definitions).

## Security considerations

- Passwords hashed with bcrypt; JWTs signed with a configurable secret,
  60-minute expiry, no refresh-token rotation (documented, deliberate
  scope decision, not an oversight)
- Every resource-ownership check (loans, documents) is enforced
  **server-side** via a single reused `get_loan_application()` helper —
  not duplicated per-endpoint, not left to the frontend
- File uploads: server sniffs real file content via magic bytes rather
  than trusting the client's declared MIME type; uploaded files are
  stored under server-generated UUID filenames (never the client's
  filename), making path traversal structurally impossible rather than
  merely filtered
- Uploaded files are served only through an authenticated streaming
  endpoint — the storage directory is never mounted as a static file
  server
- Audit logs are append-only; no update/delete path exists for them
- **Known, disclosed gap:** staff review notes and reviewer identity are
  not currently masked from an applicant's own API response for their own
  loan application (the frontend UI never displays them to applicants,
  but the raw API payload isn't filtered server-side). Documented here
  rather than silently left unmentioned.

## Future improvements

- Wire up the already-installed Groq client for natural-language,
  SHAP-grounded explanation text (currently unused — see Environment
  Variables above)
- Server-side masking of internal review fields from applicant-facing
  responses (see Security Considerations)
- Move document storage to S3-compatible object storage for multi-instance
  deployment
- CI pipeline (GitHub Actions) running the backend test suite on push
