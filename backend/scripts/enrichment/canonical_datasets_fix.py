# -*- coding: utf-8 -*-
"""
Canonical fix for SOURCE dataset files (scripts/data_sources/*).
The massive ingestion runner re-upserts every dataset on each run, so any
DB-only canonical hygiene is reverted unless the source files are fixed too.
Applies the exact same evidence-based rules as enrichment/canonical_faculty_merge.py.
"""
import os
import sys
import json
import importlib

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BACKEND_DIR)

from scripts.enrichment.canonical_faculty_merge import (
    resolve_uni, split_multi_faculty, apply_composite_dept_rule,
    EXACT_ID_CANONICAL, FACULTY_CANONICAL, UNI_BY_ID_PREFIX, UNI_BY_DOMAIN,
    ENG_NAME, MULTI_FACULTY_SPLIT,
)

import scripts.faculty_massive_ingestion_runner as runner


def var_name_for(module, target_list):
    for name, val in vars(module).items():
        if val is target_list:
            return name
    return None


def fix_item(item: dict, header_comment: str):
    fid = item.get("id", "")
    email = item.get("email", "")
    dep = item.get("department_th", "") or ""

    pair = resolve_uni(email, fid, dep)
    if pair:
        item["university_th"], item["university"] = pair
    if item.get("university_th") == "สถาบันบัณฑิตพัฒนบริหารศาสตร์":
        item["university_th"] = "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)"
        item["university"] = ENG_NAME[item["university_th"]]

    cur = (item.get("faculty_th") or "").strip()
    if fid in EXACT_ID_CANONICAL:
        fac_th, fac_en = EXACT_ID_CANONICAL[fid]
        item["faculty_th"], item["faculty"] = fac_th, fac_en
    else:
        class _Shim:
            pass
        shim = _Shim()
        shim.id, shim.email, shim.department_th = fid, email, dep
        shim.university_th = item.get("university_th")
        shim.faculty_th = cur
        new_fac = split_multi_faculty(shim)
        if new_fac:
            item["faculty_th"] = new_fac
            item["university_th"] = shim.university_th
            item["university"] = shim.university
            if getattr(shim, "faculty", None):
                item["faculty"] = shim.faculty
        else:
            new_fac = apply_composite_dept_rule(shim)
            if new_fac:
                item["faculty_th"] = new_fac
                if getattr(shim, "faculty", None):
                    item["faculty"] = shim.faculty
                if getattr(shim, "university_th", None) != cur:
                    pass
            table = FACULTY_CANONICAL.get(item.get("university_th", ""), {})
            if cur in table:
                item["faculty_th"] = table[cur]

    # Phase 3c rule (CU medtech cohort) on dataset items
    if item.get("university_th") == "จุฬาลงกรณ์มหาวิทยาลัย" and item.get("faculty_th") == "คณะเทคนิคการแพทย์":
        item["university_th"] = "มหาวิทยาลัยมหิดล"
        item["university"] = ENG_NAME["มหาวิทยาลัยมหิดล"]
    if item.get("university_th") == "จุฬาลงกรณ์มหาวิทยาลัย" and item.get("faculty_th") == "คณะสหเวชศาสตร์ และ คณะเทคนิคการแพทย์":
        item["faculty_th"] = "คณะสหเวชศาสตร์"
        item["faculty"] = "Faculty of Allied Health Sciences"
    return item


def main():
    seen_files = {}
    total_fixed = 0
    for name, dataset in runner.ALL_FACULTY_DATASETS:
        if not dataset:
            continue
        mod = sys.modules[dataset.__module__] if hasattr(dataset, "__module__") else None
        # find module owning this list object
        owner = None
        for mname, m in list(sys.modules.items()):
            if mname.startswith("scripts.data_sources") and any(v is dataset for v in vars(m).values() if isinstance(v, list)):
                owner = m
                break
        if owner is None or not hasattr(owner, "__file__"):
            continue
        path = os.path.abspath(owner.__file__)
        if path.endswith(".pyc"):
            path = path[:-1]
        if path in seen_files:
            continue
        vname = var_name_for(owner, dataset)
        if not vname:
            continue
        seen_files[path] = (owner, vname, dataset)

    for path, (owner, vname, dataset) in seen_files.items():
        src = open(path, encoding="utf-8").read()
        header = src.splitlines()[0] if src.startswith("#") else ""
        fixed = 0
        for item in dataset:
            before = json.dumps((item.get("university_th"), item.get("faculty_th")), ensure_ascii=False)
            fix_item(item, header)
            after = json.dumps((item.get("university_th"), item.get("faculty_th")), ensure_ascii=False)
            if before != after:
                fixed += 1
        if fixed:
            code = (f"{header}\n" if header else "") + f"{vname} = " + json.dumps(dataset, ensure_ascii=False, indent=4) + "\n"
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
            total_fixed += fixed
            print(f"   ✔ {os.path.basename(path)}: {fixed} items canonicalized")
    print(f"✅ SOURCE dataset canonicalization complete: {total_fixed} items fixed across {len(seen_files)} scanned files")


if __name__ == "__main__":
    main()
