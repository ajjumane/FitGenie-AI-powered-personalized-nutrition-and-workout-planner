import sys
try:
    from google import genai
    print("Found 'google-genai' SDK")
except ImportError:
    print("Failed to find 'google-genai' SDK")

try:
    import google.generativeai as gai
    print("Found 'google-generativeai' SDK")
except ImportError:
    print("Failed to find 'google-generativeai' SDK")

from config import Config
print(f"Using API Key: {Config.GEMINI_API_KEY[:10]}...")

# Try a simple call if sdk exists
if 'google.genai' in sys.modules or 'genai' in sys.modules:
    try:
        from google import genai
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Hello, say 'AI works!'"
        )
        print(f"AI Response: {response.text}")
    except Exception as e:
        print(f"AI Call failed with (google-genai): {e}")

if 'google.generativeai' in sys.modules:
    try:
        import google.generativeai as gai
        gai.configure(api_key=Config.GEMINI_API_KEY)
        model = gai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello, say 'AI works!'")
        print(f"AI Response (gai): {response.text}")
    except Exception as e:
        print(f"AI Call failed with (google-generativeai): {e}")
