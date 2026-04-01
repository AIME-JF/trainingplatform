import psycopg2, json
conn = psycopg2.connect('host=192.168.1.40 port=5432 dbname=police_training2 user=postgres password=123456')
cur = conn.cursor()
cur.execute("""
    SELECT request_payload 
    FROM ai_tasks 
    WHERE id = 32
""")
row = cur.fetchone()
if row and row[0]:
    payload = json.loads(row[0]) if isinstance(row[0], str) else row[0]
    print(json.dumps(payload, indent=2, ensure_ascii=False))
conn.close()
