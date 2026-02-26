from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from App.core.dependencies import get_db
from App.client.supabase import SupabaseStorage
from App.services.cv import cv_service
from App.repositories import cv as cv_repo
from App.services.llm import llm_service
from App.schemas.cv import CVUploadResponse, CVOut, MatchRequest, MatchedCV
from uuid import UUID
router = APIRouter(prefix="/cv", tags=["CV"])


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    user_id: UUID = Form(...),
    db: Session = Depends(get_db),
):
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()

    # 1. Upload raw PDF to Supabase
    storage = SupabaseStorage()
    file_url = storage.upload_cv(file_bytes, file.filename, user_id)

    # 2. Extract text from PDF
    full_text = cv_service.extract_text_from_pdf(file_bytes)
    if not full_text:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF.")

    # 3. LLM: extract structured info + generate summary (parallel-ish)
    analyzed, summary = await _analyze_and_summarize(full_text)

    # 4. Build skill rows with embeddings
    skill_rows = await cv_service.build_skill_rows(analyzed)

    # 5. Save CV to DB
    cv = await cv_repo.create_cv(
        db,
        owner_id=user_id,
        file_url=file_url,
        full_text=full_text,
        name=analyzed.get("name"),
        education=analyzed.get("education"),
        experience_years=analyzed.get("experience_years", 0.0),
        summary=summary,
    )

    # 6. Save skills with embeddings
    await cv_repo.create_skills(db, cv.id, skill_rows)

    return CVUploadResponse(
        id=cv.id,
        name=cv.name,
        education=cv.education,
        experience_years=cv.experience_years,
        summary=cv.summary,
        topics=[r["skill"] for r in skill_rows if r["category"] == "topic"],
        file_url=cv.file_url,
    )


@router.get("/{cv_id}", response_model=CVOut)
async def get_cv(cv_id: str, db: Session = Depends(get_db)):
    cv = await cv_repo.get_cv_by_id(db, cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found.")
    return cv


@router.get("/", response_model=list[CVOut])
async def list_cvs(db: Session = Depends(get_db)):
    return await cv_repo.get_all_cvs(db)


@router.post("/match", response_model=list[MatchedCV])
async def match_cvs(request: MatchRequest, db: Session = Depends(get_db)):
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty.")

    # Embed the plain text description
    embeddings = await llm_service.emb([request.description])
    query_vector = embeddings[0]

    results = await cv_repo.search_matching_cvs(
        db,
        query_vector=query_vector,
        must_have=request.must_have or [],
        top_k=request.top_k,
    )

    if not results:
        return []

    return [MatchedCV(**r) for r in results]


# ---------- helpers ----------

async def _analyze_and_summarize(full_text: str) -> tuple[dict, str]:
    """Run LLM analysis and summary. Could be parallelized with asyncio.gather."""
    import asyncio
    analyzed, summary = await asyncio.gather(
        cv_service.analyze_cv(full_text),
        cv_service.generate_summary(full_text),
    )
    return analyzed, summary
