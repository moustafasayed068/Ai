import tempfile
from fastapi.concurrency import run_in_threadpool
from moviepy.editor import VideoFileClip
import whisper
from App.services.llm import LLMService
from App.repositories import video as video_repo
from App.client.supabase import SupabaseStorage

llm_service = LLMService()
whisper_model = whisper.load_model("base")


class VideoService:

    @staticmethod
    async def upload_and_process_video(db, file_bytes, filename, title, user_id):
        storage = SupabaseStorage()

        # Upload video to Supabase
        public_url = storage.upload_video(file_bytes, filename, user_id)

        # Save to temporary file to work with Whisper & moviepy
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(file_bytes)
            tmp.flush()

            # Get actual video duration
            clip = VideoFileClip(tmp.name)
            video_duration = clip.duration  # seconds as float

            # Transcribe video
            result = whisper_model.transcribe(tmp.name)
            transcript = result.get("text", "").strip()

        # Save Video record
        from App.models.video import Video
        video = Video(
            title=title,
            owner_id=user_id,
            video_url=public_url,
            transcript=transcript
        )
        db.add(video)
        db.commit()
        db.refresh(video)

        # Split transcript into chunks and create embeddings + summaries
        await VideoService._process_transcript(db, video, transcript, video_duration)

        db.refresh(video)

        return video

    @staticmethod
    async def _transcribe(file_bytes: bytes) -> str:
        """Transcribe video using Whisper."""
        def _run():
            with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                result = whisper_model.transcribe(tmp.name)
                return result.get("text", "").strip()
        return await run_in_threadpool(_run)

    @staticmethod
    def _split_into_chunks(text: str, chunk_size: int = 80):
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return chunks

    @staticmethod
    async def _process_transcript(db, video, transcript: str, video_duration: float):
        # Generate video description
        description = await llm_service.chat([
            {"role": "user", "content": f"Summarize this video in 3 sentences:\n\n{transcript}"}
        ])
        await video_repo.update_video_info(db, video.id, transcript, description)

        # Split transcript into chunks
        chunks = VideoService._split_into_chunks(transcript)
        num_chunks = len(chunks)
        chunk_length = video_duration / max(1, num_chunks)  # duration per chunk

        for idx, chunk in enumerate(chunks):
            # Short summary of chunk
            summary = await llm_service.chat([
                {"role": "user", "content": f"Give one short main idea sentence:\n\n{chunk}"}
            ])
            # Embedding
            emb = await llm_service.emb([chunk])
            vector = emb[0]

            # Actual start/end timestamps
            start = idx * chunk_length
            end = min((idx + 1) * chunk_length, video_duration)

            await video_repo.create_chunk(
                db,
                video.id,
                idx,
                chunk,
                summary,
                start,
                end,
                vector
            )