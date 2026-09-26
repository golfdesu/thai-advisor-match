# -*- coding: utf-8 -*-
"""
Phase 2 — email recovery batch runner (SKILL.state engine, 2026-09-26).

Runs cli_runner.py headlessly over a JSON target list (one faculty directory per entry) with a
ThreadPoolExecutor, exporting each extraction to backend/data/agent_states/phase2/<key>.py.
Targets whose export already exists are skipped (disk-checkpoint resumability).
Emails are written to the DB afterwards by scripts/audits/reconcile_phase2_emails.py.

Usage:
    python backend/scripts/agentic_pipeline/run_phase2_email_recovery.py \
        --targets backend/data/agent_states/phase2/targets_swu.json --workers 5 --max-steps 12
"""
import os
import sys
import json
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "backend" / "scripts" / "agentic_pipeline" / "cli_runner.py"
OUT_DIR = ROOT / "backend" / "data" / "agent_states" / "phase2"


def run_target(t: dict, max_steps: int) -> str:
    out = OUT_DIR / f"{t['key']}.py"
    if out.exists():
        return f"{t['key']}: checkpoint exists, skipped"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "backend"), "PYTHONIOENCODING": "utf-8"}
    cmd = [sys.executable, str(CLI), "--univ-th", t["univ_th"], "--univ-en", t["univ_en"],
           "--faculty-th", t["faculty_th"], "--faculty-en", t["faculty_en"],
           "--export-file", str(out), "--max-steps", str(max_steps), "--no-wiki"]
    for u in t["urls"]:
        cmd += ["--url", u]
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=1800)
    except subprocess.TimeoutExpired:
        return f"{t['key']}: timeout"
    if res.returncode != 0:
        return f"{t['key']}: error {res.stderr.strip().splitlines()[-1][:200] if res.stderr.strip() else res.returncode}"
    total = next((l.split(":")[-1].strip() for l in res.stdout.splitlines() if "Total verified" in l), "?")
    return f"{t['key']}: {total} profiles"


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 2 email recovery batch runner")
    ap.add_argument("--targets", required=True)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--max-steps", type=int, default=12)
    args = ap.parse_args()
    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for line in ex.map(lambda t: run_target(t, args.max_steps), targets):
            print(line, flush=True)


if __name__ == "__main__":
    main()
