import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

print("Executing SQL window partition deduplication on courses...")
with engine.connect() as conn:
    # Check duplicates before
    res_before = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT title_th, degree_level, university, COUNT(*)
            FROM courses
            GROUP BY title_th, degree_level, university
            HAVING COUNT(*) > 1
        ) t
    """)).scalar()
    print(f"Duplicate groups before cleanup: {res_before}")

    # Delete duplicates keeping lowest ID
    del_res = conn.execute(text("""
        DELETE FROM courses
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY university, title_th, degree_level
                           ORDER BY id ASC
                       ) as rnum
                FROM courses
            ) t
            WHERE t.rnum > 1
        );
    """))
    conn.commit()
    print(f"Deleted duplicate records.")

    # Check duplicates after
    res_after = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT title_th, degree_level, university, COUNT(*)
            FROM courses
            GROUP BY title_th, degree_level, university
            HAVING COUNT(*) > 1
        ) t
    """)).scalar()
    print(f"Duplicate groups after cleanup: {res_after}")
