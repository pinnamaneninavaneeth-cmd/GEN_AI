from dotenv import load_dotenv
from google import genai
import os

load_dotenv(override=True)

key = os.getenv("GEMINI_API_KEY")

if not key:
    print("API KEY MISSING")
else:
    try:
        client = genai.Client(api_key=key)

        print("Connecting to Gemini...")

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents="Say Hello"
        )

        print("Gemini Response:")
        print(response.text)

    except Exception as e:
        print("ERROR:", e)