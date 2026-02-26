from sqlalchemy.orm import Session
from sqlalchemy import text
from App.models.video import Video
from App.models.chunk import VideoChunk
from App.services.llm import llm_service
import uuid

# ---------- VIDEO ----------

async def create_video(db: Session, title: str, owner_id: str, video_url: str) -> Video:
    video = Video(
        id=uuid.uuid4(),
        title=title,
        owner_id=owner_id,
        video_url=video_url
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


async def update_video_info(db: Session, video_id, transcript: str, description: str):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise ValueError("Video not found")
    video.transcript = transcript
    video.description = description
    db.commit()
    db.refresh(video)
    return video


async def get_video_by_id(db: Session, video_id):
    return db.query(Video).filter(Video.id == video_id).first()


async def get_all_videos(db: Session):
    return db.query(Video).all()


# ---------- CHUNKS ----------

async def create_chunk(
    db: Session,
    video_id,
    index: int,
    content: str,
    summary: str,
    start_time: float,
    end_time: float,
    embedding: list[float]
):
    chunk = VideoChunk(
        video_id=video_id,
        chunk_index=index,
        content=content,
        summary=summary,
        start_time=start_time,
        end_time=end_time,
        embedding=embedding
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


async def get_chunk_by_id(db: Session, chunk_id):
    return db.query(VideoChunk).filter(VideoChunk.id == chunk_id).first()


async def search_similar_chunks(db: Session, query_vector: list[float], top_k: int = 5):
    vector_str = "[" + ",".join(str(x) for x in query_vector) + "]"
    sql = text("""
        SELECT id
        FROM video_chunks
        ORDER BY embedding <-> CAST(:query_vector AS vector)
        LIMIT :limit
    """)
    result = db.execute(sql, {"query_vector": vector_str, "limit": top_k})
    chunk_ids = [row.id for row in result.fetchall()]

    return (
        db.query(VideoChunk)
        .filter(VideoChunk.id.in_(chunk_ids))
        .all()
    )

async def create_video_chunks(db, video_id: str, transcript: str, video_duration: float):


    from App.api.v1.routers.embeddings import to_float_list
 

    chunks_info = generate_chunks_with_timing(transcript, video_duration, max_words_per_chunk=100)

    for idx, info in enumerate(chunks_info):
        embedding_vector = await llm_service.emb([info["content"]])
        embedding_vector = to_float_list(embedding_vector[0])

        summary_text = await llm_service.chat([
            {"role": "user", "content": f"Summarize this text into a short point:\n{info['content']}"}
        ])

        chunk = VideoChunk(
            video_id=video_id,
            chunk_index=idx,
            content=info["content"],
            summary=summary_text,
            start_time=info["start_time"],
            end_time=info["end_time"],
            embedding=embedding_vector
        )
        db.add(chunk)

    db.commit()

def generate_chunks_with_timing(transcript: str, video_duration: float, max_words_per_chunk: int = 100):
    words = transcript.split()
    total_words = len(words)
    chunks = []

    seconds_per_word = video_duration / total_words if total_words > 0 else 0

    for i in range(0, total_words, max_words_per_chunk):
        chunk_words = words[i:i+max_words_per_chunk]
        chunk_text = " ".join(chunk_words)
        start_time = i * seconds_per_word
        end_time = (i + len(chunk_words)) * seconds_per_word
        chunks.append({
            "content": chunk_text,
            "start_time": start_time,
            "end_time": end_time
        })
    return chunks