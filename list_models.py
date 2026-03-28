from google import genai
from config import Config

client = genai.Client(api_key=Config.GEMINI_API_KEY)

print("Listing models...")
try:
    for m in client.models.list():
        print(f"Name: {m.name}, Supported: {m.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")
