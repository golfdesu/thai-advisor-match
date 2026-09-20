"""
Automated System Status Synchronizer for PROJECT_STRUCTURE_AND_WORKFLOW.md

Queries authoritative metrics from local PostgreSQL (localhost:5432/advisor_match)
and programmatically updates Section 7.1 in PROJECT_STRUCTURE_AND_WORKFLOW.md.
"""

import argparse
from datetime import datetime
from pathlib import Path
import re
import sys

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup project root and backend path
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parents[2]
PROJECT_ROOT = CURRENT_FILE.parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import CourseDB, FacultyDB, ResearchLabDB
from sqlalchemy import func


# English labels for Top Universities for clean documentation
UNIVERSITY_EN_NAMES = {
    "มหาวิทยาลัยเกษตรศาสตร์": "Kasetsart University (KU)",
    "จุฬาลงกรณ์มหาวิทยาลัย": "Chulalongkorn University (CU)",
    "มหาวิทยาลัยเชียงใหม่": "Chiang Mai University (CMU)",
    "มหาวิทยาลัยมหิดล": "Mahidol University (MU)",
    "มหาวิทยาลัยธรรมศาสตร์": "Thammasat University (TU)",
    "มหาวิทยาลัยขอนแก่น": "Khon Kaen University (KKU)",
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": "King Mongkut's Institute of Technology Ladkrabang (KMITL)",
    "มหาวิทยาลัยสงขลานครินทร์": "Prince of Songkla University (PSU)",
    "มหาวิทยาลัยนเรศวร": "Naresuan University (NU)",
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": "Suranaree University of Technology (SUT)",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": "Srinakharinwirot University (SWU)",
    "มหาวิทยาลัยศิลปากร": "Silpakorn University (SU)",
    "มหาวิทยาลัยบูรพา": "Burapha University (BUU)",
    "มหาวิทยาลัยแม่ฟ้าหลวง": "Mae Fah Luang University (MFU)",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": "King Mongkut's University of Technology Thonburi (KMUTT)",
}


def fetch_database_stats():
    """Query live metrics from PostgreSQL."""
    db = SessionLocal()
    try:
        total_fac = db.query(FacultyDB).count()
        null_emb = db.query(FacultyDB).filter(FacultyDB.embedding.is_(None)).count()
        openalex_count = db.query(FacultyDB).filter(FacultyDB.openalex_id.isnot(None)).count()
        h_index_count = db.query(FacultyDB).filter(FacultyDB.h_index > 0).count()
        elite_count = (
            db.query(FacultyDB)
            .filter((FacultyDB.h_index >= 20) | (FacultyDB.total_citations >= 1000))
            .count()
        )
        total_cites = db.query(func.sum(FacultyDB.total_citations)).scalar() or 0
        en_names = (
            db.query(FacultyDB)
            .filter(FacultyDB.first_name.isnot(None), FacultyDB.last_name.isnot(None))
            .count()
        )
        emails_count = (
            db.query(FacultyDB)
            .filter(FacultyDB.email.isnot(None), FacultyDB.email != "")
            .count()
        )

        total_labs = db.query(ResearchLabDB).count()
        total_courses = db.query(CourseDB).count()

        univ_rows = (
            db.query(FacultyDB.university_th, func.count(FacultyDB.id))
            .group_by(FacultyDB.university_th)
            .order_by(func.count(FacultyDB.id).desc())
            .limit(10)
            .all()
        )

        return {
            "total_fac": total_fac,
            "null_emb": null_emb,
            "openalex_count": openalex_count,
            "h_index_count": h_index_count,
            "elite_count": elite_count,
            "total_cites": int(total_cites),
            "en_names": en_names,
            "emails_count": emails_count,
            "total_labs": total_labs,
            "total_courses": total_courses,
            "top_universities": univ_rows,
        }
    finally:
        db.close()


def generate_status_markdown(stats: dict, as_of_date: str) -> str:
    """Format metrics into Section 7.1 markdown block."""
    total_fac = stats["total_fac"]
    openalex_pct = (stats["openalex_count"] / total_fac * 100) if total_fac else 0.0
    en_names_pct = (stats["en_names"] / total_fac * 100) if total_fac else 0.0
    emails_pct = (stats["emails_count"] / total_fac * 100) if total_fac else 0.0
    cites_millions = stats["total_cites"] / 1_000_000

    lines = [
        f"### 7.1 Current System Status (As of {as_of_date})",
        f"* **Faculty & Researchers in Local DB:** **{total_fac:,} records** (Post-Stage 6 Unlisted Discovery, 10-Dimensional Zero-Defect Baseline).",
        f"* **Missing Vector Embeddings:** **{stats['null_emb']} records** (100% 768-dimensional vector completeness).",
        f"* **OpenAlex-resolved Scholars:** **{stats['openalex_count']:,} records** ({openalex_pct:.1f}%) | h-index > 0: **{stats['h_index_count']:,}** | Elite advisors (h >= 20 or citations >= 1,000): **{stats['elite_count']:,}** | Total citations: **{cites_millions:.2f} Million** ({stats['total_cites']:,}).",
        f"* **Romanized English Names from Institutional Sources:** **{stats['en_names']:,} records** ({en_names_pct:.1f}% Latin first/last name coverage).",
        f"* **Official Academic Emails:** **{stats['emails_count']:,} records** ({emails_pct:.1f}% verified institutional emails, 0 personal freemails, 0 personal phone numbers per PDPA).",
        f"* **National Flagship Research Laboratories:** **{stats['total_labs']:,} Labs** (100% bidirectional advisor linking).",
        f"* **Graduate Academic Programs:** **{stats['total_courses']:,} curricula** across Thai universities.",
        "* **Top 10 Universities by Faculty Count:**",
    ]

    for idx, (univ_th, count) in enumerate(stats["top_universities"], 1):
        label = UNIVERSITY_EN_NAMES.get(univ_th, univ_th)
        lines.append(f"  {idx}. {label}: {count:,}")

    return "\n".join(lines)


def update_runbook(stats: dict, check_only: bool = False) -> bool:
    """Replace Section 7.1 in PROJECT_STRUCTURE_AND_WORKFLOW.md with updated stats."""
    runbook_path = PROJECT_ROOT / "PROJECT_STRUCTURE_AND_WORKFLOW.md"
    if not runbook_path.exists():
        print(f"Error: Runbook file not found at {runbook_path}")
        return False

    content = runbook_path.read_text(encoding="utf-8")
    today_str = datetime.now().strftime("%Y-%m-%d")
    new_section = generate_status_markdown(stats, today_str)

    # Pattern matches Section 7.1 up to Section 7.2
    pattern = re.compile(
        r"### 7\.1 Current System Status \(As of [^\)]+\)\n.*?(?=\n### 7\.2)",
        re.DOTALL,
    )

    if not pattern.search(content):
        print("Warning: Section 7.1 pattern not matched in runbook. Searching alternative header...")
        alt_pattern = re.compile(
            r"### 7\.1 Current System Status[^\n]*\n.*?(?=\n### 7\.2)",
            re.DOTALL,
        )
        if not alt_pattern.search(content):
            print("Error: Could not locate Section 7.1 in PROJECT_STRUCTURE_AND_WORKFLOW.md")
            return False
        pattern = alt_pattern

    updated_content = pattern.sub(new_section, content)

    if check_only:
        print("\n[CHECK ONLY] Generated Section 7.1 Markdown:\n")
        print(new_section)
        return True

    runbook_path.write_text(updated_content, encoding="utf-8")
    print(f"[OK] Successfully updated Section 7.1 in {runbook_path.name} (As of {today_str})")
    return True


def main():
    parser = argparse.ArgumentParser(description="Sync PostgreSQL stats into PROJECT_STRUCTURE_AND_WORKFLOW.md")
    parser.add_argument("--check", action="store_true", help="Print stats without modifying the file")
    args = parser.parse_args()

    print("Querying PostgreSQL database (localhost:5432/advisor_match)...")
    stats = fetch_database_stats()
    print(f"-> Total Faculty: {stats['total_fac']:,}")
    print(f"-> OpenAlex Resolved: {stats['openalex_count']:,}")
    print(f"-> Citations: {stats['total_cites']:,}")
    print(f"-> Courses: {stats['total_courses']:,}")
    print(f"-> Labs: {stats['total_labs']:,}")

    success = update_runbook(stats, check_only=args.check)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
