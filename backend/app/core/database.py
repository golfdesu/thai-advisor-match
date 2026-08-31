import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

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

# pgvector HNSW: filtered vector search (e.g. university ILIKE + ORDER BY <=> + LIMIT)
# returns zero rows with default ef_search when the filtered set is small (SUT 87 / 4162).
# Raise per-connection ef_search so every API query sees a tuned index scan.
try:
    from sqlalchemy import event as _sa_event, text as _sa_text

    @_sa_event.listens_for(engine, "connect")
    def _set_hnsw_ef_search(dbapi_conn, _rec):
        try:
            cur = dbapi_conn.cursor()
            cur.execute("SET hnsw.ef_search = 400")
            cur.close()
        except Exception:
            pass

    # Also enforce on each Session checkout (covers pooled connections that
    # already ran SET on first connect but may have been RESET by pool recycle).
    @_sa_event.listens_for(engine, "checkout")
    def _set_hnsw_on_checkout(dbapi_conn, _rec, _proxy):
        try:
            cur = dbapi_conn.cursor()
            cur.execute("SET hnsw.ef_search = 400")
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
        # Defense-in-depth: also SET per-request before any vector ORDER BY.
        try:
            from sqlalchemy import text as _t
            db.execute(_t("SET LOCAL hnsw.ef_search = 400"))
        except Exception:
            pass
        yield db
    finally:
        db.close()
