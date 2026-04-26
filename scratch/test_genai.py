
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_genai():
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=os.getenv("MODEL_NAME"),
            contents="Say hello"
        )
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_genai()
