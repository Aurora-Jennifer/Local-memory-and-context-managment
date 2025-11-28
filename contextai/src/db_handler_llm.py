from pathlib import Path
import sqlite3

EXPECTED_LOGS_SCHEMA = {
    "timestamp": "TEXT",
    "project": "TEXT",
    "prompt": "TEXT",
    "response": "TEXT",
    "model": "TEXT",
    "tags": "TEXT",
    "source_file": "TEXT",
    "category": "TEXT",
    "conversation_id": "TEXT",
    "context": "TEXT",
    "quality_raw": "REAL",
    "entry_distance": "INTEGER",
    "quality_decay_rate": "REAL",
    "effective_score": "REAL"
}

def get_project_db_path(project_name: str) -> Path:
    """
    Construct the path to the project's SQLite DB.
    Creates the directory if it doesn't exist.
    """
    base_context_dir = Path.home() / ".contextai" / "contextdb"
    project_dir = base_context_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir / f"{project_name}.db"

def ranking_db_path(project_name: str) -> Path:
    """
    Returns the path to the scoring database
    """
    base_context_dir = Path.home() / ".contextai" / "rankingdb"
    project_dir = base_context_dir / project_name
    project_dir.mkdir(parents=True, exists_ok=True)
    return project_dir / f"{project_name}_ranking.db"

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
        confirmed_good INTEGER DEFAULT 0,
        category TEXT DEFAULT "misc"
    )
    """)
    conn.commit()

def validate_or_patch_schema(conn, expected_schema):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(logs)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    for column, col_type in expected_schema.items():
        if column not in existing_columns:
            print(f"Adding missing column: {column} ({col_type})...")
            default = "DEFAULT NULL"
            if "TEXT" in col_type:
                default = "DEFAULT 'misc'"
            if "INTEGER" in col_type:
                default = "DEFAULT 0"
            if "REAL" in col_type:
                default = "DEFAULT 0.0"
            cursor.execute(f"ALTER TABLE logs ADD COLUMN {column} {col_type} {default}")
    conn.commit()

# Example use
if __name__ == "__main__":
    project_name = "trading"
    db_path = get_project_db_path(project_name)
    conn = sqlite3.connect(db_path)
    ensure_logs_schema(conn)
    conn.close()
