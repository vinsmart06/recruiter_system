from autogen_agentchat.teams import RoundRobinGroupChat
import json, re
import asyncio
from backend.agents.recruiter_agents import (
    resume_agent,
    question_agent,
    evaluation_agent,
    skill_gap_agent,
    training_agent
)


async def run_recruiter_team(jd, resumes):

    team = RoundRobinGroupChat(
        participants=[
            resume_agent,
            question_agent,
            evaluation_agent,
            skill_gap_agent,
            training_agent
        ],
        max_turns=5
    )

    task = f"""
Job Description:
{jd}

Candidate Resumes:
{resumes}

Steps:
1 Rank resumes
2 Generate interview questions
3 Evaluate candidate answers
4 Identify skill gaps
5 Suggest learning roadmap
"""

    result = await team.run(task=task)

    return result.messages[-1].content

async def analyze_resumes(jd, resumes):
    resume_text = ""

    for i, r in enumerate(resumes):
        resume_text += f"\nCandidate {i+1}:\n{r}\n"
        
    prompt = f"""
    You are an AI recruitment expert.

    Job Description:
    {jd}
    Analyze the following resumes and return ONLY JSON in this format:

    {{
        "candidates":[
        {{
         "name":"Candidate name",
          "match_score":0-100,
         "strengths":[list of strengths],
         "weaknesses":[list of weaknesses]
        }}
    ],
    "summary":"short summary of best candidate"
    }}
    Candidate Resumes:
    {resume_text}

    """


#    response = await resume_agent.run(
#        messages=[
#            {"role": "user", "content": f"JD: {jd}\nResumes:{resumes}"}
#        ]
#    )
    response = await resume_agent.run(task=prompt)
    #return response
 
    

    text = response.messages[-1].content

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        data = json.loads(match.group())
    else:
        data = {"candidates": [], "summary": text}

    return data

async def generate_questions(jd, resume):

    task = f"""
    Job Description:
    {jd}

    Resume:
    {resume}

    Generate 2 interview questions.
    """

#    result = await question_agent.run(task)
#    return result.messages[-1].content

    response = await question_agent.run(task=task)

    questions_text = response.messages[-1].content
    questions = questions_text.split("\n")
    questions = [q.strip() for q in questions if q.strip()]
    return questions

async def evaluate_answers(questions, answers):

    task = f"""
    Questions:
    {questions}

    Answers:
    {answers}

    Evaluate answers and score candidate.
    """

    result = await evaluation_agent.run(task=task)
    content = result.messages[-1].content
 #   print("LLM OUTPUT:", content)
    if not content:
     return {"error": "Empty response from LLM"}
    return json.loads(content)


async def generate_training_plan(skill_gaps):
    prompt = f"""
    Candidate skill gaps:

    {skill_gaps}

    Create a structured training plan.

    Include:
    - learning topics
    - suggested resources
    - timeline
    """
    #result = await training_agent.run(task=prompt)
    result = await run_with_timeout(training_agent, prompt, timeout=15)

    if isinstance(result, dict) and "error" in result:
        return result
    content = result.messages[-1].content
#    print("LLM OUTPUT training plan:", content)

    if not content:
     return {"error": "Empty response from LLM"}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        
        if match:
            return json.loads(match.group())
        
        return {
            "error": "Invalid training plan  JSON from LLM",
            "raw_output": content
        }

async def detect_skill_gap(evaluation_result, job_description):

    prompt = f"""
    You are an AI hiring expert.

    Evaluation Result:
    {evaluation_result}

    Job Description:
    {job_description}

    Identify candidate skill gaps.

    Return a short list of missing skills.
    """
 #   result = await skill_gap_agent.run(task=prompt)
    result = await run_with_timeout(skill_gap_agent, prompt, timeout=15)

    if isinstance(result, dict) and "error" in result:
        return result
    content = result.messages[-1].content
  #  print("LLM OUTPUT skill gap:", content)
    if not content:
     return {"error": "Empty response from LLM"}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        
        if match:
            return json.loads(match.group())
        
        return {
            "error": "Invalid skill gap JSON from LLM",
            "raw_output": content
        }
    
async def run_full_recruitment_pipeline(jd, resumes, answers=None):

    # STEP 1: Analyze resumes
    resume_analysis = await analyze_resumes(jd, resumes)

    best_candidate = None
    if resume_analysis["candidates"]:
        best_candidate = max(
            resume_analysis["candidates"],
            key=lambda x: x["match_score"]
        )

    best_resume = resumes[0] if resumes else ""

    # STEP 2: Generate interview questions
    questions = await generate_questions(jd, best_resume)

    result = {
        "resume_analysis": resume_analysis,
        "questions": questions
    }

    # STEP 3: Evaluate answers (only if answers provided)
    if answers:

        evaluation = await evaluate_answers(questions, answers)

        # STEP 4: Detect skill gaps
        skill_gaps = await detect_skill_gap(evaluation, jd)

        # STEP 5: Training plan
        training_plan = await generate_training_plan(skill_gaps)

        result["evaluation"] = evaluation
        result["skill_gaps"] = skill_gaps
        result["training_plan"] = training_plan

    return result

async def generate_questions_onjd(jd):

    task = f"""
    Job Description:
    {jd}

    Generate 2 interview questions.
    """

#    result = await question_agent.run(task)
#    return result.messages[-1].content

    response = await question_agent.run(task=task)

    questions_text = response.messages[-1].content
    questions = questions_text.split("\n")
    questions = [q.strip() for q in questions if q.strip()]
    return questions


async def run_with_timeout(agent, task, timeout=15, retries=2):
    for attempt in range(retries):
        try:
            result = await asyncio.wait_for(
                agent.run(task=task),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            if attempt == retries - 1:
                return {
                    "error": f"{agent.name} timed out after {timeout}s"
                }