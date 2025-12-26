from models.db import get_db_connection

try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("✅ Database connected successfully!")
    cur.close()
    conn.close()
except Exception as e:
    print("❌ Database connection failed")
    print(e)
