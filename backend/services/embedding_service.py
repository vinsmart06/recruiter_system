
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()
from backend.llm_config import get_llm_config

llm_config = get_llm_config()

def create_resume_embedding(text):
    text = text[:8000]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding

   # return response.tolist()

def extract_candidate_name_llm(resume_text):

    prompt = f"""
Extract the candidate's full name from this resume.

Resume:
{resume_text}

Return ONLY the name.
"""

    response = client.chat.completions.create(
        model=llm_config["model"],
        messages=[{"role": "user", "content": prompt}]
    )

    name = response.choices[0].message.content.strip()

    return name