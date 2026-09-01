"""
CLI Runner for SKILL.state Faculty Extraction Agent
Based on the SKILL.state Architecture & Evaluation: https://arxiv.org/html/2608.26263v2#S5
"""
import os
import sys
import argparse

# Setup python path to project backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.agentic_pipeline.faculty_agent import FacultyExtractionAgent
from scripts.agentic_pipeline.state_reducer import load_state_checkpoint


def main():
    parser = argparse.ArgumentParser(description="SKILL.state Autonomous Faculty Extraction & Cleaning Agent")
    parser.add_argument("--univ-th", type=str, default="สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", help="University Thai Name")
    parser.add_argument("--univ-en", type=str, default="King Mongkut's Institute of Technology Ladkrabang", help="University EN Name")
    parser.add_argument("--faculty-th", type=str, default="คณะวิศวกรรมศาสตร์", help="Faculty Thai Name")
    parser.add_argument("--faculty-en", type=str, default="School of Engineering", help="Faculty EN Name")
    parser.add_argument("--url", action="append", help="Target seed URL(s) to crawl", default=[])
    parser.add_argument("--resume", type=str, help="Path to checkpoint JSON to resume")
    parser.add_argument("--export-file", type=str, help="Path to save Python dataset", default=None)
    parser.add_argument("--max-steps", type=int, default=20, help="Maximum steps to crawl")

    args = parser.parse_args()

    print("=================================================================")
    print("🤖 SKILL.state AUTONOMOUS FACULTY EXTRACTION AGENT")
    print("=================================================================")

    agent = FacultyExtractionAgent(
        target_university_th=args.univ_th,
        target_university_en=args.univ_en,
        target_faculty_th=args.faculty_th,
        target_faculty_en=args.faculty_en,
        max_steps=args.max_steps
    )

    if args.resume:
        print(f"📂 Resuming session from checkpoint: {args.resume}")
        agent.state = load_state_checkpoint(args.resume)
        print(f"   Loaded {len(agent.state.faculties)} existing verified faculties.")

    if args.url:
        agent.add_seed_urls(args.url)

    if agent.state.pending_urls:
        print(f"🚀 Starting crawl over {len(agent.state.pending_urls)} URLs...")
        agent.run_crawl_loop()
    else:
        print("ℹ️ No URLs in pending queue. Use --url to specify seed URLs.")

    print(f"\n✨ Completed! Total verified faculties in state: {len(agent.state.faculties)}")

    if args.export_file:
        code = agent.export_as_dataset_python()
        os.makedirs(os.path.dirname(os.path.abspath(args.export_file)), exist_ok=True)
        with open(args.export_file, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"💾 Dataset exported to: {args.export_file}")


if __name__ == "__main__":
    main()
