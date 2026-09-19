"""Wave26 Batch C verify-only closeout (kmitl_iaai) - 2026-09-17.
Seeds: ['https://iaai.kmitl.ac.th']
Findings: homepage title now 'International Academy of Aviation Industry' (domain repurposed; NO kingsteruni.edu/Bruce Willis markers - demo-template NOT still live). 1 verified: Asst. Prof. Dr. Soemsak Yooyen named as Dean (message-from-the-dean quote author) on official homepage; TH name transliterated. 1 single-token row (news-headline promotion mention) discarded per 2-token rule. Verified count in body: 1 (NO DB commit).
"""
# SKILL.state FacultyExtractionAgent (parity cleanup, session manual)
EXTRACTED_FACULTIES = [
  {
    "id": "kmitl_intacademy_yooyen_002",
    "university": "KMITL",
    "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "faculty": "Int. Academy of AI",
    "faculty_th": "วิทยาลัยปัญญาประดิษฐ์",
    "department": "",
    "department_th": "",
    "academic_title": "ผศ.ดร.",
    "academic_title_th": "ผศ.ดร.",
    "first_name": "Soemsak",
    "last_name": "Yooyen",
    "full_name": "Soemsak Yooyen",
    "full_name_th": "ผศ.ดร. เสริมศักดิ์ อยู่เย็น",
    "role": "อาจารย์ประจำ",
    "email": "",
    "image_url": "",
    "profile_url": "",
    "education": [],
    "research_interests": [],
    "featured_publications": [],
    "scholar_url": "",
    "confidence_score": 0.95
  }
]
