import os
import sys
import sqlite3

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

DB_PATH = config.DB_PATH

def get_db_connection():
    """Create and return a database connection with foreign key support and WAL mode."""
    # Ensure parent folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def _col_exists(conn, table, col):
    """Return True if 'col' already exists in 'table'."""
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return any(r['name'] == col for r in rows)

def _run_migrations(conn):
    """Add any columns that exist in the schema but are missing from the live DB."""
    migrations = [
        # (table, column_name, column_definition)
        ("visits", "approval_status", "TEXT DEFAULT 'pending'"),
        ("visits", "approved_by",     "INTEGER"),
        ("visits", "approved_at",     "TIMESTAMP"),
        ("visits", "qr_code_path",    "TEXT"),
        ("visits", "host_notified",   "INTEGER DEFAULT 0"),
        ("users",  "session_token",   "TEXT"),
    ]
    for table, col, definition in migrations:
        if not _col_exists(conn, table, col):
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition};")
                print(f"[DBManager] Migration: added {table}.{col}")
            except Exception as e:
                print(f"[DBManager] Migration warning for {table}.{col}: {e}")

    # Ensure all existing visits have approval_status set
    conn.execute("""
        UPDATE visits SET approval_status = 'pending'
        WHERE approval_status IS NULL;
    """)
    conn.commit()

def initialize_database():
    """Create all tables and seed default data if database is empty."""
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Resolve paths for schema.sql and seed_data.sql
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, "schema.sql")
    seed_path = os.path.join(base_dir, "seed_data.sql")

    # 1. Run Schema Creation
    if os.path.exists(schema_path):
        print(f"[DBManager] Loading database schema from {schema_path}...")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        conn.commit()
    else:
        print("[DBManager] Error: schema.sql file not found.")

    # 2. Run column migrations (safe to run every startup)
    _run_migrations(conn)

    # 3. Check if we need to seed
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        if os.path.exists(seed_path):
            print(f"[DBManager] Seeding default records from {seed_path}...")
            with open(seed_path, "r", encoding="utf-8") as f:
                seed_sql = f.read()
            cursor.executescript(seed_sql)
            conn.commit()
            print("[DBManager] Seeding completed.")
        else:
            print("[DBManager] Error: seed_data.sql file not found.")
    else:
        print("[DBManager] Database already seeded. Skipping.")

    conn.close()

if __name__ == "__main__":
    initialize_database()
