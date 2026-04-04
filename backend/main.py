from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db, create_postgres_db_if_not_exists


from backend.routers.candidate_routes import router as candidate_router
from backend.routers.interview_routes import router as interview_router
from backend.routers.recruiter_routes import router as recruiter_router
from backend.routers.analytics_routes import router as analytics_router
from backend.routers.process_routes import router as process_router

app = FastAPI(title="AI Recruiter system")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidate_router)
app.include_router(interview_router)
app.include_router(recruiter_router)
app.include_router(analytics_router)
app.include_router(process_router)

@app.get("/")
def root():
    return {"message": "AI Recruiter system is running"}

@app.on_event("startup")
def startup():
    try:
        create_postgres_db_if_not_exists()
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print("❌ DB Error:", e)

@app.get("/health")
def health():
    return {"status": "healthy"}