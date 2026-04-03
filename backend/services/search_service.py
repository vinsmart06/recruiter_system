from backend.database import get_connection
from backend.services.embedding_service import create_resume_embedding


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