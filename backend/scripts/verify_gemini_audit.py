import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, re
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import create_engine, text
env=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),encoding='utf-8').read()
db_url=env.split('DATABASE_URL=')[-1].split('\n')[0].strip().strip('"')
engine=create_engine(db_url, pool_pre_ping=True)
with engine.connect() as conn:
    rows=conn.execute(text("SELECT id FROM courses")).fetchall()
    uuid_pat=re.compile(r'_[0-9a-f]{6}$')
    uuid_count=sum(1 for r in rows if uuid_pat.search(r[0]))
    print(f"Total {len(rows)} UUID suffix {uuid_count} ({uuid_count/len(rows)*100:.1f}%)")
    nida_bach=conn.execute(text("SELECT count(*) FROM courses WHERE university='National Institute of Development Administration' AND degree_level='ปริญญาตรี'")).scalar()
    print(f"NIDA bachelor count {nida_bach}")
    nida_med=conn.execute(text("SELECT count(*) FROM courses WHERE university='National Institute of Development Administration' AND faculty_th LIKE '%แพทย%'")).scalar()
    print(f"NIDA medical faculty count {nida_med}")
    cmu_tqf=conn.execute(text("SELECT count(*) FROM courses WHERE id LIKE 'cmu_tqf_%'")).scalar()
    print(f"CMU TQF ids {cmu_tqf}")
    cmu_rows=conn.execute(text("SELECT id FROM courses WHERE university='Chiang Mai University'")).fetchall()
    cmu_uuid=len([r for r in cmu_rows if uuid_pat.search(r[0])])
    print(f"CMU UUID suffix {cmu_uuid} / {len(cmu_rows)} ({cmu_uuid/len(cmu_rows)*100:.1f}%)")
    # check other unis
    for uni in ['Mae Fah Luang University','Suranaree University of Technology']:
        rows2=conn.execute(text(f"SELECT id FROM courses WHERE university='{uni}'")).fetchall()
        cnt=len([r for r in rows2 if uuid_pat.search(r[0])])
        print(f"{uni[:20]} UUID {cnt}/{len(rows2)} ({cnt/len(rows2)*100:.1f}%)")
    import pathlib
    print("generate files:", list(pathlib.Path("scripts").glob("generate*.py")))
    print("agent files:", list(pathlib.Path("scripts").glob("agent*.py")))
    print("scrape files:", list(pathlib.Path("scripts").glob("scrape*.py")))
    print("courses_new count:", len(list(pathlib.Path("data/courses_new").glob("*.json"))) if pathlib.Path("data/courses_new").exists() else 0)
