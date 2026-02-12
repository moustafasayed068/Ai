import cohere
from App.core.config import settings

# Initialize Cohere client
co = cohere.ClientV2(settings.COHERE_API_KEY)

def get_chat_response(user_message: str):
    """Chat with Cohere"""
    try:
        response = co.chat(
            model="command-r-08-2024",  # Updated model
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.message.content[0].text
    except Exception as e:
        raise Exception(f"Cohere chat error: {str(e)}")