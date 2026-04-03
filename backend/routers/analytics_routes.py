from fastapi import APIRouter
from backend.database import (
    get_total_candidates,
    get_interviewed_candidates,
    get_recommended_candidates,
    get_top_candidates
)
#from backend.database import get_all_candidates
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
async def analytics_summary():

    total = get_total_candidates()
    interviewed = get_interviewed_candidates()
    recommended = get_recommended_candidates()

    return {
        "total_candidates": total,
        "interviewed": interviewed,
        "recommended": recommended
    }


@router.get("/top_candidates")
async def top_candidates():

    candidates = get_top_candidates()

    return {
        "top_candidates": candidates
    }

@router.get("/dashboard")
def dashboard():
    total = get_total_candidates()
    candidates = get_top_candidates()

   # total = len(candidates)

    scores = [c["score"] for c in candidates if c["score"] is not None]

    avg_score = sum(scores) / len(scores) if scores else 0
    print("total:", total)
    print("candidates---", candidates)
    print("scores:::::", scores)
    print("avg score..........", avg_score)
    top_candidates = sorted(
        candidates,
        key=lambda x: x["score"],
        reverse=True
    )[:5]

    return {
        "total_candidates": total,
        "average_score": avg_score,
        "top_candidates": top_candidates
    }

