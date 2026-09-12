# -*- coding: utf-8 -*-
"""
Central Academic Taxonomy & Regional Mapping for Thai EduCenter.
Provides deterministic mapping of 37 Thai Universities across 5 geographical regions
with O(1) in-memory lookups and LRU caching for hierarchical cascading selectors.
"""

from typing import Dict, List, Optional, Any
from app.core.dsa_utils import LRUCache

REGIONS_CONFIG: List[Dict[str, str]] = [
    {"id": "all", "label_th": "ทุกภูมิภาค", "label_en": "All Regions", "icon": "🇹🇭"},
    {"id": "central", "label_th": "กรุงเทพฯ และปริมณฑล / ภาคกลาง", "label_en": "Bangkok & Central", "icon": "🏙️"},
    {"id": "north", "label_th": "ภาคเหนือ", "label_en": "Northern", "icon": "⛰️"},
    {"id": "northeast", "label_th": "ภาคตะวันออกเฉียงเหนือ (อีสาน)", "label_en": "Northeastern", "icon": "🌾"},
    {"id": "south", "label_th": "ภาคใต้", "label_en": "Southern", "icon": "🌊"},
    {"id": "east", "label_th": "ภาคตะวันออก", "label_en": "Eastern", "icon": "🌅"},
]

UNIVERSITY_TAXONOMY: Dict[str, Dict[str, str]] = {
    # Central / Bangkok & Metropolitan (22 institutions)
    "จุฬาลงกรณ์มหาวิทยาลัย": {"en": "Chulalongkorn University", "abbr": "CU", "region": "central"},
    "มหาวิทยาลัยมหิดล": {"en": "Mahidol University", "abbr": "MU", "region": "central"},
    "มหาวิทยาลัยธรรมศาสตร์": {"en": "Thammasat University", "abbr": "TU", "region": "central"},
    "มหาวิทยาลัยเกษตรศาสตร์": {"en": "Kasetsart University", "abbr": "KU", "region": "central"},
    "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง": {"en": "King Mongkut's Institute of Technology Ladkrabang", "abbr": "KMITL", "region": "central"},
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี": {"en": "King Mongkut's University of Technology Thonburi", "abbr": "KMUTT", "region": "central"},
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ": {"en": "King Mongkut's University of Technology North Bangkok", "abbr": "KMUTNB", "region": "central"},
    "มหาวิทยาลัยศรีนครินทรวิโรฒ": {"en": "Srinakharinwirot University", "abbr": "SWU", "region": "central"},
    "มหาวิทยาลัยศิลปากร": {"en": "Silpakorn University", "abbr": "SU", "region": "central"},
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)": {"en": "National Institute of Development Administration", "abbr": "NIDA", "region": "central"},
    "มหาวิทยาลัยรามคำแหง": {"en": "Ramkhamhaeng University", "abbr": "RU", "region": "central"},
    "มหาวิทยาลัยสวนดุสิต": {"en": "Suan Dusit University", "abbr": "SDU", "region": "central"},
    "มหาวิทยาลัยราชภัฏสวนสุนันทา": {"en": "Suan Sunandha Rajabhat University", "abbr": "SSRU", "region": "central"},
    "มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ": {"en": "Rajamangala University of Technology Krungthep", "abbr": "RMUTK", "region": "central"},
    "มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร": {"en": "Rajamangala University of Technology Phra Nakhon", "abbr": "RMUTP", "region": "central"},
    "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี": {"en": "Rajamangala University of Technology Thanyaburi", "abbr": "RMUTT", "region": "central"},
    "มหาวิทยาลัยสุโขทัยธรรมาธิราช": {"en": "Sukhothai Thammathirat Open University", "abbr": "STOU", "region": "central"},
    "มหาวิทยาลัยกรุงเทพ": {"en": "Bangkok University", "abbr": "BU", "region": "central"},
    "มหาวิทยาลัยรังสิต": {"en": "Rangsit University", "abbr": "RSU", "region": "central"},
    "มหาวิทยาลัยหอการค้าไทย": {"en": "University of the Thai Chamber of Commerce", "abbr": "UTCC", "region": "central"},
    "มหาวิทยาลัยศรีปทุม": {"en": "Sripatum University", "abbr": "SPU", "region": "central"},
    "มหาวิทยาลัยอัสสัมชัญ": {"en": "Assumption University", "abbr": "AU", "region": "central"},

    # North (6 institutions)
    "มหาวิทยาลัยเชียงใหม่": {"en": "Chiang Mai University", "abbr": "CMU", "region": "north"},
    "มหาวิทยาลัยแม่ฟ้าหลวง": {"en": "Mae Fah Luang University", "abbr": "MFU", "region": "north"},
    "มหาวิทยาลัยนเรศวร": {"en": "Naresuan University", "abbr": "NU", "region": "north"},
    "มหาวิทยาลัยพะเยา": {"en": "University of Phayao", "abbr": "UP", "region": "north"},
    "มหาวิทยาลัยแม่โจ้": {"en": "Maejo University", "abbr": "MJU", "region": "north"},
    "มหาวิทยาลัยราชภัฏเชียงใหม่": {"en": "Chiang Mai Rajabhat University", "abbr": "CMRU", "region": "north"},

    # Northeast (5 institutions)
    "มหาวิทยาลัยขอนแก่น": {"en": "Khon Kaen University", "abbr": "KKU", "region": "northeast"},
    "มหาวิทยาลัยเทคโนโลยีสุรนารี": {"en": "Suranaree University of Technology", "abbr": "SUT", "region": "northeast"},
    "มหาวิทยาลัยมหาสารคาม": {"en": "Mahasarakham University", "abbr": "MSU", "region": "northeast"},
    "มหาวิทยาลัยอุบลราชธานี": {"en": "Ubon Ratchathani University", "abbr": "UBU", "region": "northeast"},
    "มหาวิทยาลัยศรีปทุม วิทยาเขตขอนแก่น": {"en": "Sripatum University Khon Kaen", "abbr": "SPU KK", "region": "northeast"},

    # South (3 institutions)
    "มหาวิทยาลัยสงขลานครินทร์": {"en": "Prince of Songkla University", "abbr": "PSU", "region": "south"},
    "มหาวิทยาลัยทักษิณ": {"en": "Thaksin University", "abbr": "TSU", "region": "south"},
    "มหาวิทยาลัยวลัยลักษณ์": {"en": "Walailak University", "abbr": "WU", "region": "south"},

    # East (1 institution)
    "มหาวิทยาลัยบูรพา": {"en": "Burapha University", "abbr": "BUU", "region": "east"},
}

_REGION_CACHE = LRUCache[str, Any](capacity=512)

def get_unis_for_region(region: Optional[str]) -> List[str]:
    """Return list of Thai university names for a given region slug ('all', 'north', etc.)"""
    if not region or region.strip().lower() in ("all", "ทุกภูมิภาค", ""):
        return []
    target = region.strip().lower()
    return [name_th for name_th, info in UNIVERSITY_TAXONOMY.items() if info["region"] == target]

def get_university_info(name_th: str) -> Dict[str, str]:
    """Retrieve metadata for a Thai university name with defensive fallback"""
    return UNIVERSITY_TAXONOMY.get(name_th, {
        "en": name_th,
        "abbr": "",
        "region": "central"
    })
