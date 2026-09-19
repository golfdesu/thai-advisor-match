"""Systematically classify all shared emails:
1. Genuine duplicates of the same individual (to be merged preserving max citations, publications, and canonical fields)
2. Different individuals where the email is authentic to one and contaminated/borrowed on the other (to be cleared on the contaminated record)
3. Shared departmental inboxes (to be cleared per Section 9 Invariants)
"""
import json
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB

def classify():
    db = SessionLocal()
    try:
        report_path = BACKEND_DIR / "data" / "agent_states" / "deep_forensic_investigation_report.json"
        data = json.loads(report_path.read_text(encoding="utf-8"))

        all_shared = data.get("shared_emails_same_person", []) + data.get("shared_emails_diff_person", [])
        print(f"Total shared email groups to analyze: {len(all_shared)}")

        duplicate_pairs = []
        email_cleans = []

        for group in all_shared:
            email = group["email"]
            facs = group["faculties"]
            f1, f2 = facs[0], facs[1]

            # 1. Check if same person duplicates:
            # - Nipon Chattipakorn (cmu_cb0c6016_3425 vs cmu_med_nipon_001)
            # - Piyarat Chansiripornchai (chulalongk_facultyofv_chansiriporncha_169 vs chulalongk_facultyofv_fac_163_163)
            # - Sumpun Thammacharoen (chulalongk_facultyofv_thammacharoen_079 vs chulalongk_facultyofv_thamcharoen_068)
            # - Peter Ractham (tu_bus_tbs_018 vs tu_tbs_peter_001)
            # - Wasu Chaopanon (khonkaenun_collegeofc_chaopanon_061 vs kku_5412fb44_5980)
            # - Sirikan Chucherd (mfu_it_chucherd_011 vs mfu_sirikan_chucherd_1962)
            # - Marcin Szawelski (mahidoluni_collegeofm_szawelski_123 vs mahidoluni_collegeofm_szawelski_213)
            # - Nipattra Suwanparin (chulalongk_facultyofv_suwanprparin_172 vs chulalongk_facultyofv_fac_164_164)
            # - Jitladda Sakdapipanich (mahidoluni_facultyofs_tsakdapipanich_011 vs mu_sci_wave14_b_0019)
            # - Piyanan Taweethavonsawat (chulalongk_facultyofv_taw_112 vs chulalongk_facultyofv_taweethavonsawa_126)
            # - Teeravisit Laohapensaeng (mfu_it_teeravisit_001 vs mfu_teeravisit_laohapensaeng_4118)
            # - Pakorn Varanusupakul (cu_sci_wave14_b_0034 vs chulalongk_facultyofs_fac_006_006)
            # - Panuwat Padungros (cu_sci_wave14_b_0037 vs chulalongk_facultyofs_fac_014_014)
            # - Patchanita Thamyongkit (cu_sci_wave14_b_0039 vs chulalongk_facultyofs_fac_021_021)
            # - Numpon Insin (cu_sci_wave14_b_0031 vs chulalongk_facultyofs_fac_017_017)
            # - Treetip Boonyam (mahidoluni_collegeofm_boonyam_080 vs mahidoluni_collegeofm_boonyam_035)
            # - Joseph Bowman (mahidoluni_collegeofm_bowman_143 vs mahidoluni_collegeofm_bowman_036)
            # - Sanong Ekgasit (chulalongk_facultyofs_fac_007_007 vs chula_sci_002_8742ad)
            # - Watis Leelapatra (kku_1dd5e0f1_2035 vs khonkaenun_collegeofc_leelapatra_062)
            # - Kit Tientanopajai (kku_dd282888_5274 vs khonkaenun_collegeofc_tientanopajai_051)
            # - Kanchana Sethanan (kku_eng_wave12_0020 vs kku_eng_kanchana_001)

            # Let's print each
            print(f"{email}:")
            print(f"  A: {f1['id']} | {f1['name']} | cites={f1['cites']}")
            print(f"  B: {f2['id']} | {f2['name']} | cites={f2['cites']}")

    finally:
        db.close()

if __name__ == "__main__":
    classify()
