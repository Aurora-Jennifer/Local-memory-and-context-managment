import sqlite3
from db_handler_llm import ranking_db_path  

def ensure_logs_schema(conn: sqlite3.Connection):
    """
    Create the logs table schema if it doesn't exist.
    Includes quality scoring and metadata fields.
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        model TEXT,
        project TEXT,
        prompt TEXT,
        response TEXT,
        tags TEXT,
        source_file TEXT,
        conversation_id TEXT,
        context TEXT,
        quality_raw REAL DEFAULT NULL,
        entry_distance INTEGER DEFAULT NULL,
        quality_decay_rate REAL DEFAULT NULL,
        effective_score REAL DEFAULT NULL,
        confirmed_good INTEGER DEFAULT 0
    )
    """)
    conn.commit()

def run_score_reinforcement(project: str):
    db_path = ranking_db_path(project)
    conn = sqlite3.connect(db_path)
    ensure_logs_schema(conn)  # Ensure the logs table exists
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, quality_raw, entry_distance, quality_decay_rate, confirmed_good
        FROM logs
        WHERE quality_raw IS NOT NULL
    """)
    rows = cursor.fetchall()

    updated_rows = []

    for row in rows:
        log_id, quality_raw, entry_distance, decay_rate, confirmed_good = row
        decay_rate = decay_rate if decay_rate is not None else 0.05
        entry_distance = entry_distance if entry_distance is not None else 0

        effective_score = quality_raw * ((1 - decay_rate) ** entry_distance)

        if confirmed_good:
            effective_score += 0.1
            effective_score = min(effective_score, 1.0)

        updated_rows.append((effective_score, log_id))

    cursor.executemany("UPDATE logs SET effective_score = ? WHERE id = ?", updated_rows)
    conn.commit()
    conn.close()
    return f"✅ Reinforcement scores updated for {len(updated_rows)} entries in '{project}'"

# Retry
run_score_reinforcement("trading")
