from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

print("API key found:", bool(api_key))
print("Model:", model)

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

print("Sending request...")
interaction = client.interactions.create(
    model=model,
    input="Say hello in one short sentence."
)

print("Response:")
print(interaction.output_text)
