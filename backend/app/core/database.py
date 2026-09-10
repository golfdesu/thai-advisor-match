import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Ensure backend/.env is reliably loaded regardless of working directory
_backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
if _backend_env.exists():
    load_dotenv(dotenv_path=_backend_env)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///:memory:"

engine_kwargs = {
    "pool_pre_ping": not DATABASE_URL.startswith("sqlite"),
}
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 300,
        "pool_timeout": 15,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

# pgvector HNSW tuning (perf audit 2026-09-10, vector 0.8.6):
# - ef_search=400 was an old workaround for filtered ANN returning 0 rows on small
#   sets (e.g. university ILIKE + ORDER BY <=>). It is now COUNTERPRODUCTIVE:
#   EXPLAIN shows ef>=64 makes the planner abandon ix_faculties_embedding_hnsw for
#   Seq Scan+Sort (12.7ms -> 22-35ms) on unfiltered faculties search (5.7k rows);
#   ef=40 is the last value that keeps Index Scan (measured 40/64/80 on prod data).
# - 0.8's hnsw.iterative_scan fixes the original zero-row problem properly:
#   the scan keeps pulling graph candidates until the filter yields LIMIT rows,
#   so we can keep a small ef. Verified: SUT-filtered course query returns full
#   top-5 at ef=40 with iterative_scan on.
_HNSW_TUNE = "SET hnsw.ef_search = 40; SET hnsw.iterative_scan = strict_order"
try:
    from sqlalchemy import event as _sa_event, text as _sa_text

    @_sa_event.listens_for(engine, "connect")
    def _set_hnsw_ef_search(dbapi_conn, _rec):
        try:
            cur = dbapi_conn.cursor()
            cur.execute(_HNSW_TUNE)
            cur.close()
        except Exception:
            pass

    # Also enforce on each Session checkout (covers pooled connections that
    # already ran SET on first connect but may have been RESET by pool recycle).
    @_sa_event.listens_for(engine, "checkout")
    def _set_hnsw_on_checkout(dbapi_conn, _rec, _proxy):
        try:
            cur = dbapi_conn.cursor()
            cur.execute(_HNSW_TUNE)
            cur.close()
        except Exception:
            pass
except Exception:
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        # No per-request SET here: the connect/checkout listeners above already
        # pin the HNSW GUCs for every pooled connection, and `SET LOCAL` without
        # an explicit transaction was a verified no-op (perf audit 2026-09-10)
        # that still cost 2 round-trips per request.
        yield db
    finally:
        db.close()
