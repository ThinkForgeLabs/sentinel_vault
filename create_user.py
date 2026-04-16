
import bcrypt, psycopg2, uuid, datetime

pw = bcrypt.hashpw(b'Admin123!', bcrypt.gensalt()).decode()
uid = str(uuid.uuid4())
now = datetime.datetime.utcnow()

conn = psycopg2.connect('postgresql://sentinel:sentinel@localhost:5433/sentinel_vault')
cur = conn.cursor()
cur.execute(
    'INSERT INTO users (id, username, display_name, password_hash, role, is_active, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
    (uid, 'admin', 'Admin', pw, 'admin', True, now, now)
)
conn.commit()
cur.close()
conn.close()
print('User created!')
