"""
FastAPI application entrypoint.

Single monolithic backend: one app, one process, one database. Routers for
future modules (loans, scoring, admin) will be included here the same way
`auth` is, as they're built.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import applicants, auth, documents, loans

app = FastAPI(
    title="Credit Risk Analyzer API",
    description="Backend for the AI-powered credit risk analyzer & loan decision system.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(applicants.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "credit-risk-analyzer-api"}