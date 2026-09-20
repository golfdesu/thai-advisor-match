# -*- coding: utf-8 -*-
"""
Prepare and execute Phase 1: CU & KU Deep Cleaning
Fixes:
- 20 CU Science 'REDACTED'
- 12 CU CBS 'Miss'
- 6 CU Pharmacy 'Chula'
- 2 CU Education 'Member'
- 1 CU Architecture 'Danai Thaitakoo' -> 'Vikrom Laovisutthichai'
- 9 CU Foreign faculty full_name_th
- 45 KU Agro-Industry title & role leaks
"""
import os
import sys
import json
import re
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_text import build_faculty_embedding_text
from app.core.embedding_service import EmbeddingService, load_all_gemini_keys
from google import genai

STATE_CHECKPOINT_PATH = os.path.join(BACKEND_DIR, "data", "agent_states", "skill_state_cu_ku_deep_clean.json")

# 1. CU Science 'REDACTED' Map
CU_SCI_REDACTED_MAP = {
    "cu_sci_wave14_b_0112": ("Parinya", "Karndumri"),        # ปริญญา การดำริห์
    "cu_sci_wave14_b_0106": ("Taweewat", "Somboonpanyakul"), # ทวีวัฒน์ สมบูรณ์ปัญญากุล
    "cu_sci_wave14_b_0111": ("Panadda", "Dechadilok"),       # ปนัดดา เดชาดิลก
    "cu_sci_wave14_b_0138": ("Orapin", "Wannadelok"),        # อรพิน วรรณดิลก
    "cu_sci_wave14_b_0105": ("Napat", "Poovuttikul"),        # ณภัทร ภู่วุฒิกุล
    "cu_sci_wave14_b_0107": ("Thanawut", "Thanathibodee"),   # ธนวุฒิ ธนาธิบดี
    "cu_sci_wave14_b_0108": ("Thiti", "Taychatanapat"),      # ธิติ เตชธนพัฒน์
    "cu_sci_wave14_b_0113": ("Patcha", "Chatraphorn"),       # ปัจฉา ฉัตราภรณ์
    "cu_sci_wave14_b_0114": ("Piyabut", "Burikham"),         # ปิยบุตร บุรีคำ
    "cu_sci_wave14_b_0120": ("Yossathorn", "Tawabutr"),      # ยศธร ทะวะบุตร
    "cu_sci_wave14_b_0122": ("Rangsima", "Chanphana"),       # รังสิมา ชาญพนา
    "cu_sci_wave14_b_0123": ("Rujikorn", "Dhanawittayapol"), # รุจิกร ธนวิทยาพล
    "cu_sci_wave14_b_0124": ("Warakorn", "Yanwachirakul"),   # วรากร ญาณวชิรากุล
    "cu_sci_wave14_b_0126": ("Vicharit", "Yingcharoenrat"),  # วิชาฤทธิ์ ยิ่งเจริญรัตน์
    "cu_sci_wave14_b_0130": ("Sakuntam", "Sanorpim"),        # สกุลธรรม เสนาะพิมพ์
    "cu_sci_wave14_b_0135": ("Santipong", "Boribarn"),       # สันติพงศ์ บริบาล
    "cu_sci_wave14_b_0137": ("Surachate", "Limkumnerd"),     # สุรเชษฐ์ หลิมกำเนิด
    "cu_sci_wave14_b_0104": ("Choosri", "Wongmanerod"),      # ชูศรี วงศ์มณีโรจน์
    "cu_sci_wave14_b_0116": ("Porncharoen", "Palotaidamkerng"), # พรเจริญ ผโลทัยดำเกิง
    "cu_sci_wave14_b_0140": ("Amnat", "Sathanon"),           # อำนาจ สาธานนท์
}

# 2. CU CBS 'Miss' Map
CU_CBS_MISS_MAP = {
    "cu_cbs_wave11_0268": ("Nattaporn", "Virunhagarun", "ผศ. ณัฐพร วิรุฬหการุญ"),
    "cu_cbs_wave11_0315": ("Arin", "Chirapaisarnkul", "อ. อรินทร์ จิรไพศาลกุล"),
    "cu_cbs_wave11_0341": ("Kanya", "Sannamwong", "อ. กัญญา แสนนามวงษ์"),
    "cu_cbs_wave11_0378": ("Piyanuch", "Marittanaporn", "อ. ปิยนุช มริตตนะพร"),
    "cu_cbs_wave11_0345": ("Kingpai", "Koosakulnirund", "อ. กิ่งไผ่ คู่สกุลนิรันดร์"),
    "cu_cbs_wave11_0398": ("Samita", "Dhanasobhon", "อ. สมิตา ธนะโสภณ"),
    "cu_cbs_wave11_0302": ("Varaporn", "Pothipala", "อ. วราภรณ์ โพธิผละ"),
    "cu_cbs_wave11_0316": ("Aussdaporn", "Machavanich", "อ. อัษฎาพร มัจฉวานิช"),
    "cu_cbs_wave11_0371": ("Patcharee", "Treepornchaisak", "อ. พัชรี ตรีพรชัยศักดิ์"),
    "cu_cbs_wave11_0391": ("Preeyaporn", "Jareonlarp", "อ. ปรียาภรณ์ เจริญลาภ"),
    "cu_cbs_wave11_0432": ("Waraporn", "Prapasirikul", "อ. วราพร ประภาศิริกุล"),
    "cu_cbs_wave11_0430": ("Wanvadee", "Tangpaisarnkul", "อ. วรรณวดี ตั้งไพศาลกุล"),
}

# 3. CU Pharmacy 'Chula' Map
CU_PHARM_CHULA_MAP = {
    "cu_pharm_wave16_0082": ("Sirinoot", "Palapinyo"),     # ผศ. ภญ. สิรินุช พละภิญโญ
    "cu_pharm_wave16_0033": ("Nonthaneth", "Nalinratana"), # อ. ภก. ดร. นนท์ธเนศ นลินรัตน์
    "cu_pharm_wave16_0050": ("Pasarapa", "Towiwat"),       # รศ. ร.ท.หญิง ภญ. ดร. ภัสราภา โตวิวัฒน์
    "cu_pharm_wave16_0075": ("Veerakiet", "Boonkanokwong"), # ผศ. ภก. ดร. วีระเกียรติ บุญกนกวงศ์
    "cu_pharm_wave16_0095": ("Chotirat", "Nakaranurack"),  # ผศ. ภญ. โชติรัตน์ นครานุรักษ์
    "cu_pharm_wave16_0058": ("Rataya", "Luechapudiporn"),  # รศ. ภญ. ดร. รัตยา ลือชาพุฒิพร
}

# 4. CU Architecture & Education Map
CU_OTHER_MAP = {
    "cu_ds_wave11_0015": ("Vikrom", "Laovisutthichai"), # ผศ.ดร. วิกรม เหล่าวิสุทธิชัย
    "cu_wave19_edu_0015": ("Ravee", "Chutasring"),      # ผศ.ดร. ระวี จูฑศฤงค์
    "cu_wave19_edu_0025": ("Penvara", "Chuprawat"),     # ผศ.ดร. เพ็ญวรา ชูประวัติ
}

# 5. CU Foreign Faculty full_name_th correction
CU_FOREIGN_MAP = {
    "cu_cbs_wave11_0044": "อ. Morten Bennedsen",
    "cu_cbs_wave11_0047": "อ. Shawn Cole",
    "cu_cbs_wave11_0049": "อ. Tony Kang",
    "cu_ahs_wave15_0008": "ดร. James Michael Brimson",
    "cu_cbs_wave11_0048": "อ. Söhnke M. Bartram",
    "cu_cbs_wave11_0046": "อ. Roger King",
    "cu_cbs_wave11_0354": "อ. Mustafa Moussa",
    "cu_cbs_wave11_0038": "อ. Deborah Lucas",
    "cu_cbs_wave11_0045": "อ. Paul Embrechts",
}

def clean_ku_agro_name(f_th, f_en, l_en, email):
    """
    Parses and sanitizes KU Agro faculty records with title/role leaks.
    """
    combined = f"{f_en} {l_en}".strip()
    # Strip prefixes: Ait, En, Asst, Assoc, Prof, Associate, Assistant, Essor, etc.
    combined = re.sub(r"^(?:Ait\s+En\s+|Ait\s+|En\s+|Asst\s+Prof\s+|Assoc\s+Prof\s+|Associate\s+Prof\s+|Assistant\s+Prof\s+|Assoc\s+|Asst\s+|Associate\s+|Assistant\s+|Essor\s+|Prof\s+|Dr\s+|Mr\s+|Ms\s+|Mrs\s+)+", "", combined, flags=re.I).strip()
    # Strip suffixes: Professor Emeritus, Academic Expert, Editnp, Ph, Dba Finance, etc.
    combined = re.sub(r"\s+(?:Professor\s+Emeritus|Academic\s+Expert|Emeritus|Expert|Editnp|Ph\.?D?|Dba\s+Finance|Dba).*$", "", combined, flags=re.I).strip()
    parts = combined.split()
    if len(parts) >= 2:
        return parts[0].title(), " ".join(parts[1:]).title()
    elif len(parts) == 1:
        return parts[0].title(), "Agro"
    return f_en, l_en

def main():
    print("=================================================================")
    print("🚀 PHASE 1: CU & KU DEEP QUALITY HYGIENE RESOLUTION")
    print("=================================================================")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    db = SessionLocal()
    embedder = EmbeddingService()

    modified_records = []

    # 1. Fix CU Science REDACTED
    for fid, (f_en, l_en) in CU_SCI_REDACTED_MAP.items():
        r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if r:
            r.first_name = f_en
            r.last_name = l_en
            r.embedding_text = build_faculty_embedding_text(r)
            r.embedding = embedder.get_embedding(r.embedding_text)
            modified_records.append((fid, f"{f_en} {l_en}", "CU_SCI_REDACTED"))

    # 2. Fix CU CBS Miss
    for fid, (f_en, l_en, th_clean) in CU_CBS_MISS_MAP.items():
        r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if r:
            r.first_name = f_en
            r.last_name = l_en
            r.full_name_th = th_clean
            r.embedding_text = build_faculty_embedding_text(r)
            r.embedding = embedder.get_embedding(r.embedding_text)
            modified_records.append((fid, f"{f_en} {l_en}", "CU_CBS_MISS"))

    # 3. Fix CU Pharmacy Chula
    for fid, (f_en, l_en) in CU_PHARM_CHULA_MAP.items():
        r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if r:
            r.first_name = f_en
            r.last_name = l_en
            r.embedding_text = build_faculty_embedding_text(r)
            r.embedding = embedder.get_embedding(r.embedding_text)
            modified_records.append((fid, f"{f_en} {l_en}", "CU_PHARM_CHULA"))

    # 4. Fix CU Architecture & Education
    for fid, (f_en, l_en) in CU_OTHER_MAP.items():
        r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if r:
            r.first_name = f_en
            r.last_name = l_en
            r.embedding_text = build_faculty_embedding_text(r)
            r.embedding = embedder.get_embedding(r.embedding_text)
            modified_records.append((fid, f"{f_en} {l_en}", "CU_OTHER_MAP"))

    # 5. Fix CU Foreign Faculty full_name_th
    for fid, th_name in CU_FOREIGN_MAP.items():
        r = db.query(FacultyDB).filter(FacultyDB.id == fid).first()
        if r:
            r.full_name_th = th_name
            r.embedding_text = build_faculty_embedding_text(r)
            r.embedding = embedder.get_embedding(r.embedding_text)
            modified_records.append((fid, th_name, "CU_FOREIGN_TH"))

    # 6. Fix KU Agro Title & Role Leaks
    ku_agro_records = db.query(FacultyDB).filter(
        FacultyDB.university_th.like("%เกษตรศาสตร์%"),
        FacultyDB.faculty_th.like("%อุตสาหกรรมเกษตร%")
    ).all()
    for r in ku_agro_records:
        f = r.first_name or ""
        l = r.last_name or ""
        if any(w.lower() in f.lower() for w in ["prof", "assoc", "asst", "ait", "associate", "assistant", "essor"]) or \
           any(w.lower() in l.lower() for w in ["expert", "emeritus", "editnp", "dba", "finance", "ph", "prof"]):
            clean_f, clean_l = clean_ku_agro_name(r.full_name_th, f, l, r.email)
            if clean_f != f or clean_l != l:
                r.first_name = clean_f
                r.last_name = clean_l
                r.embedding_text = build_faculty_embedding_text(r)
                r.embedding = embedder.get_embedding(r.embedding_text)
                modified_records.append((r.id, f"{clean_f} {clean_l}", "KU_AGRO_TITLE_CLEAN"))

    db.commit()
    print(f"✅ Successfully cleaned and re-indexed {len(modified_records)} records in CU and KU!")

    # Checkpoint to disk
    os.makedirs(os.path.dirname(STATE_CHECKPOINT_PATH), exist_ok=True)
    with open(STATE_CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "count": len(modified_records),
            "records": [{"id": m[0], "name": m[1], "rule": m[2]} for m in modified_records]
        }, f, ensure_ascii=False, indent=2)

    db.close()

if __name__ == "__main__":
    main()
