import psycopg2
import json

conn = psycopg2.connect('host=192.168.1.40 port=5432 dbname=police_training2 user=postgres password=123456')
cur = conn.cursor()
cur.execute("""
    SELECT g.group_key, c.config_key, c.config_value 
    FROM configs c 
    JOIN config_groups g ON c.group_id = g.id 
    WHERE g.group_key = 'ai'
""")
rows = cur.fetchall()
for r in rows:
    val = r[2]
    if val and len(str(val)) > 100:
        val = str(val)[:100] + "..."
    print(f"{r[0]}.{r[1]} = {val}")
conn.close()
