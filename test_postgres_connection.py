import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="ai_ide_db",
        user="ai_ide_user",
        password="ai_ide_password"
    )
    print("Connection succeeded")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")