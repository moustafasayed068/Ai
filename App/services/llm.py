import base64
import cohere
from App.core.config import settings


class LLMService:
    def __init__(self):
        self.client = cohere.ClientV2(settings.COHERE_API_KEY)

    def chat(self, messages: list, file_url: str | None = None) -> str:
        try:
            if file_url:
                last_message = messages[-1]["content"]
                messages[-1]["content"] = [
                    {"type": "document", "document": {"url": file_url}},
                    {"type": "text", "text": last_message}
                ]

            response = self.client.chat(
                model=settings.LLM_MODEL,
                messages=messages
            )

            return response.message.content[0].text

        except Exception as e:
            raise RuntimeError(f"LLM error: {e}") from e

    def analyze_image(self, image_bytes: bytes, mime_type: str) -> str:
        
        try:
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")


            image_data = f"data:{mime_type};base64,{encoded_image}"

            response = self.client.chat(
                model=settings.VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image_data},
                            {"type": "text", "text": "Describe this image briefly."},
                        ],
                    }
                ],
            )

            return response.message.content[0].text

        except Exception as e:
            raise RuntimeError(f"Vision error: {e}") from e
