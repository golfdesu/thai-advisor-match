# -*- coding: utf-8 -*-
"""
Audit every data_sources dataset for records whose official email domain
contradicts the recorded university (legacy copy-paste mislabels).

Read-only. Reports file:line so the source dataset can be corrected at the
single source of truth (otherwise a re-ingest restores the wrong value).
"""
import sys
import os
import re
import json
import importlib.util

sys.stdout.reconfigure(encoding="utf-8")

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS_DIR = os.path.join(SCRIPTS_DIR, "data_sources")

# official.ac.th email domain -> canonical Thai university name
DOMAIN_TO_UNIV = {
    "tsu.ac.th": "มหาวิทยาลัยทักษิณ",
    "ubu.ac.th": "มหาวิทยาลัยอุบลราชธานี",
    "msu.ac.th": "มหาวิทยาลัยมหาสารคาม",
    "up.ac.th": "มหาวิทยาลัยพะเยา",
    "ku.ac.th": "มหาวิทยาลัยเกษตรศาสตร์",
    "cmu.ac.th": "มหาวิทยาลัยเชียงใหม่",
    "mu.mahidol.ac.th": "มหาวิทยาลัยมหิดล",
    "mahidol.ac.th": "มหาวิทยาลัยมหิดล",
    "chula.ac.th": "จุฬาลงกรณ์มหาวิทยาลัย",
    "tu.ac.th": "มหาวิทยาลัยธรรมศาสตร์",
    "kku.ac.th": "มหาวิทยาลัยขอนแก่น",
    "psu.ac.th": "มหาวิทยาลัยสงขลานครินทร์",
    "kmitl.ac.th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "kmutt.ac.th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "kmutnb.ac.th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
    "sut.ac.th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
    "buu.ac.th": "มหาวิทยาลัยบูรพา",
    "mfu.ac.th": "มหาวิทยาลัยแม่ฟ้าหลวง",
    "mju.ac.th": "มหาวิทยาลัยแม่โจ้",
    "nu.ac.th": "มหาวิทยาลัยนเรศวร",
    "swu.ac.th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "su.ac.th": "มหาวิทยาลัยศิลปากร",
}

RECORD_RE = re.compile(r"\{[^{}]*?\"id\":\s*\"(?P<id>[^\"]+)\".*?\}", re.DOTALL)
EMAIL_RE = re.compile(r"\"email\":\s*\"([^\"]+)\"")
UNIV_RE = re.compile(r"\"university_th\":\s*\"([^\"]+)\"")
NAME_RE = re.compile(r"\"full_name_th\":\s*\"([^\"]+)\"")


def scan_file(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    hits = []
    for chunk in RECORD_RE.finditer(raw):
        text = chunk.group(0)
        em = EMAIL_RE.search(text)
        if not em:
            continue
        domain = em.group(1).split("@")[-1].strip().lower()
        expect = DOMAIN_TO_UNIV.get(domain)
        if not expect:
            continue
        got_m = UNIV_RE.search(text)
        got = got_m.group(1) if got_m else ""
        if got != expect:
            line = raw[: chunk.start()].count("\n") + 1
            nm = NAME_RE.search(text)
            hits.append((line, chunk.group("id"), nm.group(1) if nm else "",
                         em.group(1), got or "<missing>"))
    return hits


def main():
    total = 0
    for fn in sorted(os.listdir(DS_DIR)):
        if not fn.endswith(".py") or fn.startswith("__"):
            continue
        hits = scan_file(os.path.join(DS_DIR, fn))
        if hits:
            print(f"\n### {fn}  ({len(hits)} mismatch)")
            for h in hits:
                print(f"  L{h[0]:<6} {h[1]:<42} {h[2]:<28} {h[3]:<26} says={h[4]}")
            total += len(hits)
    print(f"\nTOTAL mismatched records across data_sources: {total}")


if __name__ == "__main__":
    main()
