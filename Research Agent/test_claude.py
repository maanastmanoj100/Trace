
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("ANTHROPIC_MODEL")

if not api_key or not model:
    raise ValueError("Check your .env file for the API key and model ID.")

client = Anthropic(api_key=api_key)

try:
    response = client.messages.create(
        model=model,
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: TRACE connection successful"
            }
        ],
    )
    print(response.content[0].text)

except Exception as error:
    print(f"Connection failed: {error}")
