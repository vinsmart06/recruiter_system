from fastapi import APIRouter
from backend.agents.orchestrator import generate_questions
from backend.agents.orchestrator import evaluate_answers, detect_skill_gap, generate_training_plan

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/start")
async def start_interview(data: dict):

    job_description = data["job_description"]
    candidate_resume = data["resume"]

    questions = await generate_questions(
        job_description,
        candidate_resume
    )

    return {
        "questions": questions
    }


@router.post("/submit_answers")
async def submit_answers(data: dict):

    questions = data["questions"]
    answers = data["answers"]
    job_description = data["job_description"]
    print("answer", answers)
    evaluation = await evaluate_answers(
        questions,
        answers
    )
    print("evaluation", evaluation)
    skill_gap = await detect_skill_gap(
        evaluation,
        job_description
    )
    print("skill gap:",skill_gap)
    # Step 3: Generate training plan
    training_plan = await generate_training_plan(
        skill_gap
    )
    print("training_plan:",training_plan)
    return {
        "evaluation": evaluation,
        "skill_gap": skill_gap,
        "training_plan": training_plan
    }