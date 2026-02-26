from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from App.db.session import get_db
from App.services.video import VideoService
from App.repositories import video as video_repo
from App.schemas.video import VideoResponse
from App.schemas.video import ChunkResponse, VideoWithChunksResponse
from App.schemas.video import SearchResult
from App.services.llm import LLMService
from App.core.dependencies import get_current_user
from App.schemas.user import UserResponse

router = APIRouter()
llm_service = LLMService()


# ---------- UPLOAD VIDEO ----------



# App/api/v1/routers/video.py

@router.post("/videos/", response_model=VideoWithChunksResponse)
async def upload_video(
    title: str = Form(...),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    file_bytes = await video_file.read()

    video = await VideoService.upload_and_process_video(
        db=db,
        file_bytes=file_bytes,
        filename=video_file.filename,
        title=title,
        user_id=str(current_user.id)
    )

    return VideoWithChunksResponse(
        id=video.id,
        title=video.title,
        description=video.description,  # optional: you can return first chunk summary instead
        video_url=video.video_url,
        created_at=video.created_at,
        chunks=video.chunks
    )


# ---------- GET ALL VIDEOS ----------

@router.get("/videos", response_model=list[VideoResponse])
async def get_all_videos(db: Session = Depends(get_db)):
    return await video_repo.get_all_videos(db)


# ---------- GET VIDEO BY ID ----------

@router.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, db: Session = Depends(get_db)):
    video = await video_repo.get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


# ---------- GET CHUNK BY ID ----------

@router.get("/chunks/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(chunk_id: str, db: Session = Depends(get_db)):
    chunk = await video_repo.get_chunk_by_id(db, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return chunk


# ---------- SEARCH ----------

@router.get("/search", response_model=list[SearchResult])
async def search(query: str, top_k: int = 5, db: Session = Depends(get_db)):
    emb = await llm_service.emb([query])
    query_vector = emb[0]
    results = await video_repo.search_similar_chunks(db, query_vector, top_k)

    # convert raw rows into SearchResult
    response = []
    for r in results:
        response.append(SearchResult(
            chunk_id=r.id,
            video_id=r.video_id,
            title=r.video.title,
            summary=r.summary,
            similarity_score=0.0,  # optional: calculate cosine if needed
            start_time=r.start_time,
            end_time=r.end_time
        ))
    return response