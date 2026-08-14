from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend import env_loader  # Load .env first!
from .database import init_db, get_db
from .seed import seed_initial_data
from .routers import auth_router, documents, calculations, approvals, proofs, cost_types

app = FastAPI(
    title="SLA Recovery Audit System",
    description="Automated SLA recovery claim processing system",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(documents.router)
app.include_router(calculations.router)
app.include_router(approvals.router)
app.include_router(proofs.router)
app.include_router(cost_types.router)


@app.on_event("startup")
def startup_event():
    init_db()
    db = next(get_db())
    try:
        seed_initial_data(db)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"message": "SLA Recovery Audit System API"}
