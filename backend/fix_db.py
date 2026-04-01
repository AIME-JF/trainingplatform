from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg://postgres:123456@192.168.1.40:5432/police_training2')
conn = engine.connect()
conn.execute(text("UPDATE alembic_version SET version_num = '1a2b3c4d5e6f'"))
conn.commit()
result = conn.execute(text('SELECT version_num FROM alembic_version'))
print('Updated to:', result.fetchone()[0])
conn.close()