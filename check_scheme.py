import psycopg2
conn = psycopg2.connect('postgresql://sentinel:sentinel@localhost:5433/sentinel_vault')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
for row in cur.fetchall():
    print(row)
conn.close()