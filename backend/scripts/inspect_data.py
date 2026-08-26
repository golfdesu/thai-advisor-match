import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def inspect():
    ku_path = Path("backend/scripts/archive/data/ku_courses.json")
    tu_path = Path("backend/scripts/archive/data/tu_courses.json")
    
    with open(ku_path, "r", encoding="utf-8") as f:
        ku_data = json.load(f)
    with open(tu_path, "r", encoding="utf-8") as f:
        tu_data = json.load(f)
        
    print(f"KU Count: {len(ku_data)}")
    for i, c in enumerate(ku_data, 1):
        print(f"KU {i:02d}: [{c['degree_level']}] {c['faculty_th']} - {c['title_th']} ({c['id']})")
        
    print(f"\nTU Count: {len(tu_data)}")
    for i, c in enumerate(tu_data, 1):
        print(f"TU {i:02d}: [{c['degree_level']}] {c['faculty_th']} - {c['title_th']} ({c['id']})")

if __name__ == "__main__":
    inspect()
