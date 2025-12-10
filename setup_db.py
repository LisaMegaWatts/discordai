import os
import psycopg2

def run_migration(sql_path):
    db_url = os.getenv("DATABASE_URL", "postgresql://ai_ide_user:ai_ide_password@localhost:5432/ai_ide_db")
    import re
    m = re.match(r"postgresql(\+asyncpg)?://([^:]+):([^@]+)@([^:/]+):(\d+)/([^?]+)", db_url)
    if not m:
        raise ValueError("DATABASE_URL format invalid for psycopg2")
    user, password, host, port, dbname = m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)
    conn = psycopg2.connect(user=user, password=password, host=host, port=port, dbname=dbname)
    with conn, conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS document_blobs CASCADE;")
        with open(sql_path, "r") as f:
            cur.execute(f.read())
    print(f"Migration {sql_path} applied successfully.")

if __name__ == "__main__":
    run_migration("migrations/003_add_document_blob.sql")