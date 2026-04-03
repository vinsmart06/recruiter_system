from typing import Annotated
import uuid, os,json
from sklearn.metrics.pairwise import cosine_similarity
from backend.services.embedding_service import create_resume_embedding
from backend.services.ranking_service import rank_resumes
from backend.services.resume_parser import parse_resume_file 
from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from backend.database import get_multiple_candidates,get_one_candidate,update_candidate_score
from backend.agents.orchestrator import (
    run_recruiter_team,
    analyze_resumes,
    generate_questions,
    generate_questions_onjd
)
from backend.services.rag_search import semantic_candidate_search
from backend.llm_config import get_llm_config
from openai import OpenAI
from pydantic import BaseModel

class JDRequest(BaseModel):
    job_description: str
    
llm_config = get_llm_config()
client = OpenAI()
router = APIRouter(prefix="/process", tags=["Recruitment"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("/recruit")

async def run_recruitment(data: dict):

    jd = data["job_description"]
    resumes = data["resumes"]

    result = await run_recruiter_team(jd, resumes)

    return {"result": result}



#router = APIRouter(prefix="/process")

import asyncio

async def parse_all_resumes(files):

#    loop = asyncio.get_event_loop()

#    tasks = [
#        loop.run_in_executor(None, parse_resume_file, file)
#        for file in files
#    ]
    parsed_resumes = []

    for file in files:
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

                # Parse using file path
        text = parse_resume_file(file_path)

        parsed_resumes.append(text)
            
    return parsed_resumes   
#    results = await asyncio.gather(*tasks)

#    return results

@router.post("/rank_resumes")
#async def rank(data: dict):
async def rank(data: dict):
#    job_description: Annotated[str , Form(...)],
#    files: Annotated[list[UploadFile] , File(..., description="Upload multiple resume files")]
     job_description = data["job_description"]
     candidate_ids = data["candidate_ids"]

     parsed_resumes = get_multiple_candidates(candidate_ids)
 #   jd = data["job_description"]
 #   resume_files = data["resumes"]
 #    parsed_resumes = []
     print(data)     
     jd_embedding = create_resume_embedding(job_description)
     for cid in data["candidate_ids"]:
         candidate = get_one_candidate(cid)
         resume_embedding = json.loads(candidate["embedding"])
         score = cosine_similarity(
            [jd_embedding],
            [resume_embedding]
                )[0][0]
     #    score = cid["score"]
         score = float(score)
         print("score--",score)
         update_candidate_score(cid,score)
     ranked = rank_resumes(job_description, parsed_resumes)

    #return {"top_candidates": ranked}
  #   print(ranked)
     top_resumes = [r["resume"] for r in ranked[:3]]
     #top_resumes =parsed_resumes[:3]
     analysis = await analyze_resumes(job_description, top_resumes)
     #print("ranked::::", ranked) 
     print("analysis----", analysis)
     return {
        "top_candidates": ranked,
        "analysis": analysis
     }

@router.post("/start_interview")
async def start_interview(file: UploadFile = File(...), job_description: str = Form(...)):
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    resume_text = parse_resume_file(file_path)

    questions = await generate_questions(job_description, resume_text)

    return {
        "questions": questions,
        "resume_text": resume_text
    }

    
@router.post("/semantic_search")
async def semantic_search_api(data: dict):

    jd = data.get("job_description")

    if not jd:
        return {"error": "job_description is required"}

    results = semantic_candidate_search(jd)

    return {
        "top_candidates": results
    }

@router.post("/rewrite_jd")
def rewrite_query(data: JDRequest):

    jd = data.job_description
    prompt = f"""
    Convert this job description into a structured search query with skills:

    {jd}
    """

    res = client.chat.completions.create(
        model=llm_config["model"],
        messages=[{"role": "user", "content": prompt}]
    )
    print("LLM retruned JD",res.choices[0].message.content)
    return  {
        "original_jd": jd,
        "job_description": res.choices[0].message.content
    }

@router.post("/ask_questions")
async def ask_questions(data: dict):
 #   filename = f"{uuid.uuid4()}_{file.filename}"
 #   file_path = os.path.join(UPLOAD_FOLDER, filename)

 #   with open(file_path, "wb") as f:
 #       content = await file.read()
 #       f.write(content)

 #   resume_text = parse_resume_file(file_path)
    jd = data.get("job_description")
    questions = await generate_questions_onjd(jd)

    return {
        "questions": questions
        
    }