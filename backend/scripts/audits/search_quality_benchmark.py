# -*- coding: utf-8 -*-
"""
Search-quality benchmark for the semantic advisor matcher (DSA/cyber audit 2026-09-10).

WHY: the off-dictionary Thai recall gap (Thai queries score 53-80 while the English
equivalent scores 92+) was discovered by ad-hoc probing. This makes it a regression
gate: a fixed corpus of (query, expected-domain keywords) pairs, scored on
  * BEST_SCORE   — highest match_score returned (calibration health)
  * TOP1_HIT     — did an advisor whose interests match the topic land at rank 1?
  * TOPK_RECALL  — how many of the top-k results are topic-relevant?
Run against a LIVE backend (it measures the real endpoint, not a reimplementation):
    python backend/scripts/audits/search_quality_benchmark.py                 # both languages
    python backend/scripts/audits/search_quality_benchmark.py --language th   # Thai only
    python backend/scripts/audits/search_quality_benchmark.py --json out.json # machine-diffable
Exit code 1 if any configured floor is breached (usable in CI).
"""
import sys
import io
import json
import time
import argparse
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

API = "http://127.0.0.1:8000/api/v1/search/"

# Each case: a Thai phrasing + the English phrasing of the SAME topic, and the
# lowercase tokens that must appear in an advisor's interests/name/faculty for a
# result to count as on-topic. Deliberately biased toward terms that are NOT in
# THAI_EN_SYNONYMS — that dictionary gap is the thing under test.
CASES = [
    {"topic": "japanese translation", "th": "การแปลภาษาญี่ปุ่น", "en": "Japanese translation studies",
     "must": ["japanese", "日本", "แปล", "ภาษาญี่ปุ่น", "translation"]},
    {"topic": "clinical parasitology", "th": "ปรสิตวิทยาคลินิก", "en": "clinical parasitology",
     "must": ["parasit", "ปรสิต", "tropical", "helminth", "malaria"]},
    {"topic": "infectious disease", "th": "โรคติดเชื้ออุบัติใหม่", "en": "emerging infectious disease",
     "must": ["infect", "โรคติดเชื้อ", "epidemi", "viral", "virus", "disease"]},
    {"topic": "supply chain", "th": "ห่วงโซ่อุปทานและการกระจายสินค้า", "en": "supply chain logistics",
     "must": ["supply chain", "logistic", "โซ่อุปทาน", "โลจิสติก", "procurement"]},
    {"topic": "archaeology", "th": "โบราณคดีก่อนประวัติศาสตร์", "en": "prehistoric archaeology",
     "must": ["archaeo", "โบราณคดี", "prehistor", "ก่อนประวัติศาสตร์", "excavat"]},
    {"topic": "early childhood ed", "th": "การศึกษาปฐมวัย", "en": "early childhood education",
     "must": ["early childhood", "ปฐมวัย", "preschool", "kindergarten"]},
    {"topic": "constitutional law", "th": "กฎหมายรัฐธรรมนูญ", "en": "constitutional law",
     "must": ["constitutional", "รัฐธรรม", "public law", "law"]},
    {"topic": "geotechnical engineering", "th": "วิศวกรรมปฐพี", "en": "geotechnical engineering",
     "must": ["geotech", "ปฐพี", "soil", "foundation", "slope"]},
    {"topic": "gerontology", "th": "วิทยาการผู้สูงอายุ", "en": "gerontology aging",
     "must": ["geront", "ผู้สูงอายุ", "aging", "elderly"]},
    {"topic": "numerate cognition", "th": "พหุปัญญาและการเรียนรู้คณิตศาสตร์", "en": "mathematics cognition learning",
     "must": ["math", "คณิต", "cognition", "cognitive", "numerac"]},
]

# Floors calibrated from the 2026-09-10 baseline measurement (pre-fix). They exist
# to catch REGRESSION, not to assert perfection: if Thai best-score falls below the
# known-bad baseline mean, or recall collapses, fail loudly.
FLOORS = {"th": {"best": 40.0, "recall": 0.10}, "en": {"best": 85.0, "recall": 0.20}}


def search(query: str, top_k: int = 10, retries: int = 2):
    body = json.dumps({"query": query, "top_k": top_k}).encode()
    last = None
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 429:
                time.sleep(65)
                continue
            raise
        except Exception as e:  # transient connection reset
            last = repr(e)[:80]
            time.sleep(1)
    raise RuntimeError(f"search failed: {last}")


def hay(result) -> str:
    f = result.get("faculty", {})
    parts = [f.get("research_interests") or [], [f.get("full_name_th") or "", f.get("full_name") or ""],
             [f.get("faculty_th") or "", f.get("faculty") or "", f.get("department_th") or ""],
             [p.get("title", "") if isinstance(p, dict) else str(p)
              for p in (f.get("featured_publications") or [])[:8]]]
    out = []
    for p in parts:
        out += p if isinstance(p, list) else [str(p)]
    return " ".join(str(x) for x in out).lower()


def score_case(case, language, top_k):
    q = case[language]
    d = search(q, top_k)
    res = d.get("results", [])
    best = max((r.get("match_score", 0) for r in res), default=0.0)
    hits = [r for r in res if any(tok in hay(r) for tok in case["must"])]
    recall = len(hits) / max(1, len(res))
    top1 = bool(res) and any(tok in hay(res[0]) for tok in case["must"])
    return {"query": q, "best": best, "recall": recall, "top1": top1, "n": len(res)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--language", choices=["th", "en", "both"], default="both")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    langs = ["th", "en"] if args.language == "both" else [args.language]
    rows, failures = {}, []
    for lang in langs:
        print(f"\n===== {lang.upper()} queries =====")
        print(f"  {'topic':<24}{'best':>6}{'top1':>6}{'recall':>8}   query")
        agg_b = agg_r = 0.0
        rows[lang] = []
        for case in CASES:
            # warm both languages first so embedding latency is not the variable
            r = score_case(case, lang, args.top_k)
            rows[lang].append({"topic": case["topic"], **r})
            agg_b += r["best"]; agg_r += r["recall"]
            flag = "" if r["top1"] else "  ✗top1"
            print(f"  {case['topic']:<24}{r['best']:>6.1f}{('✓' if r['top1'] else '✗'):>6}{r['recall']*100:>7.0f}%   {r['query'][:34]}{flag}")
        n = len(CASES)
        mb, mr = agg_b / n, agg_r / n
        fl = FLOORS[lang]
        print(f"  MEAN best={mb:.1f} recall={mr*100:.0f}%  (floors: best≥{fl['best']}, recall≥{fl['recall']*100:.0f}%)")
        if mb < fl["best"]:
            failures.append(f"{lang}: mean best {mb:.1f} < floor {fl['best']}")
        if mr < fl["recall"]:
            failures.append(f"{lang}: mean recall {mr*100:.0f}% < floor {fl['recall']*100:.0f}%")

    # paired gap: the metric the fix should shrink (en best - th best)
    if "th" in rows and "en" in rows:
        gaps = [(e["best"] - t["best"], e["topic"]) for e, t in zip(rows["en"], rows["th"])]
        mean_gap = sum(g for g, _ in gaps) / len(gaps)
        print(f"\n===== TH→EN QUALITY GAP =====\n  mean gap = {mean_gap:+.1f} points "
              f"(negative means Thai outperforms English; closer to 0 is better)")
        for g, topic in sorted(gaps, key=lambda x: -x[0]):
            print(f"  {g:+7.1f}  {topic}")
    else:
        mean_gap = None

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"rows": rows, "mean_gap_th_minus_en": mean_gap, "failures": failures},
                      fh, ensure_ascii=False, indent=1)
        print(f"\nwrote {args.json_out}")

    if failures:
        print("\nFLOORS BREACHED: " + "; ".join(failures))
        sys.exit(1)
    print("\nall floors hold.")


if __name__ == "__main__":
    main()
