from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg://postgres:123456@192.168.1.40:5432/police_training2')
conn = engine.connect()

result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_points'"))
columns = [row[0] for row in result]
print('Current columns:', columns)

if 'course_id' not in columns:
    conn.execute(text("ALTER TABLE knowledge_points ADD COLUMN course_id INTEGER"))
    conn.commit()
    print('Added course_id column')
else:
    print('course_id already exists')

result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_points'"))
print('Updated columns:', [row[0] for row in result])
conn.close()