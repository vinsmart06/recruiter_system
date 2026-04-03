from fastapi import APIRouter, UploadFile, File
from backend.services.resume_parser import parse_resume_file, parse_resume
from backend.services.embedding_service import create_resume_embedding, extract_candidate_name_llm
from backend.database import save_candidate
from backend.services.search_service import semantic_candidate_search
import os
import uuid
from backend.database import get_one_candidate

router = APIRouter(prefix="/candidate", tags=["Candidate"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"{UPLOAD_FOLDER}/{filename}"
    # Save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

 #   content = await file.read()
  #  resume_text = content.decode("utf-8", errors="ignore")

    parsed_resume = parse_resume_file(file_path)
    parsed = parse_resume(parsed_resume)
    name = parsed["name"]
    email = parsed["email"]
    phone = parsed["phone"]
    if not name:
      name = extract_candidate_name_llm(parsed_resume)
 #   print("name1---",name1)
    embedding = create_resume_embedding(parsed_resume)

    candidate_id = save_candidate(
        parsed_resume,
        embedding,
        filename,
        name,
        email,
        phone
    )

    return {
        "candidate_id": candidate_id,
        "message": "Resume uploaded successfully"
    }

@router.get("/search")
async def search_candidates(query: str):

    results = semantic_candidate_search(query)

    return {
        "query": query,
        "results": results
    }

@router.get("/{candidate_id}")
async def get_candidate(candidate_id: int):

   
    candidate = get_one_candidate(candidate_id)
    if not candidate:
        return {"message": "Candidate not found"}
    return candidate

