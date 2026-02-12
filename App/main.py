from fastapi import FastAPI
from App.db.session import engine, get_db, get_supabase_db
from App.db.base import Base
from App.api.v1.routers import users, items, admin
from .core.config import settings
import logging
from .api.v1.routers import users, items, admin  # add admin


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Dual Database App",
    description=f"Current DB Mode: {settings.DB_MODE}"
)

app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(items.router, prefix="/items", tags=["items"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Starting with DB_MODE: {settings.DB_MODE}")
    if settings.DB_MODE == "local":
        logger.info("💾 Using LOCAL database only")
    elif settings.DB_MODE == "supabase":
        logger.info("☁️  Using SUPABASE database only")
    elif settings.DB_MODE == "both":
        logger.info("🔄 Using BOTH databases (sync mode)")