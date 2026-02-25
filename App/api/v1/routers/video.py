from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from App.db.session import get_db
from App.repositories import video as video_repo
from App.repositories.video import to_float_list, get_storage, _extract_public_url, _cosine_similarity
from App.services.llm import LLMService
from App.client.supabase import SupabaseStorage
from App.core.dependencies import get_current_user
from App.schemas.user import UserResponse
from App.schemas.video import VideoResponse, VideoSearchResult
from typing import Optional
import tempfile
import whisper
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
llm_service = LLMService()
whisper_model = whisper.load_model("base")

# --- Endpoints --- #

@router.post("/videos/", response_model=VideoResponse)
async def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: SupabaseStorage = Depends(get_storage),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Upload a video: stores it in Supabase, transcribes via Whisper,
    generates a Cohere embedding from the transcript, and saves it
    directly onto the Video row (videos.embedding column).
    """
    try:
        # 1. Read video bytes
        file_bytes = await video_file.read()

        # 2. Upload to Supabase Video Bucket
        try:
            storage_resp = await run_in_threadpool(
                storage.upload_video, file_bytes, video_file.filename, str(current_user.id)
            )
            public_url = _extract_public_url(storage_resp)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload to storage failed: {e}")

        # 3. Create Video record in DB
        video = await video_repo.create_video(
            db, title, description, str(current_user.id), public_url or ""
        )

        # 4. Transcribe audio with Whisper (blocking → threadpool)
        transcript: Optional[str] = None
        try:
            def _transcribe() -> str:
                with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
                    tmp.write(file_bytes)
                    tmp.flush()
                    result = whisper_model.transcribe(tmp.name)
                    return result.get("text", "").strip()

            transcript = await run_in_threadpool(_transcribe)
        except Exception as transcribe_error:
            logger.warning(f"Whisper transcription failed: {transcribe_error}")

        # 5. Save transcript
        if transcript:
            await video_repo.update_video_transcript(db, video.id, transcript)

        # 6. Generate embedding and save directly onto the Video row
        #    (videos.embedding column – NOT the separate embeddings/chats table)
        if transcript:
            try:
                embeddings = await llm_service.emb([transcript])
                if embeddings and isinstance(embeddings, list) and len(embeddings) > 0:
                    embedding_vector = to_float_list(embeddings[0])
                    await video_repo.save_video_embedding(db, video.id, embedding_vector)
            except Exception as emb_error:
                logger.warning(f"Embedding generation failed for video {video.id}: {emb_error}")

        return VideoResponse(
            video_id=video.id,
            title=video.title,
            description=video.description,
            transcript=transcript,
            video_url=public_url or "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=list[VideoSearchResult])
async def search_videos(
    query: str,
    top_k: int = 5,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Semantic video search.

    Embeds the user's text query with Cohere, then ranks all stored video
    embeddings (videos.embedding column) by cosine similarity and returns
    the top-k matching videos with their similarity score.
    """
    # 1. Embed the search query
    try:
        query_embeddings = await llm_service.emb([query])
        if not query_embeddings or not isinstance(query_embeddings, list):
            raise HTTPException(status_code=500, detail="Failed to embed search query")
        query_vector = to_float_list(query_embeddings[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")

    # 2. Fetch all videos that have an embedding stored (videos.embedding IS NOT NULL)
    videos_with_emb = await video_repo.get_videos_with_embeddings(db)
    if not videos_with_emb:
        raise HTTPException(
            status_code=404,
            detail="No videos with embeddings found. Upload and transcribe videos first."
        )

    # 3. Score each video's embedding against the query vector
    scored: list[tuple[float, object]] = []
    for video in videos_with_emb:
        if not video.embedding:
            continue
        score = _cosine_similarity(query_vector, list(video.embedding))
        scored.append((score, video))

    if not scored:
        raise HTTPException(status_code=404, detail="No matching videos found")

    # 4. Sort descending by similarity and take top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:max(1, top_k)]

    # 5. Build response
    return [
        VideoSearchResult(
            video_id=video.id,
            title=video.title,
            description=video.description,
            video_url=video.video_url,
            transcript=video.transcript,
            similarity_score=round(score, 4),
        )
        for score, video in top_results
    ]