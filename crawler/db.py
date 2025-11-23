# FILE: crawler/db.py
import os
import logging
import psycopg2
from psycopg2.extras import execute_values
from crawler.config import DATABASE_URL

logger = logging.getLogger("DB")

def get_conn():
    """Return a new connection to the PostgreSQL database."""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """
    AUTO-MIGRATION:
    Reads sql/migrations.sql and creates tables if they don't exist.
    This ensures the code works on GitHub Actions (where DB is empty).
    """
    try:
        conn = get_conn()
        
        # Calculate path to sql/migrations.sql relative to this file
        # logical path: crawler/db.py -> go up one level -> sql/migrations.sql
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sql_path = os.path.join(base_dir, 'sql', 'migrations.sql')
        
        if not os.path.exists(sql_path):
            logger.error(f"❌ SQL file not found at: {sql_path}")
            return

        with open(sql_path, 'r') as f:
            schema_sql = f.read()
            
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        logger.info("✅ Database schema initialized successfully.")
        
    except Exception as e:
        logger.error(f"⚠️ Database initialization failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def insert_staging_batch(conn, rows):
    if not rows:
        return
    with conn.cursor() as cur:
        sql = """
        INSERT INTO repo_staging (repo_id, full_name, url, created_at, stars, source_slice)
        VALUES %s
        """
        execute_values(cur, sql, rows)
    conn.commit()

def upsert_from_staging(conn):
    with conn.cursor() as cur:
        # 1. Upsert Repositories
        cur.execute("""
        INSERT INTO repositories (id, full_name, created_at, updated_at)
        SELECT repo_id, full_name, created_at, now()
        FROM repo_staging
        ON CONFLICT (id) DO UPDATE
        SET full_name = EXCLUDED.full_name,
            updated_at = now();
        """)

        # 2. Upsert Stars
        cur.execute("""
        INSERT INTO repo_stars (repo_id, stars, updated_at)
        SELECT repo_id, stars, now()
        FROM repo_staging
        ON CONFLICT (repo_id) DO UPDATE
        SET stars = EXCLUDED.stars,
            updated_at = now();
        """)

        # 3. History Log
        cur.execute("""
        INSERT INTO repo_star_history (repo_id, stars, recorded_at)
        SELECT repo_id, stars, now()
        FROM repo_staging;
        """)

        # 4. Clean Staging
        cur.execute("TRUNCATE repo_staging;")
    
    conn.commit()