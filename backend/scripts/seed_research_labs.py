import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure backend root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.db_models import ResearchLabDB
from app.core.embedding_service import embedding_service
from scripts.data_sources.top_research_labs import TOP_RESEARCH_LABS
from scripts.data_sources.expanded_research_labs import EXPANDED_RESEARCH_LABS
from scripts.data_sources.regional_research_labs_phase2 import REGIONAL_RESEARCH_LABS_PHASE2

ALL_RESEARCH_LABS = TOP_RESEARCH_LABS + EXPANDED_RESEARCH_LABS + REGIONAL_RESEARCH_LABS_PHASE2

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def build_lab_embedding_text(lab: dict) -> str:
    """Synthesizes structured rich text for high-accuracy 768-dim vector embedding."""
    name_th = lab.get("name_th", "")
    name_en = lab.get("name_en", "")
    univ_th = lab.get("university_th", "")
    univ_en = lab.get("university", "")
    fac_th = lab.get("faculty_th", "")
    fac_en = lab.get("faculty", "")
    dept_th = lab.get("department_th", "")
    dept_en = lab.get("department", "")
    desc = lab.get("description", "")
    domains = ", ".join(lab.get("research_domains", []))
    equipment = ", ".join(lab.get("flagship_equipment", []))
    partners = ", ".join(lab.get("industry_partners", []))
    positions = ", ".join(lab.get("open_positions", []))

    parts = [
        f"ห้องปฏิบัติการและศูนย์วิจัย: {name_th} ({name_en})",
        f"มหาวิทยาลัยและคณะ: {univ_th} ({univ_en}), {fac_th} ({fac_en}), {dept_th} ({dept_en})",
        f"รายละเอียดและวิสัยทัศน์: {desc}",
        f"สาขาวิชาวิจัยและความเชี่ยวชาญหลัก (Research Domains): {domains}",
        f"เครื่องมือวิจัยและโครงสร้างพื้นฐานระดับชาติ (Flagship Equipment & Infrastructure): {equipment}",
        f"พันธมิตรภาคอุตสาหกรรมและระดับนานาชาติ (Industry Partners): {partners}",
        f"ทุนการศึกษาและตำแหน่งที่เปิดรับ (Scholarships & Open Positions): {positions}"
    ]
    return "\n".join(parts)


def process_lab(lab_data: dict):
    emb_text = build_lab_embedding_text(lab_data)
    try:
        vector = embedding_service.get_embedding(emb_text)
    except Exception as e:
        logger.warning(f"Failed to generate embedding for {lab_data.get('id')}: {e}")
        vector = None

    return lab_data, emb_text, vector


def seed_labs():
    logger.info("Initializing research_labs table schema in database...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        logger.info(f"Preparing to embed and seed {len(ALL_RESEARCH_LABS)} premier research labs...")

        # Pre-query existing labs to avoid redundant embedding generation
        existing_labs = {
            row[0]: row[1]
            for row in db.query(ResearchLabDB.id, ResearchLabDB.embedding).all()
        }

        embedded_records = []
        labs_to_embed = []
        for lab in ALL_RESEARCH_LABS:
            lab_id = lab.get("id")
            existing_emb = existing_labs.get(lab_id)
            if existing_emb is not None:
                emb_text = build_lab_embedding_text(lab)
                embedded_records.append((lab, emb_text, existing_emb))
            else:
                labs_to_embed.append(lab)

        if labs_to_embed:
            logger.info(f"Vectorizing {len(labs_to_embed)} new/un-embedded research labs...")
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_lab = {executor.submit(process_lab, lab): lab for lab in labs_to_embed}
                for future in as_completed(future_to_lab):
                    lab_data, emb_text, vector = future.result()
                    embedded_records.append((lab_data, emb_text, vector))
                    logger.info(f"Vectorized lab: {lab_data['id']} ({lab_data['name_th'][:30]}...)")
        else:
            logger.info("All research labs already have embeddings in database.")

        logger.info("Writing lab records to PostgreSQL / Supabase...")
        count_inserted = 0
        count_updated = 0

        for lab_data, emb_text, vector in embedded_records:
            existing = db.query(ResearchLabDB).filter(ResearchLabDB.id == lab_data["id"]).first()
            if existing:
                existing.name_th = lab_data.get("name_th")
                existing.name_en = lab_data.get("name_en")
                existing.university = lab_data.get("university")
                existing.university_th = lab_data.get("university_th")
                existing.faculty = lab_data.get("faculty")
                existing.faculty_th = lab_data.get("faculty_th")
                existing.department = lab_data.get("department")
                existing.department_th = lab_data.get("department_th")
                existing.lead_advisor_id = lab_data.get("lead_advisor_id")
                existing.member_faculty_ids = lab_data.get("member_faculty_ids", [])
                existing.description = lab_data.get("description")
                existing.research_domains = lab_data.get("research_domains", [])
                existing.flagship_equipment = lab_data.get("flagship_equipment", [])
                existing.industry_partners = lab_data.get("industry_partners", [])
                existing.open_positions = lab_data.get("open_positions", [])
                existing.website_url = lab_data.get("website_url")
                existing.image_url = lab_data.get("image_url")
                existing.embedding_text = emb_text
                if vector:
                    existing.embedding = vector
                count_updated += 1
            else:
                new_lab = ResearchLabDB(
                    id=lab_data["id"],
                    name_th=lab_data.get("name_th"),
                    name_en=lab_data.get("name_en"),
                    university=lab_data.get("university"),
                    university_th=lab_data.get("university_th"),
                    faculty=lab_data.get("faculty"),
                    faculty_th=lab_data.get("faculty_th"),
                    department=lab_data.get("department"),
                    department_th=lab_data.get("department_th"),
                    lead_advisor_id=lab_data.get("lead_advisor_id"),
                    member_faculty_ids=lab_data.get("member_faculty_ids", []),
                    description=lab_data.get("description"),
                    research_domains=lab_data.get("research_domains", []),
                    flagship_equipment=lab_data.get("flagship_equipment", []),
                    industry_partners=lab_data.get("industry_partners", []),
                    open_positions=lab_data.get("open_positions", []),
                    website_url=lab_data.get("website_url"),
                    image_url=lab_data.get("image_url"),
                    embedding_text=emb_text,
                    embedding=vector
                )
                db.add(new_lab)
                count_inserted += 1

        db.commit()
        logger.info(f"Successfully seeded research labs: {count_inserted} inserted, {count_updated} updated.")

        # Quick verification query
        total_labs = db.query(ResearchLabDB).count()
        logger.info(f"Total Research Labs in database: {total_labs}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding research labs: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_labs()
