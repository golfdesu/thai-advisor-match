"""
Local PostgreSQL (Docker) -> Supabase Sync Script
Pushes newly crawled, enriched, or updated data from your Local Docker PostgreSQL back to Supabase.
Run this only when you are ready to update production (e.g. at the end of a sprint or ingestion wave).
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

DEFAULT_LOCAL_URL = "postgresql://postgres:postgres@localhost:5432/advisor_match"
DEFAULT_SUPABASE_URL = os.getenv("SUPABASE_DATABASE_URL")

from scripts.migrate_supabase_to_local import TABLES_CONFIG, migrate_table

def main():
    parser = argparse.ArgumentParser(description="Sync data from Local Docker PostgreSQL up to Supabase")
    parser.add_argument("--source", type=str, default=DEFAULT_LOCAL_URL, help="Source Local Postgres URL")
    parser.add_argument("--target", type=str, default=DEFAULT_SUPABASE_URL, help="Target Supabase URL")
    parser.add_argument("--table", type=str, default=None, help="Sync specific table only (e.g. faculties)")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for transfer")
    parser.add_argument("--truncate", action="store_true", help="Truncate target before sync (BE CAREFUL on Supabase!)")
    args = parser.parse_args()

    print("\n========================================================")
    print("🚀 Thai EduCenter Database Sync: Local -> Supabase")
    print("========================================================")
    print(f"Source (Local)    : {args.source}")
    print(f"Target (Supabase) : {args.target[:35]}...{args.target[-15:] if args.target else ''}")
    print(f"Batch Size        : {args.batch_size}")
    print(f"Truncate          : {args.truncate}")
    print("========================================================\n")

    if not args.target:
        print("❌ Error: SUPABASE_DATABASE_URL is not set in backend/.env")
        sys.exit(1)

    try:
        src_engine = create_engine(args.source, pool_pre_ping=True)
        with src_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print("✅ Successfully connected to Local DB")
    except Exception as e:
        print(f"❌ Failed to connect to Local DB: {e}")
        sys.exit(1)

    try:
        dst_engine = create_engine(args.target, pool_pre_ping=True)
        with dst_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print("✅ Successfully connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)

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
            print(f"❌ Error syncing {config['name']}: {e}")
            import traceback
            traceback.print_exc()

    print("\n========================================================")
    print("🏁 LOCAL -> SUPABASE SYNC COMPLETED!")
    print("========================================================\n")

if __name__ == "__main__":
    main()
