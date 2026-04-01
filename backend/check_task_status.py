import psycopg2
conn = psycopg2.connect('host=192.168.1.40 port=5432 dbname=police_training2 user=postgres password=123456')
cur = conn.cursor()
cur.execute("""
    SELECT id, task_name, task_type, status, created_at, started_at, completed_at, error_message,
           request_payload, result_payload
    FROM ai_tasks 
    ORDER BY created_at DESC 
    LIMIT 5
""")
rows = cur.fetchall()
for r in rows:
    print(f"\n{'='*60}")
    print(f"ID={r[0]} | name={r[1]} | type={r[2]} | status={r[3]}")
    print(f"created={r[4]} | started={r[5]} | completed={r[6]}")
    print(f"error={r[7]}")
    req = str(r[8])[:300] if r[8] else "None"
    res = str(r[9])[:300] if r[9] else "None"
    print(f"request_payload: {req}")
    print(f"result_payload: {res}")
conn.close()
