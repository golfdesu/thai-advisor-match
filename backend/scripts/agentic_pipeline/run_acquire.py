"""
Shorthand CLI Wrapper for SKILL.state Faculty Extraction Agent
Enables fast, low-friction execution of headless data acquisition.
"""
import os
import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup python path to project backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent
from scripts.agentic_pipeline.state_reducer import load_state_checkpoint

UNIVERSITY_MAPPINGS = {
    "cu": ("จุฬาลงกรณ์มหาวิทยาลัย", "Chulalongkorn University"),
    "chula": ("จุฬาลงกรณ์มหาวิทยาลัย", "Chulalongkorn University"),
    "cmu": ("มหาวิทยาลัยเชียงใหม่", "Chiang Mai University"),
    "ku": ("มหาวิทยาลัยเกษตรศาสตร์", "Kasetsart University"),
    "mu": ("มหาวิทยาลัยมหิดล", "Mahidol University"),
    "mahidol": ("มหาวิทยาลัยมหิดล", "Mahidol University"),
    "kku": ("มหาวิทยาลัยขอนแก่น", "Khon Kaen University"),
    "kmitl": ("สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "King Mongkut's Institute of Technology Ladkrabang"),
    "kmutt": ("มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี", "King Mongkut's University of Technology Thonburi"),
    "tu": ("มหาวิทยาลัยธรรมศาสตร์", "Thammasat University"),
    "psu": ("มหาวิทยาลัยสงขลานครินทร์", "Prince of Songkla University"),
    "mfu": ("มหาวิทยาลัยแม่ฟ้าหลวง", "Mae Fah Luang University"),
}

FACULTY_MAPPINGS = {
    "engineering": ("คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    "eng": ("คณะวิศวกรรมศาสตร์", "Faculty of Engineering"),
    "science": ("คณะวิทยาศาสตร์", "Faculty of Science"),
    "sci": ("คณะวิทยาศาสตร์", "Faculty of Science"),
    "medicine": ("คณะแพทยศาสตร์", "Faculty of Medicine"),
    "med": ("คณะแพทยศาสตร์", "Faculty of Medicine"),
    "dentistry": ("คณะทันตแพทยศาสตร์", "Faculty of Dentistry"),
    "dent": ("คณะทันตแพทยศาสตร์", "Faculty of Dentistry"),
    "pharmacy": ("คณะเภสัชศาสตร์", "Faculty of Pharmacy"),
    "pharm": ("คณะเภสัชศาสตร์", "Faculty of Pharmacy"),
    "agriculture": ("คณะเกษตรศาสตร์", "Faculty of Agriculture"),
    "agro": ("คณะอุตสาหกรรมเกษตร", "Faculty of Agro-Industry"),
    "business": ("คณะบริหารธุรกิจ", "Faculty of Business Administration"),
    "law": ("คณะนิติศาสตร์", "Faculty of Law"),
    "economics": ("คณะเศรษฐศาสตร์", "Faculty of Economics"),
    "econ": ("คณะเศรษฐศาสตร์", "Faculty of Economics"),
}


def resolve_metadata(univ_input: str, fac_input: str):
    u_key = univ_input.strip().lower()
    if u_key in UNIVERSITY_MAPPINGS:
        univ_th, univ_en = UNIVERSITY_MAPPINGS[u_key]
    else:
        univ_th = univ_input
        univ_en = univ_input

    f_key = fac_input.strip().lower()
    if f_key in FACULTY_MAPPINGS:
        fac_th, fac_en = FACULTY_MAPPINGS[f_key]
    else:
        fac_th = fac_input
        fac_en = fac_input

    return univ_th, univ_en, fac_th, fac_en


def main():
    parser = argparse.ArgumentParser(description="Fast Shorthand Runner for SKILL.state")
    parser.add_argument("--url", action="append", required=True, help="Target URL to crawl (can specify multiple)")
    parser.add_argument("--univ", type=str, default="CU", help="University shortcut (CU, CMU, KU, MU, KKU, KMITL, KMUTT, TU, PSU, MFU)")
    parser.add_argument("--fac", type=str, default="Engineering", help="Faculty shortcut (Engineering, Science, Medicine, Dentistry, Pharmacy, etc.)")
    parser.add_argument("--max-steps", type=int, default=20, help="Maximum crawl steps")
    parser.add_argument("--resume", type=str, help="Path to checkpoint to resume", default=None)
    parser.add_argument("--no-wiki", action="store_true", help="Disable wiki seeding")

    args = parser.parse_args()

    univ_th, univ_en, fac_th, fac_en = resolve_metadata(args.univ, args.fac)

    print("=================================================================")
    print("🚀 SKILL.state FAST RUNNER")
    print(f"🏛️ University: {univ_th} ({univ_en})")
    print(f"🏢 Faculty:    {fac_th} ({fac_en})")
    print(f"🔗 Target URLs: {len(args.url)}")
    print("=================================================================")

    agent = FacultyExtractionAgent(
        target_university_th=univ_th,
        target_university_en=univ_en,
        target_faculty_th=fac_th,
        target_faculty_en=fac_en,
        max_steps=args.max_steps,
        auto_lookup_wiki=not args.no_wiki
    )

    if args.resume:
        print(f"📂 Resuming from checkpoint: {args.resume}")
        agent.state = load_state_checkpoint(args.resume)
        print(f"   Loaded {len(agent.state.faculties)} existing verified faculties.")

    agent.add_seed_urls(args.url)

    if agent.state.pending_urls:
        print(f"🚀 Starting crawl over {len(agent.state.pending_urls)} URLs...")
        agent.run_crawl_loop()
    else:
        print("ℹ️ No URLs in pending queue.")

    print(f"\n✨ Done! Total verified faculties in state: {len(agent.state.faculties)}")


if __name__ == "__main__":
    main()
