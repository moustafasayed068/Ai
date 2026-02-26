from contextlib import asynccontextmanager
from fastapi import FastAPI
from App.db.session import engine, supabase_engine
from App.db.base import Base
from App.core.config import settings
from App.api.v1.routers import llm, users, items, admin, img, embeddings, video, cv
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    if settings.DB_MODE in ["local", "both"]:
        Base.metadata.create_all(bind=engine)

    if settings.DB_MODE in ["supabase", "both"] and supabase_engine:
        Base.metadata.create_all(bind=supabase_engine)

    yield
    # Shutdown (nothing needed)


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv.router)
app.include_router(video.router, prefix="/video", tags=["vid"])
app.include_router(embeddings.router, prefix="/embedding", tags=["Embedding"])
app.include_router(llm.router, prefix="/llm", tags=["Chat"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(items.router, prefix="/items", tags=["Items"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(img.router, prefix="/img-analysis", tags=["IMG"])