import sqlite3
from datetime import datetime
from pathlib import Path

GLOBAL_RANK_PATH = Path.home() / ".contextai" / "rankingdb" / "global_rankings.db"

def ensure_ranking_schema(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id INTEGER,
            timestamp TEXT,
            quality_raw REAL,
            decay_rate REAL,
            entry_distance INTEGER,
            effective_score REAL,
            confirmed_good INTEGER DEFAULT 0,
            scoring_method TEXT DEFAULT 'default',
            FOREIGN KEY (log_id) REFERENCES logs(id)
        )
    """)
    conn.commit()

def score_log(log_id, quality_raw, entry_distance, decay_rate, confirmed_good=False):
    effective_score = quality_raw * (1 - decay_rate)**entry_distance
    return {
        "log_id": log_id,
        "timestamp": datetime.now().isoformat(),
        "quality_raw": quality_raw,
        "decay_rate": decay_rate,
        "entry_distance": entry_distance,
        "effective_score": effective_score,
        "confirmed_good": int(confirmed_good),
        "scoring_method": "default"
    }

def insert_score(conn, score_dict):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO log_scores (
            log_id, timestamp, quality_raw, decay_rate,
            entry_distance, effective_score, confirmed_good, scoring_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        score_dict["log_id"],
        score_dict["timestamp"],
        score_dict["quality_raw"],
        score_dict["decay_rate"],
        score_dict["entry_distance"],
        score_dict["effective_score"],
        score_dict["confirmed_good"],
        score_dict["scoring_method"]
    ))
    conn.commit()

def get_ranking_db_path(project: str) -> Path:
    """
    Returns the path to the ranking database for the specified project.
    """
    ranking_dir = Path.home() / ".contextai" / "rankingdb"
    ranking_dir.mkdir(parents=True, exist_ok=True)
    return ranking_dir / f"{project}_ranking.db"

def ensure_ranking_schema(conn: sqlite3.Connection):
    """
    Creates the ranking table schema if it doesn't exist.
    """
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_id INTEGER,
        score REAL,
        last_updated TEXT
    )
    """)
    conn.commit()

def insert_or_update_score(conn: sqlite3.Connection, log_id: int, score: float):
    """
    Inserts or updates the ranking score for a given log entry.
    """
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    # Check if entry already exists
    cursor.execute("SELECT id FROM rankings WHERE log_id = ?", (log_id,))
    row = cursor.fetchone()

    if row:
        cursor.execute("UPDATE rankings SET score = ?, last_updated = ? WHERE log_id = ?", (score, now, log_id))
    else:
        cursor.execute("INSERT INTO rankings (log_id, score, last_updated) VALUES (?, ?, ?)", (log_id, score, now))

    conn.commit()

def get_top_ranked_entries(conn: sqlite3.Connection, limit: int = 5):
    """
    Retrieves top-ranked entries sorted by score.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rankings ORDER BY score DESC LIMIT ?", (limit,))
    return cursor.fetchall()

def update_global_rank(project: str, log_id: int, prompt: str, score: float, confirmed: bool = False, tags: str = None):
    conn = sqlite3.connect(GLOBAL_RANK_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO global_rankings (project, log_id, prompt, score, confirmed_good, timestamp, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        project, log_id, prompt, score, int(confirmed),
        datetime.now().isoformat(), tags or ""
    ))
    conn.commit()
    conn.close()
