import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="advisor_match", user="postgres", password="postgres"
)
cur = conn.cursor()

cur.execute("UPDATE faculties SET email = NULL WHERE email = ''")
print("Rows updated:", cur.rowcount)
conn.commit()

cur.execute("SELECT COUNT(*) FROM faculties WHERE email = ''")
print("Remaining empty-string emails:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM faculties WHERE email IS NULL")
print("Total NULL emails now:", cur.fetchone()[0])

conn.close()
print("Done.")
