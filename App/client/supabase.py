from supabase import create_client, Client
from App.core.config import settings
import uuid

class SupabaseStorage:
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.chat_bucket = settings.SUPABASE_BUCKET
        self.video_bucket = settings.SUPABASE_VIDEO_BUCKET
        self.image_bucket = settings.SUPABASE_IMAGE_BUCKET
        self.cv_bucket = settings.SUPABASE_CV_BUCKET

    def upload_video(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        file_path = f"{user_id}/{uuid.uuid4()}_{filename}"

        self.client.storage.from_(self.video_bucket).upload(
            file_path,
            file_bytes,
            {"content-type": "video/mp4"}
        )

        return self.client.storage.from_(self.video_bucket).get_public_url(file_path)

    def upload_file(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        file_path = f"{user_id}/{uuid.uuid4()}_{filename}"

        self.client.storage.from_(self.chat_bucket).upload(file_path, file_bytes)

        return self.client.storage.from_(self.chat_bucket).get_public_url(file_path)

    def upload_image(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        file_path = f"{user_id}/{filename}"

        self.client.storage.from_(self.image_bucket).upload(
            file_path,
            file_bytes,
            {"content-type": "image/jpeg"}
        )

        return self.client.storage.from_(self.image_bucket).get_public_url(file_path)
    

    def upload_cv(self, file_bytes: bytes, filename: str, user_id: str) -> str:
        file_path = f"{user_id}/{uuid.uuid4()}_{filename}"
        self.client.storage.from_(self.cv_bucket).upload(
            file_path,
            file_bytes,
            {"content-type": "application/pdf"}
        )
        return self.client.storage.from_(self.cv_bucket).get_public_url(file_path)