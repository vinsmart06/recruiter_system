import os
from dotenv import load_dotenv

load_dotenv()

def get_llm_config():
    return {
        "model": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "temperature": 0
    }