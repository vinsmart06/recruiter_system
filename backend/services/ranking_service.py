from backend.database import get_connection
from backend.services.embedding_service import create_resume_embedding
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def search_best_resumes(query_embedding):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT text,
        embedding <-> %s AS distance
        FROM resumes
        ORDER BY distance
        LIMIT 5
        """,
        (query_embedding,)
    )

    results = cur.fetchall()

    return results

def rank_resumes(job_description, resumes):

    jd_embedding = create_resume_embedding(job_description)

    scores = []

    for i, r in enumerate(resumes):

        r_embedding = create_resume_embedding(r["text"])

        similarity = cosine_similarity(
            [jd_embedding],
            [r_embedding]
        )[0][0]

#        scores.append({"name": "Candidate",
#                  "score": similarity,
#                  "resume":r""})
        scores.append({
          "name": r["filename"],
          "score": similarity,
          "resume":r["text"]
            })
    ranked = sorted(
        scores,
        key=lambda x: x["score"],
        reverse=True
    )

    return ranked[:5]


def store_resume(name, resume_text):

    embedding = create_resume_embedding(resume_text)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO candidates (name, resume_text, embedding)
        VALUES (%s, %s, %s)
    """, (name, resume_text, embedding))

    conn.commit()

    cur.close()
    conn.close()

#def semantic_candidate_search(job_description):

#    embedding = create_resume_embedding(job_description)

#    conn = get_connection()
#    cur = conn.cursor()

 #   cur.execute("""
#        SELECT name, resume_text
#        FROM candidates
#        ORDER BY embedding <-> %s
#        LIMIT 5
#    """, (embedding,))

#    results = cur.fetchall()

#    cur.close()
#    conn.close()

#    return results