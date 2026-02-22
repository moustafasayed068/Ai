from fastapi import FastAPI
from App.db.session import engine, supabase_engine
from App.db.base import Base
from App.core.config import settings
from App.api.v1.routers import llm, users, items, admin, img
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


@app.on_event("startup")
def create_tables():
   
    if settings.DB_MODE in ["local", "both"]:
        
        Base.metadata.create_all(bind=engine)

    
    if settings.DB_MODE in ["supabase", "both"] and supabase_engine:
        
        Base.metadata.create_all(bind=supabase_engine)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    
app.include_router(llm.router, prefix="/llm", tags=["Chat"])  
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(items.router, prefix="/items", tags=["Items"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(img.router, prefix="/img-analysis", tags=["IMG"])

