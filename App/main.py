from fastapi import FastAPI
from App.db.session import engine
from App.db.base import Base
from App.api.v1.routers import users, items, admin
from .core.config import settings
import logging
from .api.v1.routers import users, items, admin,cohere  

from fastapi.middleware.cors import CORSMiddleware


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="FastAPI Dual Database App with AI",
    description=f"FastAPI application with flexible database configuration and Cohere AI. Current mode: {settings.DB_MODE}",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "FastAPI Dual Database Application with AI",
        "db_mode": settings.DB_MODE,
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "db_mode": settings.DB_MODE,
        "failure_strategy": settings.SUPABASE_FAILURE_STRATEGY
    }
    
app.include_router(cohere.router, prefix="/api/v1", tags=["AI"])  
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(items.router, prefix="/api/v1/items", tags=["Items"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Application starting with DB_MODE: {settings.DB_MODE}")
    logger.info(f"📊 Failure strategy: {settings.SUPABASE_FAILURE_STRATEGY}")
    logger.info(f"🤖 Cohere AI: Enabled")
    
    if settings.DB_MODE == "local":
        logger.info("💾 Using LOCAL database only")
    elif settings.DB_MODE == "supabase":
        logger.info("☁️  Using SUPABASE database only")
    elif settings.DB_MODE == "both":
        logger.info("🔄 Using BOTH databases (sync mode)")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")