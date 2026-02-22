from supabase import create_client, Client
from App.core.config import settings
import uuid

IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/svg+xml"}

class SupabaseStorage:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket = settings.SUPABASE_BUCKET
        self.image_bucket = settings.SUPABASE_IMAGE_BUCKET
    
    def upload_file(self, file_bytes: bytes, filename: str, user_id: int) -> str:
        file_path = f"{user_id}/{uuid.uuid4()}_{filename}"
        self.client.storage.from_(self.bucket).upload(file_path, file_bytes)
        return self.client.storage.from_(self.bucket).get_public_url(file_path)
    
    def upload_image(self, file_bytes: bytes, filename: str, user_id) -> str:
        path = f"{user_id}/{filename}"
        self.client.storage.from_(self.image_bucket).upload(
            path, file_bytes, {"content-type": "image/jpeg"} 
        )
        return self.client.storage.from_(self.image_bucket).get_public_url(path)