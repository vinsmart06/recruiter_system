from backend.database import get_connection
from backend.services.embedding_service import create_resume_embedding
#from backend.database import conn
from backend.database import get_total_candidates

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import faiss, pickle
#conn = get_connection()
def store_resume(resume_text, embedding):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO resumes(text, embedding)
        VALUES (%s, %s)
        """,
        (resume_text, embedding)
    )

    conn.commit()

def semantic_candidate_search(query, limit=5):

    conn = get_connection()
    cur = conn.cursor()

    query_embedding = create_resume_embedding(query)
    # convert list to string for pgvector
    query_embedding = str(query_embedding)
    sql = """
        SELECT
            id,
        name,
        email,
        resume_text,
        file_name,
        embedding <-> %s::vector AS distance
        FROM candidates
        ORDER BY embedding <-> %s::vector
        LIMIT %s
        """

    
    cur.execute(sql, (query_embedding, query_embedding, limit))

    results = cur.fetchall()

    cur.close()
    conn.close()

    candidates = []

    for row in results:
        candidates.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "resume_text": row[3][:300],  # preview
            "file_name": row[4],
            "similarity_score": row[5]
        })

    return candidates

def semantic_search(query):

    query_embedding = create_resume_embedding(query)

    candidates = get_total_candidates()

    scores = []

    for c in candidates:

        similarity = cosine_similarity(
            [query_embedding],
            [c["embedding"]]
        )[0][0]

        scores.append((c, similarity))

    ranked = sorted(scores, key=lambda x: x[1], reverse=True)

    return ranked[:5]

class ResumeRAG:

    def __init__(self):

        self.index = None
        self.resumes = []

    def build_index(self, resumes):

        self.resumes = resumes

        embeddings = [create_resume_embedding(r) for r in resumes]

        dim = len(embeddings[0])

        self.index = faiss.IndexFlatL2(dim)

        self.index.add(np.array(embeddings).astype("float32"))

    def search(self, query, k=3):

        query_embedding = np.array([create_resume_embedding(query)]).astype("float32")

        distances, indices = self.index.search(query_embedding, k)

        results = [self.resumes[i] for i in indices[0]]

        return results

    def save(self):

        faiss.write_index(self.index, "resume_index.faiss")

        with open("resume_data.pkl", "wb") as f:
            pickle.dump(self.resumes, f)

    def load(self):

        self.index = faiss.read_index("resume_index.faiss")

        with open("resume_data.pkl", "rb") as f:
            self.resumes = pickle.load(f)