from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from App.services.llm import LLMService
from App.client.supabase import SupabaseStorage
from App.core.dependencies import get_current_user
from App.schemas.user import UserResponse

router = APIRouter()
llm_service = LLMService()

def get_storage():
    return SupabaseStorage()

@router.post("/analyze-image")
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    storage: SupabaseStorage = Depends(get_storage)
):
    image_bytes = await file.read()
    mime_type = file.content_type

    try:
        image_url = await run_in_threadpool(
            storage.upload_image, image_bytes, file.filename, current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")


    try:
        result = await run_in_threadpool(
            llm_service.analyze_image,
            image_bytes,
            mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {e}")

    return {"analysis": result, "image_url": image_url}