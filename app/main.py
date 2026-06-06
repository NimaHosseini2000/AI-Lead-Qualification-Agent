from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from app.database import Base, engine
from app.models import lead as _lead_models  # noqa: F401 — registers models with Base
from app.routes import leads, webhook

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Lead Qualification Agent",
    description="Automatically qualifies inbound leads using OpenAI and routes them to the right sales team.",
    version="1.0.0",
)

app.include_router(webhook.router)
app.include_router(leads.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
