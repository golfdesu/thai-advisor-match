# -*- coding: utf-8 -*-
"""Apply a reviewed local-database hygiene pass.

Default mode is read-only and writes an audit report.  Pass ``--apply`` to
commit the targeted corrections to the local ``advisor_match`` database.
This script never connects to Supabase and never deletes faculty rows.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Support execution from the repository root and from backend/.
_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

REPORT_PATH = _BACKEND / "data" / "agent_states" / "db_hygiene_2026_09_12.json"
PHONE_ID = "cu_pharm_wave16_0077"
# Thai mobile numbers and international +66 landline/mobile numbers.  Keep
# this deliberately strict so publication IDs and years are not treated as PII.
PHONE_PATTERN = re.compile(
    r"(?<![\w])(?:"
    r"\+66[2-9](?:[ -]?\d){7,8}"
    r"|0[689]\d[ -]?\d{3}[ -]?\d{3,4}"
    r")(?![\w])"
)
CMU_PHONE_NAME_PATTERN = re.compile(
    r"^(?P<name>.+?)(?:\+66[0-9][0-9 ()-]{5,})(?P<email>[A-Za-z0-9._%+-]+@cmu\.ac\.th)$"
)

CMU_PHONE_NAME_IDS = (
    "cmu_1cb97442_7160", "cmu_1d486944_1991", "cmu_1f826650_2245",
    "cmu_21ef9178_8446", "cmu_2745f26b_4268", "cmu_287e8e43_1006",
    "cmu_2a2de574_8728", "cmu_2ef6732a_5450", "cmu_34918c03_3062",
    "cmu_4219f97d_1473", "cmu_4f88ba76_4891", "cmu_5634c958_5188",
    "cmu_58b7a832_1668", "cmu_af2fbb73_5327",
)

ALL_FIELDS_PHONE_SCAN = (
    "full_name_th", "email", "research_interests", "featured_publications",
    "education", "taught_courses", "department", "department_th",
    "faculty", "faculty_th", "role", "profile_url", "scholar_url",
)

MALFORMED_EMAIL_FIXES: dict[str, str | None] = {
    "thaksinuni_facultyofl_visamidtanan_028": None,
    "su_eng_teacher_025": None,
    "su_eng_teacher_063": None,
    "su_eng_teacher_091": None,
    "chulalongk_facultyofv_vasutharamarak_174": None,
    "chula_eng_cp_003": "wiwat@chula.ac.th",
    "ku_agro_wave15_0102": None,
}

# These fields are used only to choose which duplicate OpenAlex row remains the
# canonical row.  Rows are not deleted; losing rows are re-queued by clearing
# their OpenAlex ID.
RICHNESS_FIELDS = (
    "full_name_th",
    "first_name",
    "last_name",
    "email",
    "research_interests",
    "featured_publications",
    "image_url",
    "h_index",
)

DUPLICATE_SELECT = text(
    """
    SELECT id, openalex_id, full_name_th, first_name, last_name, email,
           research_interests, featured_publications, image_url, h_index
    FROM faculties
    WHERE openalex_id IS NOT NULL
      AND openalex_id <> ''
      AND openalex_id <> 'not_indexed'
    ORDER BY openalex_id, id
    """
)

PHONE_SELECT = text(
    "SELECT id, research_interests FROM faculties WHERE id = :id"
)
EMAIL_SELECT = text(
    "SELECT id, email FROM faculties WHERE id = ANY(:ids) ORDER BY id"
)


def has_value(value: Any) -> bool:
    """Return whether a field contains meaningful data, not [] or whitespace."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def richness(row: dict[str, Any]) -> tuple[int, int, int, str]:
    """Rank a duplicate row by completeness, metrics, then text richness."""
    non_null = sum(has_value(row.get(field)) for field in RICHNESS_FIELDS)
    h_index = int(row.get("h_index") or 0)
    interests = row.get("research_interests")
    try:
        interest_length = len(json.dumps(interests, ensure_ascii=False))
    except (TypeError, ValueError):
        interest_length = len(str(interests or ""))
    # Stable final tie-break keeps dry-run and apply deterministic.
    return non_null, h_index, interest_length, str(row.get("id") or "")


def scrub_phone_strings(value: Any) -> tuple[Any, bool]:
    """Recursively remove phone-number patterns from scalar/JSON fields."""
    if isinstance(value, str):
        cleaned = PHONE_PATTERN.sub(" ", value)
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        cleaned = re.sub(r"\s+([,;:)])", r"\1", cleaned)
        cleaned = re.sub(r"([(])\s+", r"\1", cleaned)
        cleaned = cleaned.strip(" ;,|-\t")
        return cleaned, cleaned != value
    if isinstance(value, list):
        changed = False
        cleaned_list = []
        for item in value:
            new_item, item_changed = scrub_phone_strings(item)
            changed = changed or item_changed
            if new_item != "":
                cleaned_list.append(new_item)
        return cleaned_list, changed
    if isinstance(value, dict):
        changed = False
        cleaned_dict = {}
        for key, item in value.items():
            new_item, item_changed = scrub_phone_strings(item)
            cleaned_dict[key] = new_item
            changed = changed or item_changed
        return cleaned_dict, changed
    return value, False


def clean_cmu_name(row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Recover the official CMU email and remove phone/email contamination."""
    if row["id"] not in CMU_PHONE_NAME_IDS or row.get("email") != "ams@cmu.ac.th":
        return row, False
    match = re.search(
        r"\+66[ -]?[0-9][0-9 ()-]{5,}(?P<email>[A-Za-z0-9._%+-]+@cmu\.ac\.th)$",
        row.get("full_name_th") or "",
    )
    if not match:
        return row, False
    cleaned = dict(row)
    cleaned["full_name_th"] = row["full_name_th"][: match.start()].rstrip()
    cleaned["email"] = match.group("email")
    return cleaned, True


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


PRIVACY_SELECT = text(
    """
    SELECT id, full_name_th, email, research_interests, featured_publications,
           education, taught_courses, department, department_th, faculty,
           faculty_th, role, profile_url, scholar_url
    FROM faculties
    """
)

PRIVACY_JSON_FIELDS = {
    "research_interests", "featured_publications", "education", "taught_courses"
}
PRIVACY_TEXT_FIELDS = set(ALL_FIELDS_PHONE_SCAN) - PRIVACY_JSON_FIELDS - {"full_name_th", "email"}


def build_privacy_plan(conn) -> list[dict[str, Any]]:
    """Plan only confirmed phone contamination, not phone-shaped DOI digits.

    A broad regex over publication JSON produces false positives such as DOI
    ``10.1073/pnas.0909097107``.  The audit identified the exact CMU name
    contamination rows and the exact Chula Pharmacy field, so scope the write
    set to those reviewed records.
    """
    reviewed_ids = list(CMU_PHONE_NAME_IDS) + [PHONE_ID]
    actions = []
    for raw in conn.execute(
        text(PRIVACY_SELECT.text + " WHERE id = ANY(:ids)"), {"ids": reviewed_ids}
    ).mappings():
        row = dict(raw)
        row, name_changed = clean_cmu_name(row)
        changes = {}
        if name_changed:
            changes["full_name_th"] = row["full_name_th"]
            changes["email"] = row["email"]
        if row["id"] == PHONE_ID:
            new_value, changed = scrub_phone_strings(row.get("research_interests"))
            if changed:
                changes["research_interests"] = new_value
        if changes:
            actions.append({"id": row["id"], "changes": changes})
    return actions


def build_plan(conn) -> dict[str, Any]:
    privacy_actions = build_privacy_plan(conn)

    email_rows = {
        row["id"]: row["email"]
        for row in conn.execute(
            EMAIL_SELECT, {"ids": list(MALFORMED_EMAIL_FIXES)}
        ).mappings()
    }
    email_actions = []
    for rid, replacement in MALFORMED_EMAIL_FIXES.items():
        before = email_rows.get(rid)
        if before != replacement:
            email_actions.append(
                {"id": rid, "action": "set_email", "replacement": replacement}
            )

    duplicate_rows = list(conn.execute(DUPLICATE_SELECT).mappings())
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in duplicate_rows:
        groups[row["openalex_id"]].append(dict(row))

    duplicate_actions = []
    for openalex_id, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        winner = max(members, key=richness)
        losers = [row for row in members if row["id"] != winner["id"]]
        duplicate_actions.append(
            {
                "openalex_id": openalex_id,
                "keep_id": winner["id"],
                "clear_ids": [row["id"] for row in losers],
                "member_count": len(members),
            }
        )

    return {
        "privacy": privacy_actions,
        "emails": email_actions,
        "duplicate_openalex": duplicate_actions,
        "duplicate_group_count": len(duplicate_actions),
        "duplicate_rows_to_requeue": sum(
            len(action["clear_ids"]) for action in duplicate_actions
        ),
    }


def apply_plan(conn, plan: dict[str, Any], *, dedupe_openalex: bool) -> None:
    for action in plan["privacy"]:
        assignments = []
        params = {"id": action["id"]}
        for field, value in action["changes"].items():
            if field in PRIVACY_JSON_FIELDS:
                assignments.append(f"{field} = CAST(:{field} AS JSON)")
                params[field] = json_text(value)
            else:
                assignments.append(f"{field} = :{field}")
                params[field] = value
        conn.execute(
            text(f"UPDATE faculties SET {', '.join(assignments)} WHERE id = :id"),
            params,
        )

    for action in plan["emails"]:
        conn.execute(
            text("UPDATE faculties SET email = :email WHERE id = :id"),
            {"id": action["id"], "email": MALFORMED_EMAIL_FIXES[action["id"]]},
        )

    if dedupe_openalex:
        for group in plan["duplicate_openalex"]:
            for rid in group["clear_ids"]:
                conn.execute(
                    text("UPDATE faculties SET openalex_id = NULL WHERE id = :id"),
                    {"id": rid},
                )


def write_report(
    plan: dict[str, Any], apply: bool, dedupe_openalex: bool
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "mode": "apply" if apply else "dry-run",
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "privacy": plan["privacy"],
        "emails": plan["emails"],
        "duplicate_openalex": plan["duplicate_openalex"],
        "duplicate_group_count": plan["duplicate_group_count"],
        "duplicate_rows_to_requeue": plan["duplicate_rows_to_requeue"],
        "duplicate_openalex_applied": bool(apply and dedupe_openalex),
    }
    with REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)


def print_summary(plan: dict[str, Any], apply: bool) -> None:
    print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
    print(f"Privacy rows to clean: {len(plan['privacy'])}")
    print(f"Malformed email updates: {len(plan['emails'])}")
    if plan["privacy"]:
        for action in plan["privacy"][:20]:
            print(f"  privacy: {action['id']} -> {', '.join(action['changes'])}")
    if len(plan["privacy"]) > 20:
        print(f"  ... {len(plan['privacy']) - 20} more privacy rows")

    print(
        "Duplicate OpenAlex groups: "
        f"{plan['duplicate_group_count']} "
        f"({plan['duplicate_rows_to_requeue']} rows re-queued)"
    )
    print(f"Audit report: {REPORT_PATH}")
    if not apply:
        print("No database changes made. Re-run with --apply to commit this exact plan.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="commit the planned updates")
    parser.add_argument(
        "--dedupe-openalex",
        action="store_true",
        help="also clear duplicate OpenAlex IDs; disabled by default because cross-university collisions need review",
    )
    args = parser.parse_args()

    # engine.begin() gives dry-run a read-only connection in practice because
    # build_plan only issues SELECTs; apply uses one atomic transaction.
    with engine.begin() as conn:
        plan = build_plan(conn)
        if args.apply:
            apply_plan(conn, plan, dedupe_openalex=args.dedupe_openalex)

    write_report(plan, args.apply, args.dedupe_openalex)
    print_summary(plan, args.apply)
    if args.apply and not args.dedupe_openalex:
        print("OpenAlex dedupe skipped; use --dedupe-openalex only after collision review.")


if __name__ == "__main__":
    main()
