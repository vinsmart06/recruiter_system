from fastapi import APIRouter
from backend.services.rag_search import semantic_candidate_search
from pydantic import BaseModel
from backend.agents.orchestrator import run_full_recruitment_pipeline

class SearchRequest(BaseModel):
    query: str
router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


@router.post("/search_candidates")
async def search_candidates_api(data: SearchRequest):

    results = semantic_candidate_search(data.query)

    return {"results": results}



@router.post("/recruiter/run")
async def run_recruiter(data: dict):

    jd = data["jd"]
    resumes = data["resumes"]
    answers = data.get("answers")

    result = await run_full_recruitment_pipeline(
        jd,
        resumes,
        answers
    )

    return result