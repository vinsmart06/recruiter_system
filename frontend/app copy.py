import streamlit as st
import requests
import json
import pdfplumber
import docx
import uuid, os
import pandas as pd
BACKEND_URL = "http://localhost:8000"


st.set_page_config(
    page_title="AI Recruiter System",
    layout="wide"
)
# Create session once
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
session_id = st.session_state.session_id    
memory = {}
def save_memory(session_id, data):
    memory[session_id] = data
def get_memory(session_id):
    return memory.get(session_id, {})

st.title("🤖 AI Recruiter System")
# --------------------------------------------------
# Resume Text Extraction
# --------------------------------------------------
def extract_text(file):

    if file.type == "application/pdf":
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            return "\n".join(p.page.extract_text() or "" for p in pdf.pages)

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import docx
        doc = docx.Document(file)
        return "\n".join(p.text for p in doc.paragraphs)

    else:
        return file.read().decode("utf-8", errors="ignore")
# --------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Recruiter Dashboard",
        "Candidate Interview",
        "Analytics",
    #    "All in one",
        "All agents call"
    ]
)

# --------------------------------------------------
# 1️⃣ Recruiter Dashboard
# --------------------------------------------------

if menu == "Recruiter Dashboard":

    st.header("📄 Recruiter Dashboard")

    job_description = st.text_area(
        "Paste Job Description"
    )


    uploaded_files = st.file_uploader(
        "Upload Candidate Resumes",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt"]
    )


    if st.button("Analyze Resumes"):
        if not job_description:
            st.warning("Please enter job description")
            st.stop()
        if not uploaded_files:
           st.warning("Please upload resumes")
           st.stop()
        with st.spinner("Analyzing resumes..."):
        
            candidate_ids = []

            for file in uploaded_files:
                files={
                    "file": (file.name, file, file.type)
                }           
                response_upload = requests.post(
                        f"{BACKEND_URL}/candidate/upload_resume",
                          files=files
                            )
                if response_upload.status_code == 200:
                    candidate_ids.append(
                    response_upload.json()["candidate_id"]
                    )
                else:
                    st.error("Failed to upload resume")
                    st.stop()
            data = {
                "job_description": job_description,
                 "candidate_ids": candidate_ids
                     }
            try:
                response = requests.post(
                    f"{BACKEND_URL}/process/rank_resumes",
                    #files=files,
                    json=data
                )
                #    response_save = requests.post(f"{BACKEND_URL}/candidate/upload_resume",
            #        files=files,
            #        data=data)
                

                if response.status_code != 200:
                    st.error("Backend error")
                    st.stop()
                else:
                    result = response.json()   
            except Exception as e:
               st.error(f"API error: {e}")
               st.stop()
            











            st.subheader("🏆 Top Candidates")

            for idx, candidate in enumerate(result["top_candidates"]):
            #    name = candidate.get("name", f"Candidate {idx+1}")
                name = candidate.get("resume_name", "candidate")
                score = candidate.get("score", 0)

                st.write(f"{name} - Score: {round(score,2)}")    
            #  resume, score = candidate

            #    st.write(
            #        f"Candidate {idx+1} - Score: {round(score,2)}"
            #    )

            st.subheader("🧠 AI Resume Analysis")

            #st.write(result["analysis"])
            analysis = result["analysis"]
            for candidate in analysis["candidates"]:
                st.markdown(f"### {candidate['name']}")
                st.write("Match Score:", candidate["match_score"])
                st.progress(candidate["match_score"] / 100)
                st.markdown("✅ Strengths")
                for s in candidate["strengths"]:
                    st.write(f"- {s}")
                
                st.markdown("⚠ Weaknesses")
                for w in candidate["weaknesses"]:
                    st.write(f"-{w}")
            st.subheader("📊 Summary")
            st.write(analysis["summary"])

# --------------------------------------------------
# 2️⃣ Candidate Interview
# --------------------------------------------------

elif menu == "Candidate Interview":

    st.header("🎤 AI Interview")

    candidate_name = st.text_input("Candidate Name")

    job_description = st.text_area(
        "Job Description"
    )
    resume_file = st.file_uploader(
        "Upload Candidate Resume",
        type=["pdf", "docx", "txt"]
    )
    if st.button("Generate Interview Questions"):
        if not job_description or not resume_file:
           st.warning("Please provide job description and resume")
           st.stop()
        files = {
            "file": (resume_file.name, resume_file, resume_file.type)
        }
          
        data = {
                 "job_description": job_description
         #        "resume": "Candidate resume text"
                }
        try:
            response = requests.post(
                f"{BACKEND_URL}/process/start_interview",
                files=files,
                data=data
            )
            if response.status_code != 200:
                st.error("Backend error")
                st.stop()
            else:
                questions = response.json()["questions"]

                st.session_state["questions"] = questions
                st.session_state["job_description"] = job_description  
        except Exception as e:
         st.error(f"API error: {e}")
         st.stop()
    if "questions" in st.session_state:
        import re
        st.subheader("Interview Questions")
     #   print(st.session_state["questions"])
        answers = []
        clean_questions = []
        for q in st.session_state["questions"]:
            q = q.strip()

        # keep only lines starting with number
            if re.match(r"^\d+\.", q):
               clean_questions.append(q)
        clean_questions = list(dict.fromkeys(clean_questions))
        for i, q in enumerate(st.session_state["questions"]):
            q = re.sub(r"^\d+\.\s*", "", q)   
        #    print(q) 
            st.write(f"**Q{i+1}. {q}**")
        #    print(st.write(f"**Q{i+1}. {q}**"))
        #    ans = st.text_area(
        #        f"Answer {i+1}",
        #        key=f"ans{i}"
        #    )
            ans = st.text_area("your answer", key=f"answer_{i}")
            answers.append(ans)
                  # 8. Save memory
        memory = get_memory(session_id) 
        memory.setdefault("jd", job_description)
        memory.setdefault("interview_history", [])
        # Step 2: Initialize if first time
        if not memory:
            memory = {
                "jd": job_description,
                "interview_history": []
            }          
        # Step 3: Append new Q&A
        memory["interview_history"].append({
            "question": questions,
            "answer": answers
        })
        save_memory(session_id,memory)
        
        #questions= st.session_state["questions"]

        if st.button("Submit Answers"):
            if any(ans.strip() == "" for ans in answers):
                st.warning("Please answer all questions before submitting.")
                st.stop()    
            payload = {
                "candidate_name": candidate_name,
                "questions": st.session_state["questions"],    
                "answers": answers,
                "job_description": st.session_state["job_description"]
            }
            try:
                response = requests.post(
                    f"{BACKEND_URL}/interview/submit_answers",
                    json=payload
                )
                if response.status_code != 200:
                    st.error("Backend error")
                    st.stop()
                else:
                    result = response.json()    
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()        
                
            st.session_state["evaluation"] = result["evaluation"]

            st.session_state["skill_gap"] = result["skill_gap"] 

            st.session_state["training_plan"] = result["training_plan"] 

            st.subheader("📊 Evaluation of Candidate")
            evaluation = st.session_state["evaluation"]
            # Overall Score
            st.metric("Overall Score", evaluation["overall_score"])

            st.write("### Question Scores")

            for s in evaluation["scores"]:
                st.write(f"**Question {s['question']}** : {s['score']} / 5")

            st.write("### Feedback")
            st.info(evaluation["feedback"])

         #   st.write(result["evaluation"])
            
            st.subheader("🧠 Skill Gap Analysis")
            skill_gap = st.session_state["skill_gap"]

            col1, col2 = st.columns(2)

            with col1:
                st.write("### Missing Skills")
                for skill in skill_gap["missing_skills"]:
                    st.markdown(f"- {skill}")

            with col2:
                st.write("### Improvement Areas")
                for area in skill_gap["improvement_areas"]:
                    st.markdown(f"- {area}")

            st.write("### Recommended Training")

            for course in skill_gap["recommended_training"]:
                st.markdown(f"📘 {course}")
         #   st.write(result["skill_gap"])

            st.subheader("🎓 Personalized Training Plan")
         #   st.write(result["training_plan"])
            training = st.session_state["training_plan"]

            st.success(training["summary"])

            st.write(f"⏳ **Total Estimated Time:** {training['overall_estimated_time_weeks']} weeks")

            for skill in training["training_plan"]:

                with st.expander(f"📚 {skill['skill']} ({skill['priority']} Priority)"):

                    st.write("### Learning Resources")

                    for res in skill["learning_resources"]:
                        st.markdown(f"""
                            **{res['type']}**  
                            📖 {res['title']}  
                            {res['description']}
                            """)

                    st.write("### Practice Tasks")

                    for task in skill["practice_tasks"]:
                       st.markdown(f"- {task}")

                    st.write(f"⏱ Estimated Time: **{skill['estimated_time_weeks']} weeks**")

# --------------------------------------------------
# 3️⃣ Analytics Dashboard
# --------------------------------------------------

elif menu == "Analytics":
    job_description = st.text_area(
        "Job Description"
    )
    st.header("📈 Hiring Analytics")

    if st.button("Load Analytics"):
        try:
            response = requests.get(
                f"{BACKEND_URL}/analytics/dashboard"
            )
            if response.status_code != 200:
                st.error("Backend error")
                st.stop()
            else:
                data = response.json()
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()  
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Total Candidates",
                data["total_candidates"]
            )

        with col2:
            st.metric(
                "Average Score",
                round(data["average_score"], 2)
            )

        st.subheader("🏆 Top Candidates")

        for c in data["top_candidates"]:

            st.write(
                f"{c['name']} - Score {c['score']}"
            )

    if st.button("Find Best Candidates"):
#      job_description = st.text_area(
 #       "Job Description"
 #   )
      print("job::",job_description)  
      if not job_description:
        st.warning("Please enter job description")
        st.stop()

      rewrite_response = requests.post(
                f"{BACKEND_URL}/process/rewrite_jd",
                json={"job_description": job_description}
            )  
      job_description = rewrite_response.json()["job_description"]
     # print("rewite job::",job_description)    
      payload = {
        "job_description": job_description
    }

      response = requests.post(
          f"{BACKEND_URL}/process/semantic_search",
          json=payload
      )

      results = response.json()
      print("results:::",results)
      if response.status_code != 200:
        st.error(response.get("error", "Unknown backend error"))
        st.stop()
    #  for c in results["top_candidates"]:
    #      st.write(c)
      st.subheader("🏆 Top Matching Candidates")

      candidates = results["top_candidates"]

      for i, c in enumerate(candidates):
        similarity = c["similarity_score"]

     #   score = max(0, min(100, round((1 - similarity) * 100, 2)))
        score = round(100 / (1 + similarity), 2)
        with st.container():

            col1, col2 = st.columns([3,1])

            with col1:
                st.markdown(f"### 🥇 Rank #{i+1} — {c['name']}")
                st.write(f"📧 {c['email']}")
                st.write(f"📄 Resume File: {c['file_name']}")

            with col2:
                st.metric("Match Score", f"{score}%")
                st.progress(score/100)

            with st.expander("View Resume Preview"):
                preview = c["resume_text"][:800]
                st.write(preview)

            st.divider()
            

      df = pd.DataFrame(results["top_candidates"])

      df["match_score"] = (1 - df["similarity_score"]) * 100

      st.dataframe(
         df[["name","email","file_name","match_score"]],
             width="stretch",
             hide_index=True
         )
elif menu == "All in one":
    job_description = st.text_area(
        "Paste Job Description"
    )


    uploaded_files = st.file_uploader(
        "Upload Candidate Resumes",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt"]
    )
    if st.button("Analyze Resumes"):
        if not job_description:
            st.warning("Please enter job description")
            st.stop()
        if not uploaded_files:
           st.warning("Please upload resumes")
           st.stop()
        with st.spinner("Analyzing resumes..."):
            candidate_ids = []
            answers=[]
            for file in uploaded_files:
                files={
                    "file": (file.name, file, file.type)
                }
                payload = {
                    "jd": job_description,
                    "resumes": file,
                    "answers": answers
                    }           
                response_upload = requests.post(
                        f"{BACKEND_URL}/recruiter/run",
                          json=payload
                            )
                if response_upload.status_code == 200:
                    candidate_ids.append(
                    response_upload.json()["candidate_id"]
                    )
                else:
                    st.error("Failed to upload resume")
                    st.stop()
            data = {
                "job_description": job_description,
                 "candidate_ids": candidate_ids
                     }
elif menu == "All agents call":
    st.header("📄 Recruiter Dashboard")

    job_description = st.text_area(
        "Paste Job Description"
    )


    uploaded_files = st.file_uploader(
        "Upload Candidate Resumes",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt"]
    )


    if st.button("Analyze Resumes"):
        if not job_description:
            st.warning("Please enter job description")
            st.stop()
        if not uploaded_files:
           st.warning("Please upload resumes")
           st.stop()
        st.session_state.pop("questions", None)
        st.session_state.pop("evaluation", None)
        st.session_state.pop("skill_gap", None)
        st.session_state.pop("training_plan", None)
        for key in list(st.session_state.keys()):
            if key.startswith("answer_"):
               del st.session_state[key]
        with st.spinner("Analyzing resumes..."):
        
            candidate_ids = []

            for file in uploaded_files:
                files={
                    "file": (file.name, file, file.type)
                }           
                response_upload = requests.post(
                        f"{BACKEND_URL}/candidate/upload_resume",
                          files=files
                            )
                if response_upload.status_code == 200:
                    candidate_ids.append(
                    response_upload.json()["candidate_id"]
                    )
                else:
                    st.error("Failed to upload resume")
                    st.stop()
            data = {
                "job_description": job_description,
                 "candidate_ids": candidate_ids
                     }
            try:
                response = requests.post(
                    f"{BACKEND_URL}/process/rank_resumes",
                    #files=files,
                    json=data
                )
                #    response_save = requests.post(f"{BACKEND_URL}/candidate/upload_resume",
            #        files=files,
            #        data=data)
                

                if response.status_code != 200:
                    st.error("Backend error")
                    st.stop()
                else:
                    result = response.json()   
            except Exception as e:
               st.error(f"API error: {e}")
               st.stop()
            st.session_state["analysis_result"] = result
            analysis = result["analysis"]
            if "analysis_result" in st.session_state:
                result = st.session_state["analysis_result"]
                st.subheader("🏆 Top Candidates")
                #print(st.write(result["top_candidates"]))
             #   for idx, candidate in enumerate(result["top_candidates"]):
                for idx, candidate in enumerate(analysis["candidates"]):
                #    name = candidate.get("name", f"Candidate {idx+1}")
             #       name = candidate.get("resume_name", "candidate")
                     name = candidate['name']
             #       score = candidate.get("score", 0)
                     score = candidate["match_score"]

                     st.write(f"{name} - Score: {round(score,2)}")    
                #  resume, score = candidate

                #    st.write(
                #        f"Candidate {idx+1} - Score: {round(score,2)}"
                #    )

                st.subheader("🧠 AI Resume Analysis")

                #st.write(result["analysis"])
                
                for candidate in analysis["candidates"]:
                    st.markdown(f"### {candidate['name']}")
                    st.write("Match Score:", candidate["match_score"])
                    st.progress(candidate["match_score"] / 100)
                    st.markdown("✅ Strengths")
                    for s in candidate["strengths"]:
                        st.write(f"- {s}")
                    
                    st.markdown("⚠ Weaknesses")
                    for w in candidate["weaknesses"]:
                        st.write(f"-{w}")
                st.subheader("📊 Summary")
             #   st.write(analysis["summary"])
                st.markdown(
                    f"""
                    <div style="background-color:#f0f2f6; padding:15px; border-radius:10px;">
                        <b>Summary:</b><br>{analysis["summary"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.session_state["answers"] = []
    #candidate_name = st.text_input("Candidate Name")

 #   if st.button("Generate Interview Questions"):
     #   if not candidate_name:
     #      st.warning("Please provide Candidate Name")
     #      st.stop()
        
        data = {
                 "job_description": job_description
                }
        try:
            response = requests.post(
                f"{BACKEND_URL}/process/ask_questions",
                json=data
            )
            if response.status_code != 200:
                st.error("Backend error")
                st.stop()
            else:
                questions = response.json()["questions"]

                st.session_state["questions"] = questions
                st.session_state["job_description"] = job_description  
        except Exception as e:
         st.error(f"API error: {e}")
         st.stop()
    if "questions" in st.session_state:
        import re
        st.subheader("Interview Questions")
     #   print(st.session_state["questions"])
        answers = []
        clean_questions = []
        for q in st.session_state["questions"]:
            q = q.strip()

        # keep only lines starting with number
            if re.match(r"^\d+\.", q):
               clean_questions.append(q)
        clean_questions = list(dict.fromkeys(clean_questions))
     #   for i, q in enumerate(st.session_state["questions"]):
        for i, q in enumerate(clean_questions):
            q = re.sub(r"^\d+\.\s*", "", q)   
        #    print(q) 
            st.write(f"**Q{i+1}. {q}**")
        #    print(st.write(f"**Q{i+1}. {q}**"))
        #    ans = st.text_area(
        #        f"Answer {i+1}",
        #        key=f"ans{i}"
        #    )
            ans = st.text_area("your answer", key=f"answer_{i}", value="")
            answers.append(ans)

        if st.button("Submit Answers"):
            if any(ans.strip() == "" for ans in answers):
                st.warning("Please answer all questions before submitting.")
                st.stop()    
            payload = {
             #   "candidate_name": candidate_name,
                "questions": st.session_state["questions"],    
                "answers": answers,
                "job_description": st.session_state["job_description"]
            }
            try:
                response = requests.post(
                    f"{BACKEND_URL}/interview/submit_answers",
                    json=payload
                )
                if response.status_code != 200:
                    st.error("Backend error")
                    st.stop()
                else:
                    result = response.json()    
            except Exception as e:
                st.error(f"API error: {e}")
                st.stop()        
                
            st.session_state["evaluation"] = result["evaluation"]

            st.session_state["skill_gap"] = result["skill_gap"] 

            st.session_state["training_plan"] = result["training_plan"] 

            st.subheader("📊 Evaluation of Candidate")
            evaluation = st.session_state["evaluation"]
            # Overall Score
            st.metric("Overall Score", evaluation["overall_score"])

            st.write("### Question Scores")

            for s in evaluation["scores"]:
                st.write(f"**Question {s['question']}** : {s['score']} / 5")

            st.write("### Feedback")
            st.info(evaluation["feedback"])

         #   st.write(result["evaluation"])
            
            st.subheader("🧠 Skill Gap Analysis")
            skill_gap = st.session_state["skill_gap"]

            col1, col2 = st.columns(2)

            with col1:
                st.write("### Missing Skills")
                for skill in skill_gap["missing_skills"]:
                    st.markdown(f"- {skill}")

            with col2:
                st.write("### Improvement Areas")
                for area in skill_gap["improvement_areas"]:
                    st.markdown(f"- {area}")

            st.write("### Recommended Training")

            for course in skill_gap["recommended_training"]:
                st.markdown(f"📘 {course}")
         #   st.write(result["skill_gap"])

            st.subheader("🎓 Personalized Training Plan")
         #   st.write(result["training_plan"])
            training = st.session_state["training_plan"]

            st.success(training["summary"])

            st.write(f"⏳ **Total Estimated Time:** {training['overall_estimated_time_weeks']} weeks")

            for skill in training["training_plan"]:

                with st.expander(f"📚 {skill['skill']} ({skill['priority']} Priority)"):

                    st.write("### Learning Resources")

                    for res in skill["learning_resources"]:
                        st.markdown(f"""
                            **{res['type']}**  
                            📖 {res['title']}  
                            {res['description']}
                            """)

                    st.write("### Practice Tasks")

                    for task in skill["practice_tasks"]:
                       st.markdown(f"- {task}")

                    st.write(f"⏱ Estimated Time: **{skill['estimated_time_weeks']} weeks**")