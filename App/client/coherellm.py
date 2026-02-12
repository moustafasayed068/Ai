import cohere
from App.core.config import COHERE_API_KEY

co = cohere.Client(COHERE_API_KEY)

def chat_with_llm(user_message: str):
    response = co.chat(
        model="command-r-08-2024",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ]
    )
    return response['output'][0]['content']
