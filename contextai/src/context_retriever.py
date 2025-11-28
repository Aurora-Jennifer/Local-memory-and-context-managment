import sqlite3

def get_best_context(conn: sqlite3.Connection, project: str, tag: str = None, limit: int = 1):
    """
    Retrieve top N past responses for a given project, optionally filtered by tag.
    Orders by confirmed_good and effective_score.
    """
    cursor = conn.cursor()
    if tag:
        cursor.execute("""
            SELECT prompt, response, context FROM logs
            WHERE project = ? AND tags LIKE ?
            ORDER BY confirmed_good DESC, effective_score DESC
            LIMIT ?
        """, (project, f"%{tag}%", limit))
    else:
        cursor.execute("""
            SELECT prompt, response, context FROM logs
            WHERE project = ?
            ORDER BY confirmed_good DESC, effective_score DESC
            LIMIT ?
        """, (project, limit))

    return cursor.fetchall()
