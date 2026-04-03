from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os
from backend.llm_config import get_llm_config

llm_config = get_llm_config()
model = OpenAIChatCompletionClient(
            model=llm_config["model"],
            api_key=llm_config["api_key"])


resume_agent = AssistantAgent(
    name="resume_agent",
    model_client=model,
    system_message="""
Rank resumes against job description.
Provide ATS score and explain ranking.
"""
)

question_agent = AssistantAgent(
    name="question_agent",
    model_client=model,
    system_message="""
You are a senior technical interviewer.

Generate 2 structured interview questions based on:

1. Job description

Mix of:
- technical
- problem solving
- practical scenario questions


Rules:
-
- Do NOT repeat questions.
- Format strictly like this:
"""
)

evaluation_agent = AssistantAgent(
    name="evaluation_agent",
    model_client=model,
    system_message="""
Evaluate candidate answers.
Return ONLY valid JSON.

Format:
{
  "scores": [
    {"question": 1, "score": 0},
    {"question": 2, "score": 0}
  ],
  "overall_score": 0,
  "feedback": ""
}

Rules:
- Output MUST be valid JSON.
- Do not include explanations before or after JSON.
- Give the rating of the answers out of 5.
"""
)

skill_gap_agent = AssistantAgent(
    name="skill_gap_agent",
    model_client=model,
    system_message="""
Identify skill gaps between resume and job description.
Return ONLY JSON.

Format:
{
  "missing_skills": [],
  "improvement_areas": [],
  "recommended_training": []
}

Rules:
- Output must be valid JSON.
- Do not include explanations outside JSON.


"""
)

training_agent = AssistantAgent(
    name="training_agent",
    model_client=model,
    system_message=f"""
You are an AI career coach.

Your task is to generate a structured training plan for a candidate based on their skill gaps.

Candidate Skill Gap Analysis:


Instructions:
Create a practical training roadmap to help the candidate improve the missing skills.

Return ONLY valid JSON in the following format:

{{
  "summary": "Short summary of candidate improvement needs",

  "training_plan": [
    {{
      "skill": "Skill name",
      "priority": "High | Medium | Low",
      "learning_resources": [
        {{
          "type": "Course | Book | Practice Project",
          "title": "Resource name",
          "description": "Short explanation"
        }}
      ],
      "practice_tasks": [
        "Task 1",
        "Task 2"
      ],
      "estimated_time_weeks": number
    }}
  ],

  "overall_estimated_time_weeks": number
}}

Rules:
- Return ONLY JSON.
- Do not include text outside JSON.
- Training plan must be practical and step-by-step.
- Prioritize the most critical skills first.
"""
)