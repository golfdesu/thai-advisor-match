import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    print("Fixing misspelled university names...")
    conn.execute(text("""
        UPDATE courses
        SET university = 'King Mongkut''s University of Technology Thonburi'
        WHERE university = 'King Mongkut me University of Technology Thonburi'
    """))
    conn.execute(text("""
        UPDATE courses
        SET university = 'King Mongkut''s University of Technology North Bangkok'
        WHERE university = 'King Mongkut me''s University of Technology North Bangkok'
           OR university LIKE 'King Mongkut me%'
    """))
    conn.commit()
    print("Fixed.")
