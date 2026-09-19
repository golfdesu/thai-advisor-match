# -*- coding: utf-8 -*-
import sys
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

db = SessionLocal()

print("--- SCANNING FOR ACTUAL TRAILING GLUED SUFFIXES IN FULL_NAME_TH ---")
trailing_patterns = [
    r"รองศาสตราจารย์[\s﻿]*$",
    r"ผู้ช่วยศาสตราจารย์[\s﻿]*$",
    r"ศาสตราจารย์[\s﻿]*$",
    r"อาจารย์[\s﻿]*$",
    r",?\s*(?:Ph\.?D\.?|M\.?D\.?|M\.?Sc\.?|B\.?Sc\.?|B\.?Eng\.?)[\s﻿]*$",
    r"﻿+",
    r"​+",
]

glued_facs = []
for f in db.query(FacultyDB).all():
    name = f.full_name_th or ""
    for pat in trailing_patterns:
        if re.search(pat, name, flags=re.IGNORECASE):
            glued_facs.append((f.id, f.university_th, f.faculty_th, name, pat))
            break

print(f"Faculties with trailing suffixes: {len(glued_facs)}")
for gf in glued_facs:
    print(f"  {gf[0]} | {gf[1]} | {gf[2]} | {repr(gf[3])} | matched: {gf[4]}")

db.close()
