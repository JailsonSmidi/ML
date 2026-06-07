from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import sessions, products, listings, analyses, batches, notifications

app = FastAPI(
    title="ML Market Research API",
    version="1.0.0",
    docs_url="/docs" if settings.app_env == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router,       prefix="/api/sessions",       tags=["sessions"])
app.include_router(products.router,       prefix="/api/products",       tags=["products"])
app.include_router(listings.router,       prefix="/api/listings",       tags=["listings"])
app.include_router(analyses.router,       prefix="/api/analyses",       tags=["analyses"])
app.include_router(batches.router,        prefix="/api/batches",        tags=["batches"])
app.include_router(notifications.router,  prefix="/api/notifications",  tags=["notifications"])


@app.get("/health")
async def health():
    return {"status": "ok"}
