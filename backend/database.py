import psycopg2,os
from psycopg2.extras import RealDictCursor
from sqlalchemy_utils import database_exists
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
load_dotenv()

candidates = []
#DB_CONFIG = {
#    "dbname": "recruiter",
 #   "user": "admin",
 #   "password": "admin",
 #   "host": "localhost",
 #   "port": "5432"
#}
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}
#conn = psycopg2.connect(
#    dbname="recruiter",
#    user="postgres",
#    password="admin",
##    host="localhost",
#    port= "5432"
#)
#DB_USER = os.getenv("DB_USER")
#DB_PASSWORD = os.getenv("DB_PASSWORD")
#DB_HOST = os.getenv("DB_HOST")
#DB_PORT = os.getenv("DB_PORT")
#DB_NAME = os.getenv("DB_NAME")

#DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_postgres_db_if_not_exists():
    if os.getenv("ENV") == "local":
        """Create PostgreSQL DB if it does not exist."""
        if not database_exists(DATABASE_URL):
            print(f"Database '{DB_CONFIG['dbname']}' does not exist. Creating...")
            
            conn = psycopg2.connect(
                dbname="postgres",
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"]
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute(f'CREATE DATABASE  "{DB_CONFIG["dbname"]}"')
            cur.close()
            conn.close()
            print(f"Database '{DB_CONFIG['dbname']}' created successfully!")
        else:
            print(f"Database '{DB_CONFIG['dbname']}' already exists.")

def init_db():

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidates(
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT,
        resume_text TEXT,
        interview_status TEXT,
        file_name TEXT,
        recommended BOOLEAN,
        embedding VECTOR(1536),        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
        # add columns safely
    cur.execute("""
    ALTER TABLE candidates
    ADD COLUMN IF NOT EXISTS file_name TEXT
    """)
    cur.execute("""
    ALTER TABLE candidates
    ADD COLUMN IF NOT EXISTS score FLOAT DEFAULT 0
    """)            
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_candidates_embedding
    ON candidates
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100)
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS resumes(
        id SERIAL PRIMARY KEY,
        candidate_id INT REFERENCES candidates(id),
        resume_text TEXT,
        file_path TEXT,
        embedding vector(1536),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs(
        id SERIAL PRIMARY KEY,
        title TEXT,
        description TEXT,
        embedding vector(1536),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS interviews(
        id SERIAL PRIMARY KEY,
        candidate_id INT REFERENCES candidates(id),
        job_id INT REFERENCES jobs(id),
        status TEXT,
        score FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id SERIAL PRIMARY KEY,
        interview_id INT REFERENCES interviews(id),
        question TEXT,
        expected_answer TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS answers(
        id SERIAL PRIMARY KEY,
        question_id INT REFERENCES questions(id),
        candidate_answer TEXT,
        score FLOAT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS skill_gaps(
        id SERIAL PRIMARY KEY,
        candidate_id INT,
        job_id INT,
        missing_skills TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS training_plans(
        id SERIAL PRIMARY KEY,
        candidate_id INT,
        plan_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

#def save_candidate(candidate_data, embedding):

#    cur = conn.cursor()

#    cur.execute(
#        """
#        INSERT INTO candidates (name, resume_text, embedding)
#        VALUES (%s, %s, %s)
#        RETURNING id
#        """,
#        (
#            candidate_data["name"],
#            candidate_data["resume"],
#            embedding
#        )
#    )

#    candidate_id = cur.fetchone()[0]

#    conn.commit()

#    return candidate_id


# -----------------------------
# CANDIDATE FUNCTIONS
# -----------------------------

def save_candidate(resume_text, embedding, file_name,name,email,phone):
    query = """
    INSERT INTO candidates (resume_text, embedding, file_name,name,email,phone)
    VALUES (%s, %s, %s,%s, %s, %s)
    RETURNING id
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query, (resume_text, embedding, file_name,name,email,phone))

    cid = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return cid

def update_candidate_score(candidate_id, score):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE candidates
        SET score = %s
        WHERE id = %s
        """,
        (score, candidate_id)
    )

    conn.commit()
    cur.close()
    conn.close()

def get_one_candidate(candidate_id):

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM candidates WHERE id=%s",
        (candidate_id,)
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    return result

def get_multiple_candidates(candidate_ids):
    results = []
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
 #   for cid in candidate_ids:
    cur.execute(
            "SELECT id,file_name,resume_text FROM candidates WHERE id = ANY(%s)",
            (candidate_ids,)
        )

    rows = cur.fetchall()

    resumes = []

    for row in rows:
        resumes.append({
            "candidate_id": row["id"],
            "filename":row["file_name"],
            "text":row["resume_text"]})   # adjust column name if needed

    cur.close()
    conn.close()

    return resumes

# -----------------------------
# RESUME STORAGE
# -----------------------------

def save_resume(candidate_id, resume_text, embedding, file_path=None):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO resumes (candidate_id,resume_text,embedding,file_path)
        VALUES (%s,%s,%s,%s)
        RETURNING id
        """,
        (candidate_id, resume_text, embedding, file_path)
    )

    rid = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return rid


def get_resume(resume_id):

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT * FROM resumes WHERE id=%s",
        (resume_id,)
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    return result


# -----------------------------
# JOB STORAGE
# -----------------------------

def save_job(title, description, embedding):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO jobs (title,description,embedding)
        VALUES (%s,%s,%s)
        RETURNING id
        """,
        (title, description, embedding)
    )

    job_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return job_id


# -----------------------------
# VECTOR SEARCH
# -----------------------------

def search_resumes(job_embedding, top_k=5):

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT r.*, c.name, c.file_name
        FROM resumes r
        JOIN candidates c ON r.candidate_id = c.id
        ORDER BY r.embedding <-> %s
        LIMIT %s
        """,
        (job_embedding, top_k)
    )

    results = cur.fetchall()

    cur.close()
    conn.close()

    return results


# -----------------------------
# INTERVIEW STORAGE
# -----------------------------

def create_interview(candidate_id, job_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO interviews (candidate_id,job_id,status)
        VALUES (%s,%s,'pending')
        RETURNING id
        """,
        (candidate_id, job_id)
    )

    interview_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return interview_id


def save_question(interview_id, question, expected_answer):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO questions (interview_id,question,expected_answer)
        VALUES (%s,%s,%s)
        RETURNING id
        """,
        (interview_id, question, expected_answer)
    )

    qid = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return qid


def save_answer(question_id, answer):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO answers (question_id,candidate_answer)
        VALUES (%s,%s)
        """,
        (question_id, answer)
    )

    conn.commit()
    cur.close()
    conn.close()


# -----------------------------
# SKILL GAP
# -----------------------------

def save_skill_gap(candidate_id, job_id, missing_skills):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO skill_gaps(candidate_id,job_id,missing_skills)
        VALUES (%s,%s,%s)
        """,
        (candidate_id, job_id, missing_skills)
    )

    conn.commit()
    cur.close()
    conn.close()


# -----------------------------
# TRAINING PLAN
# -----------------------------

def save_training_plan(candidate_id, plan_text):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO training_plans(candidate_id,plan_text)
        VALUES (%s,%s)
        """,
        (candidate_id, plan_text)
    )

    conn.commit()
    cur.close()
    conn.close()

def get_total_candidates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM candidates")
    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return result

def get_top_candidates():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT name, score
        FROM candidates
        WHERE score IS NOT NULL
        ORDER BY score DESC
        LIMIT 5
    """)

    result = cur.fetchall()
    cur.close()
    conn.close()

    return result

def get_interviewed_candidates():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM candidates
        WHERE interview_status = 'completed'
    """)

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return result

def get_recommended_candidates():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM candidates
        WHERE recommended = TRUE
    """)

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return result

def get_recruitment_analytics():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total_candidates,
            COUNT(*) FILTER (WHERE recommended = TRUE) AS recommended_candidates,
            COUNT(*) FILTER (WHERE interview_status = 'scheduled') AS interview_scheduled,
            AVG(score) AS avg_ai_score
        FROM candidates
    """)

    stats = cur.fetchone()

    cur.execute("""
        SELECT name
        FROM candidates
        ORDER BY created_at DESC
        LIMIT 5
    """)

    latest = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "total_candidates": stats[0],
        "recommended_candidates": stats[1],
        "interview_scheduled": stats[2],
        "avg_ai_score": float(stats[3]) if stats[3] else 0,
        "latest_candidates": [row[0] for row in latest]
    }

def update_candidate_name_score(candidate_id, name, score):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE candidates
        SET name = %s, score = %s
        WHERE id = %s
        """,
        (name, score, candidate_id)
    )

    conn.commit()
    cur.close()
    conn.close()