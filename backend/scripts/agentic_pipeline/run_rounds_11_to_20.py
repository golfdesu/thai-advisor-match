# -*- coding: utf-8 -*-
"""
Autonomous Batch Runner for Rounds 11 - 20 (SKILL.state Engine)
Acquires authentic faculty data for sparse faculties across Top Thai Universities.
"""
import os
import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROUNDS = [
    {
        "round_num": 11,
        "name": "Silpakorn Faculty of Music",
        "univ_th": "มหาวิทยาลัยศิลปากร",
        "univ_en": "Silpakorn University",
        "faculty_th": "คณะดุริยางคศาสตร์",
        "faculty_en": "Faculty of Music",
        "url": "https://music.su.ac.th/faculty-member/",
        "export_file": "backend/data/agent_states/round11_silpakorn_music.py",
    },
    {
        "round_num": 12,
        "name": "TU Puey Ungphakorn School of Development Studies (PSDS)",
        "univ_th": "มหาวิทยาลัยธรรมศาสตร์",
        "univ_en": "Thammasat University",
        "faculty_th": "วิทยาลัยพัฒนศาสตร์ ป๋วย อึ๊งภากรณ์",
        "faculty_en": "Puey Ungphakorn School of Development Studies",
        "url": "https://psds.tu.ac.th/about-us/personnel/",
        "export_file": "backend/data/agent_states/round12_tu_psds.py",
    },
    {
        "round_num": 13,
        "name": "TU School of Global Studies (SGS)",
        "univ_th": "มหาวิทยาลัยธรรมศาสตร์",
        "univ_en": "Thammasat University",
        "faculty_th": "วิทยาลัยโลกคดีศึกษา",
        "faculty_en": "School of Global Studies",
        "url": "https://sgs.tu.ac.th/faculty/",
        "export_file": "backend/data/agent_states/round13_tu_sgs.py",
    },
    {
        "round_num": 14,
        "name": "CMU School of Public Policy (SPP)",
        "univ_th": "มหาวิทยาลัยเชียงใหม่",
        "univ_en": "Chiang Mai University",
        "faculty_th": "วิทยาลัยนโยบายสาธารณะ",
        "faculty_en": "School of Public Policy",
        "url": "https://spp.cmu.ac.th/our-school/our-people/",
        "export_file": "backend/data/agent_states/round14_cmu_spp.py",
    },
    {
        "round_num": 15,
        "name": "TU Pridi Banomyong International College (PBIC)",
        "univ_th": "มหาวิทยาลัยธรรมศาสตร์",
        "univ_en": "Thammasat University",
        "faculty_th": "วิทยาลัยนานาชาติ ปรีดี พนมยงค์",
        "faculty_en": "Pridi Banomyong International College",
        "url": "https://pbic.tu.ac.th/about-us/faculty-member/",
        "export_file": "backend/data/agent_states/round15_tu_pbic.py",
    },
    {
        "round_num": 16,
        "name": "KKU Faculty of Economics",
        "univ_th": "มหาวิทยาลัยขอนแก่น",
        "univ_en": "Khon Kaen University",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "faculty_en": "Faculty of Economics",
        "url": "https://econ.kku.ac.th/main/2257",
        "export_file": "backend/data/agent_states/round16_kku_econ.py",
    },
    {
        "round_num": 17,
        "name": "KMITL College of Advanced Manufacturing Innovation (AMI)",
        "univ_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "univ_en": "King Mongkut's Institute of Technology Ladkrabang",
        "faculty_th": "วิทยาลัยนวัตกรรมการผลิตขั้นสูง",
        "faculty_en": "College of Advanced Manufacturing Innovation",
        "url": "https://ami.kmitl.ac.th/people/faculty/",
        "export_file": "backend/data/agent_states/round17_kmitl_ami.py",
    },
    {
        "round_num": 18,
        "name": "PSU FMS - Public Administration",
        "univ_th": "มหาวิทยาลัยสงขลานครินทร์",
        "univ_en": "Prince of Songkla University",
        "faculty_th": "คณะวิทยาการจัดการ",
        "faculty_en": "Faculty of Management Sciences",
        "url": "https://www.fms.psu.ac.th/professor/professor-dpa/professor-pa/",
        "export_file": "backend/data/agent_states/round18_psu_fms_pa.py",
    },
    {
        "round_num": 19,
        "name": "PSU FMS - Finance",
        "univ_th": "มหาวิทยาลัยสงขลานครินทร์",
        "univ_en": "Prince of Songkla University",
        "faculty_th": "คณะวิทยาการจัดการ",
        "faculty_en": "Faculty of Management Sciences",
        "url": "https://www.fms.psu.ac.th/professor/professor-dba/professor-fin/",
        "export_file": "backend/data/agent_states/round19_psu_fms_fin.py",
    },
    {
        "round_num": 20,
        "name": "PSU FMS - Marketing",
        "univ_th": "มหาวิทยาลัยสงขลานครินทร์",
        "univ_en": "Prince of Songkla University",
        "faculty_th": "คณะวิทยาการจัดการ",
        "faculty_en": "Faculty of Management Sciences",
        "url": "https://www.fms.psu.ac.th/professor/professor-dba/professor-mkt/",
        "export_file": "backend/data/agent_states/round20_psu_fms_mkt.py",
    },
]

def run_all():
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend"

    cli_path = Path("backend/scripts/agentic_pipeline/cli_runner.py").resolve()

    print("=================================================================")
    print("🚀 LAUNCHING 10-ROUND AUTONOMOUS FACULTY ACQUISITION BATCH 2")
    print("=================================================================")

    for item in ROUNDS:
        r_num = item["round_num"]
        name = item["name"]
        print(f"\n>>> [ROUND {r_num:02d}/20] {name} ({item['univ_th']})")
        print(f"    Target URL: {item['url']}")
        print(f"    Export: {item['export_file']}")

        cmd = [
            sys.executable,
            str(cli_path),
            "--univ-th", item["univ_th"],
            "--univ-en", item["univ_en"],
            "--faculty-th", item["faculty_th"],
            "--faculty-en", item["faculty_en"],
            "--url", item["url"],
            "--export-file", item["export_file"],
            "--max-steps", "15",
            "--no-wiki"
        ]

        res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            print(f"    ✅ Round {r_num} completed successfully.")
            for line in res.stdout.splitlines():
                if "Completed!" in line or "Total verified faculties in state:" in line or "Extracted" in line:
                    print(f"       {line.strip()}")
        else:
            print(f"    ❌ Round {r_num} encountered error:")
            print(res.stderr[:500])

if __name__ == "__main__":
    run_all()
