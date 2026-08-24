import json
from pathlib import Path
from app.scrapers.cmu.ee_scraper import CMUElectricalEngineeringScraper


def main():
    print("Starting CMU Electrical Engineering Faculty Scraper...")
    scraper = CMUElectricalEngineeringScraper()
    members = scraper.scrape()
    print(f"Scraped {len(members)} faculty members.")

    output_path = Path(__file__).resolve().parent.parent.parent.parent / "cmu_ee_faculty.json"
    
    data = {
        "university": scraper.university_name,
        "university_th": scraper.university_name_th,
        "faculty": scraper.faculty_name,
        "faculty_th": scraper.faculty_name_th,
        "department": scraper.department_name,
        "department_th": scraper.department_name_th,
        "source_url": scraper.FACULTY_LIST_URL,
        "total_members": len(members),
        "members": [m.model_dump() for m in members]
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved enriched data to {output_path}")


if __name__ == "__main__":
    main()
