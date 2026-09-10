"""
CMU Vet JSON API -> SKILL.state Reducer pipeline.
Maps verified API records (vmcmu.vet.cmu.ac.th) to RawFacultyProfile objects,
applies them through FacultyStateReducer (RapidFuzz dedup + title normalization),
checkpoints state and exports the dataset.
"""
import io
import json
import os
import re
import sys
import time
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.stdout.reconfigure(encoding="utf-8")

import requests

from scripts.agentic_pipeline.models import (
    ExtractionAgentState,
    FacultyStatePatch,
    RawFacultyProfile,
)
from scripts.agentic_pipeline.state_reducer import FacultyStateReducer, save_state_checkpoint

API = "https://vmcmu.vet.cmu.ac.th/pages/person/api/fetchDataPerson_api.php"
CATEGORIES = ["vet_subject-1", "vet_subject-2"]

UNIV_TH = "มหาวิทยาลัยเชียงใหม่"
UNIV_EN = "Chiang Mai University"
FAC_TH = "คณะสัตวแพทยศาสตร์"
FAC_EN = "Faculty of Veterinary Medicine"


def clean_link(v):
    if not v or str(v).lower() in ("null", "none", ""):
        return None
    return str(v).strip()


def main():
    state = ExtractionAgentState(
        session_id=f"cmu_vet_api_{int(time.time())}_{uuid.uuid4().hex[:6]}",
        target_university_th=UNIV_TH,
        target_university_en=UNIV_EN,
        target_faculty_th=FAC_TH,
        target_faculty_en=FAC_EN,
    )
    reducer = FacultyStateReducer()
    total = 0

    for cat in CATEGORIES:
        r = requests.get(
            API,
            params={"typeData[type]": cat, "typeData[hospital]": cat},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        payload = r.json()
        data = payload.get("response", {}).get("results", {}).get("data", [])
        print(f"{cat}: {len(data)} records from API")

        profiles = []
        for e in data:
            prefix = ""
            if isinstance(e.get("prefix"), list) and e["prefix"]:
                prefix = (e["prefix"][0].get("prefix_TH") or "").strip()
            branch_th = ""
            if isinstance(e.get("branch"), list) and e["branch"]:
                branch_th = (e["branch"][0].get("branch_TH") or "").strip()

            full_th = f"{prefix} {e.get('fname_TH', '')} {e.get('lname_TH', '')}".strip()
            if not re.search(r"[\u0E00-\u0E7F]", full_th):
                continue

            research = e.get("research") or ""
            interests = [x.strip() for x in re.split(r"[,;/]", research) if x.strip()][:7]

            fname_en = re.sub(r"<[^>]+>", "", e.get("fname_EN") or "")
            lname_en = re.sub(r"<[^>]+>", "", e.get("lname_EN") or "")

            profiles.append(RawFacultyProfile(
                full_name_th=full_th,
                academic_title_th=prefix or None,
                first_name=fname_en.strip() or None,
                last_name=lname_en.strip() or None,
                email=(e.get("email") or "").strip() or None,
                department_th=branch_th or (e.get("department") or "").strip() or None,
                image_url=f"https://vmcmu.vet.cmu.ac.th/images/imageBranch/{e['image']}" if e.get("image") else None,
                research_interests=interests,
                scholar_url=clean_link(e.get("link_scholar")),
            ))

        patch = FacultyStatePatch(new_profiles=profiles, summary_of_changes=f"API category {cat}")
        state = reducer.apply_patch(state, patch, step_tokens=0)
        state.visited_urls.append(f"{API}?{cat}")
        total += len(profiles)
        print(f"  -> state now: {len(state.faculties)}")

    state.status = "completed"
    save_state_checkpoint(state, output_dir="data/agent_states")

    out = os.path.join("data", "agent_states", "cmu_vet_api_export.py")
    code = state_export(state)
    io.open(out, "w", encoding="utf-8").write(code)
    print(f"✨ CMU Vet: {len(state.faculties)} verified -> {out}")


def state_export(state):
    faculty_list = list(state.faculties.values())
    return (
        f"# Auto-generated from vmcmu.vet.cmu.ac.th JSON API via SKILL.state Reducer "
        f"(Session: {state.session_id})\nEXTRACTED_FACULTIES = "
        + json.dumps(faculty_list, ensure_ascii=False, indent=4)
        + "\n"
    )


if __name__ == "__main__":
    main()
