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