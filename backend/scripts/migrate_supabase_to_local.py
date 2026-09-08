"""
Supabase -> Local PostgreSQL (Docker) One-Time Data Migration Script
Transfers existing production data from Supabase to Local Docker Postgres in batches.
Once migrated, all crawl/ingestion and vector queries run 100% locally with ZERO Supabase egress.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Ensure backend root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Load .env
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

DEFAULT_LOCAL_URL = "postgresql://postgres:postgres@localhost:5432/advisor_match"
DEFAULT_SUPABASE_URL = os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL")

TABLES_CONFIG = [
    {
        "name": "quiz_questions",
        "primary_key": "id",
        "columns": ["id", "category", "question", "choices", "answer", "explanation", "level"],
        "json_cols": {"choices"},
        "vector_cols": set(),
    },
    {
        "name": "quiz_attempts",
        "primary_key": "id",
        "columns": ["id", "category", "score", "total", "answers", "created_at"],
        "json_cols": {"answers"},
        "vector_cols": set(),
    },
    {
        "name": "research_labs",
        "primary_key": "id",
        "columns": [
            "id", "name_th", "name_en", "university", "university_th",
            "faculty", "faculty_th", "department", "department_th",
            "lead_advisor_id", "member_faculty_ids", "description",
            "research_domains", "flagship_equipment", "industry_partners",
            "open_positions", "website_url", "image_url", "embedding_text", "embedding"
        ],
        "json_cols": {"member_faculty_ids", "research_domains", "flagship_equipment", "industry_partners", "open_positions"},
        "vector_cols": {"embedding"},
    },
    {
        "name": "courses",
        "primary_key": "id",
        "columns": [
            "id", "title_th", "title_en", "degree_level", "degree_name",
            "university", "university_th", "faculty", "faculty_th",
            "department", "department_th", "program_type", "duration_years",
            "total_credits", "tuition_per_semester", "tuition_total",
            "description", "curriculum_highlights", "career_paths", "tags",
            "website_url", "embedding_text", "embedding"
        ],
        "json_cols": {"curriculum_highlights", "career_paths", "tags"},
        "vector_cols": {"embedding"},
    },
    {
        "name": "faculties",
        "primary_key": "id",
        "columns": [
            "id", "university", "university_th", "faculty", "faculty_th",
            "department", "department_th", "academic_title_th", "first_name",
            "last_name", "full_name_th", "role", "email", "image_url",
            "profile_url", "education", "research_interests", "taught_courses",
            "featured_publications", "scholar_url", "embedding_text", "embedding",
            "total_publications_count", "first_author_count", "co_author_count",
            "total_citations", "h_index", "openalex_id"
        ],
        "json_cols": {"education", "research_interests", "taught_courses", "featured_publications"},
        "vector_cols": {"embedding"},
    },
    {
        "name": "semantic_cache",
        "primary_key": "id",
        "columns": [
            "id", "cache_type", "query_text", "cache_payload", "hit_count",
            "embedding", "created_at", "updated_at"
        ],
        "json_cols": {"cache_payload"},
        "vector_cols": {"embedding"},
    },
]

def migrate_table(src_engine, dst_engine, config, batch_size=500, truncate=False):
    table_name = config["name"]
    pk = config["primary_key"]
    columns = config["columns"]
    json_cols = config["json_cols"]
    vector_cols = config["vector_cols"]

    print(f"\n========================================================")
    print(f"📦 Migrating Table: '{table_name}'")
    print(f"========================================================")

    # 1. Check counts
    with src_engine.connect() as s_conn, dst_engine.connect() as d_conn:
        src_count = s_conn.execute(text(f"SELECT count(*) FROM {table_name}")).scalar()
        dst_count = d_conn.execute(text(f"SELECT count(*) FROM {table_name}")).scalar()
        print(f"  Source (Supabase): {src_count:,} rows")
        print(f"  Target (Local DB): {dst_count:,} rows")

        if src_count == 0:
            print("  ℹ️ Source is empty, skipping.")
            return

        if truncate and dst_count > 0:
            print(f"  ⚠️ Truncating target table '{table_name}'...")
            d_conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE;"))
            d_conn.commit()
            dst_count = 0

        if dst_count >= src_count and not truncate:
            print(f"  ✅ Target already contains {dst_count:,} rows. Skipping table (use --truncate to overwrite).")
            return

    # 2. Select column list formatted for SQL read
    # Format vector cols as ::text so psycopg2 receives a clean string '[0.1, 0.2, ...]'
    read_cols = []
    for col in columns:
        if col in vector_cols:
            read_cols.append(f"{col}::text AS {col}")
        else:
            read_cols.append(col)
    read_query = f"SELECT {', '.join(read_cols)} FROM {table_name} ORDER BY {pk}"

    # Build INSERT query with ON CONFLICT DO UPDATE
    col_names = ", ".join(columns)
    val_placeholders = ", ".join([f":{c}" for c in columns])
    update_assignments = ", ".join([f"{c} = EXCLUDED.{c}" for c in columns if c != pk])

    if update_assignments:
        insert_sql = text(f"""
            INSERT INTO {table_name} ({col_names})
            VALUES ({val_placeholders})
            ON CONFLICT ({pk}) DO UPDATE SET {update_assignments}
        """)
    else:
        insert_sql = text(f"""
            INSERT INTO {table_name} ({col_names})
            VALUES ({val_placeholders})
            ON CONFLICT ({pk}) DO NOTHING
        """)

    # 3. Stream in batches from source and write to destination
    start_time = time.time()
    total_migrated = 0

    with src_engine.connect().execution_options(stream_results=True) as s_conn:
        result = s_conn.execute(text(read_query))

        while True:
            rows = result.fetchmany(batch_size)
            if not rows:
                break

            # Prepare batch dicts
            batch_data = []
            for r in rows:
                row_dict = dict(r._mapping)
                # Serialize json fields if needed
                for jc in json_cols:
                    val = row_dict.get(jc)
                    if val is not None and not isinstance(val, str):
                        row_dict[jc] = json.dumps(val, ensure_ascii=False)
                # Vector field formatting
                for vc in vector_cols:
                    vval = row_dict.get(vc)
                    if vval is not None and isinstance(vval, str) and not vval.startswith('['):
                        row_dict[vc] = f"[{vval}]"
                batch_data.append(row_dict)

            # Insert into target
            with dst_engine.connect() as d_conn:
                d_conn.execute(insert_sql, batch_data)
                d_conn.commit()

            total_migrated += len(batch_data)
            pct = (total_migrated / src_count) * 100
            print(f"  ↳ Migrated {total_migrated:,} / {src_count:,} rows ({pct:.1f}%)")

    elapsed = time.time() - start_time
    print(f"  🎉 Finished '{table_name}': {total_migrated:,} rows in {elapsed:.2f}s ({total_migrated/max(elapsed, 0.01):.1f} rows/s)")


def main():
    parser = argparse.ArgumentParser(description="Migrate data from Supabase to Local Docker PostgreSQL")
    parser.add_argument("--source", type=str, default=DEFAULT_SUPABASE_URL, help="Source Supabase Database URL")
    parser.add_argument("--target", type=str, default=DEFAULT_LOCAL_URL, help="Target Local Postgres Database URL")
    parser.add_argument("--table", type=str, default=None, help="Migrate specific table only (e.g. faculties)")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for transfer")
    parser.add_argument("--truncate", action="store_true", help="Truncate target tables before inserting")
    args = parser.parse_args()

    print("\n========================================================")
    print("🚀 Thai EduCenter Database Migration: Supabase -> Local")
    print("========================================================")
    print(f"Source URL : {args.source[:35]}...{args.source[-15:] if args.source else ''}")
    print(f"Target URL : {args.target}")
    print(f"Batch Size : {args.batch_size}")
    print(f"Truncate   : {args.truncate}")
    print("========================================================\n")

    if not args.source:
        print("❌ Error: Source database URL is not provided and DATABASE_URL is not set in backend/.env")
        sys.exit(1)

    try:
        src_engine = create_engine(args.source, pool_pre_ping=True)
        with src_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print("✅ Successfully connected to Source (Supabase)")
    except Exception as e:
        print(f"❌ Failed to connect to Source (Supabase): {e}")
        sys.exit(1)

    try:
        dst_engine = create_engine(args.target, pool_pre_ping=True)
        with dst_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print("✅ Successfully connected to Target (Local Docker DB)")
    except Exception as e:
        print(f"❌ Failed to connect to Target (Local DB): {e}")
        print("👉 Did you start Docker container? Run: docker compose up -d db")
        sys.exit(1)

    # Filter tables if specified
    tables = TABLES_CONFIG
    if args.table:
        tables = [t for t in TABLES_CONFIG if t["name"] == args.table]
        if not tables:
            print(f"❌ Unknown table '{args.table}'. Available: {[t['name'] for t in TABLES_CONFIG]}")
            sys.exit(1)

    for config in tables:
        try:
            migrate_table(src_engine, dst_engine, config, batch_size=args.batch_size, truncate=args.truncate)
        except Exception as e:
            print(f"❌ Error migrating {config['name']}: {e}")
            import traceback
            traceback.print_exc()

    print("\n========================================================")
    print("🏁 ALL MIGRATIONS COMPLETED!")
    print("👉 Next step: update backend/.env with:")
    print(f'   DATABASE_URL="{args.target}"')
    print("========================================================\n")

if __name__ == "__main__":
    main()
