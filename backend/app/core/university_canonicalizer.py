# -*- coding: utf-8 -*-
"""
Central English & Thai University Canonicalization Utility

Provides deterministic canonicalization of university names, abbreviations,
acronyms, and aliases across Thai EduCenter & Advisor Match.
Guarantees deduplication symmetry: records referring to the same institution
via different aliases (e.g. "Chula", "Chulalongkorn Univ.", "KMUTT", "PSU")
map to the exact same canonical representation.
"""
from __future__ import annotations

import re

# Canonical English -> Canonical Thai mapping
CANONICAL_EN_TO_TH: dict[str, str] = {
    "Chulalongkorn University": "จุฬาลงกรณ์มหาวิทยาลัย",
    "Mahidol University": "มหาวิทยาลัยมหิดล",
    "Kasetsart University": "มหาวิทยาลัยเกษตรศาสตร์",
    "Chiang Mai University": "มหาวิทยาลัยเชียงใหม่",
    "Thammasat University": "มหาวิทยาลัยธรรมศาสตร์",
    "Khon Kaen University": "มหาวิทยาลัยขอนแก่น",
    "Prince of Songkla University": "มหาวิทยาลัยสงขลานครินทร์",
    "King Mongkut's Institute of Technology Ladkrabang": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
    "King Mongkut's University of Technology Thonburi": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
    "King Mongkut's University of Technology North Bangkok": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
    "Suranaree University of Technology": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
    "Naresuan University": "มหาวิทยาลัยนเรศวร",
    "Srinakharinwirot University": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "Silpakorn University": "มหาวิทยาลัยศิลปากร",
    "Burapha University": "มหาวิทยาลัยบูรพา",
    "Ubon Ratchathani University": "มหาวิทยาลัยอุบลราชธานี",
    "University of Phayao": "มหาวิทยาลัยพะเยา",
    "Maejo University": "มหาวิทยาลัยแม่โจ้",
    "Walailak University": "มหาวิทยาลัยวลัยลักษณ์",
    "Mae Fah Luang University": "มหาวิทยาลัยแม่ฟ้าหลวง",
    "Mahasarakham University": "มหาวิทยาลัยมหาสารคาม",
    "Thaksin University": "มหาวิทยาลัยทักษิณ",
    "Ramkhamhaeng University": "มหาวิทยาลัยรามคำแหง",
    "Suan Sunandha Rajabhat University": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
    "Suan Dusit University": "มหาวิทยาลัยสวนดุสิต",
    "National Institute of Development Administration": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
    "Bangkok University": "มหาวิทยาลัยกรุงเทพ",
    "Assumption University": "มหาวิทยาลัยอัสสัมชัญ",
    "Rangsit University": "มหาวิทยาลัยรังสิต",
    "Sripatum University": "มหาวิทยาลัยศรีปทุม",
    "Sukhothai Thammathirat Open University": "มหาวิทยาลัยสุโขทัยธรรมาธิราช",
    "Rajamangala University of Technology Thanyaburi": "มหาวิทยาลัยเทคโนโลยีราชมงคลธัญบุรี",
    "Rajamangala University of Technology Krungthep": "มหาวิทยาลัยเทคโนโลยีราชมงคลกรุงเทพ",
    "Rajamangala University of Technology Phra Nakhon": "มหาวิทยาลัยเทคโนโลยีราชมงคลพระนคร",
    "University of the Thai Chamber of Commerce": "มหาวิทยาลัยหอการค้าไทย",
    "Chiang Mai Rajabhat University": "มหาวิทยาลัยราชภัฏเชียงใหม่",
}

CANONICAL_TH_TO_EN: dict[str, str] = {
    v: k for k, v in CANONICAL_EN_TO_TH.items()
}
# Additional common Thai name variants
CANONICAL_TH_TO_EN["สถาบันบัณฑิตพัฒนบริหารศาสตร์"] = "National Institute of Development Administration"
CANONICAL_TH_TO_EN["นิด้า"] = "National Institute of Development Administration"
CANONICAL_TH_TO_EN["จุฬาฯ"] = "Chulalongkorn University"
CANONICAL_TH_TO_EN["ม.เกษตร"] = "Kasetsart University"
CANONICAL_TH_TO_EN["ม.เชียงใหม่"] = "Chiang Mai University"
CANONICAL_TH_TO_EN["ม.มหิดล"] = "Mahidol University"
CANONICAL_TH_TO_EN["ม.ธรรมศาสตร์"] = "Thammasat University"
CANONICAL_TH_TO_EN["มช."] = "Chiang Mai University"
CANONICAL_TH_TO_EN["มช"] = "Chiang Mai University"
CANONICAL_TH_TO_EN["มข."] = "Khon Kaen University"
CANONICAL_TH_TO_EN["มข"] = "Khon Kaen University"
CANONICAL_TH_TO_EN["มศว"] = "Srinakharinwirot University"
CANONICAL_TH_TO_EN["มศว."] = "Srinakharinwirot University"
CANONICAL_TH_TO_EN["มจธ"] = "King Mongkut's University of Technology Thonburi"
CANONICAL_TH_TO_EN["มจธ."] = "King Mongkut's University of Technology Thonburi"
CANONICAL_TH_TO_EN["สจล"] = "King Mongkut's Institute of Technology Ladkrabang"
CANONICAL_TH_TO_EN["สจล."] = "King Mongkut's Institute of Technology Ladkrabang"
CANONICAL_TH_TO_EN["มจพ"] = "King Mongkut's University of Technology North Bangkok"
CANONICAL_TH_TO_EN["มจพ."] = "King Mongkut's University of Technology North Bangkok"
CANONICAL_TH_TO_EN["มอ"] = "Prince of Songkla University"
CANONICAL_TH_TO_EN["มอ."] = "Prince of Songkla University"
CANONICAL_TH_TO_EN["มทส"] = "Suranaree University of Technology"
CANONICAL_TH_TO_EN["มทส."] = "Suranaree University of Technology"
CANONICAL_TH_TO_EN["มน"] = "Naresuan University"
CANONICAL_TH_TO_EN["มน."] = "Naresuan University"
CANONICAL_TH_TO_EN["มมส"] = "Mahasarakham University"
CANONICAL_TH_TO_EN["มมส."] = "Mahasarakham University"


def _normalize_key(s: str) -> str:
    """Strip punctuation and collapse whitespace for alias lookup."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s฀-๿]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# Normalized alias dictionary mapping to Canonical English Name
_RAW_ALIASES: dict[str, list[str]] = {
    "Chulalongkorn University": [
        "cu", "chula", "chulalongkorn", "chulalongkorn univ", "chulalongkorn univ.",
        "chulalongkorn u", "chulalongkorn university", "chula university",
    ],
    "Mahidol University": [
        "mu", "mahidol", "mahidol univ", "mahidol univ.", "mahidol u",
        "mahidol university",
    ],
    "Kasetsart University": [
        "ku", "kasetsart", "kasetsart univ", "kasetsart univ.", "kasetsart u",
        "kasetsart university",
    ],
    "Chiang Mai University": [
        "cmu", "chiang mai", "chiangmai", "chiang mai univ", "chiang mai univ.",
        "chiang mai u", "chiang mai university",
    ],
    "Thammasat University": [
        "tu", "thammasat", "thammasat univ", "thammasat univ.", "thammasat u",
        "thammasat university",
    ],
    "Khon Kaen University": [
        "kku", "khon kaen", "khonkaen", "khon kaen univ", "khon kaen univ.",
        "khon kaen university",
    ],
    "Prince of Songkla University": [
        "psu", "prince of songkla", "prince of songkhla", "prince of songkla univ",
        "prince of songkla univ.", "prince of songkla university",
        "prince of songkhla university", "songkla university",
    ],
    "King Mongkut's Institute of Technology Ladkrabang": [
        "kmitl", "ladkrabang", "king mongkut ladkrabang", "kmit ladkrabang",
        "king mongkuts institute of technology ladkrabang",
        "king mongkut's institute of technology ladkrabang",
    ],
    "King Mongkut's University of Technology Thonburi": [
        "kmutt", "thonburi", "king mongkut thonburi", "kmut thonburi",
        "king mongkuts university of technology thonburi",
        "king mongkut's university of technology thonburi",
    ],
    "King Mongkut's University of Technology North Bangkok": [
        "kmutnb", "north bangkok", "king mongkut north bangkok", "kmut north bangkok",
        "king mongkuts university of technology north bangkok",
        "king mongkut's university of technology north bangkok",
    ],
    "Suranaree University of Technology": [
        "sut", "suranaree", "suranaree univ", "suranaree univ.",
        "suranaree university of technology", "suranaree university",
    ],
    "Naresuan University": [
        "nu", "naresuan", "naresuan univ", "naresuan univ.", "naresuan university",
    ],
    "Srinakharinwirot University": [
        "swu", "srinakharinwirot", "srinakharinwirot univ", "srinakharinwirot univ.",
        "srinakharinwirot university",
    ],
    "Silpakorn University": [
        "su", "silpakorn", "silpakorn univ", "silpakorn univ.", "silpakorn university",
    ],
    "Burapha University": [
        "buu", "burapha", "burapha univ", "burapha univ.", "burapha university",
    ],
    "Ubon Ratchathani University": [
        "ubu", "ubon ratchathani", "ubon ratchathani univ", "ubon ratchathani univ.",
        "ubon ratchathani university", "ubon university",
    ],
    "University of Phayao": [
        "up", "phayao", "university of phayao", "phayao univ", "phayao univ.",
        "phayao university",
    ],
    "Maejo University": [
        "mju", "maejo", "maejo univ", "maejo univ.", "maejo university",
    ],
    "Walailak University": [
        "wu", "walailak", "walailak univ", "walailak univ.", "walailak university",
    ],
    "Mae Fah Luang University": [
        "mfu", "mae fah luang", "maefahluang", "mae fah luang univ",
        "mae fah luang univ.", "mae fah luang university",
    ],
    "Mahasarakham University": [
        "msu", "mahasarakham", "mahasarakham univ", "mahasarakham univ.",
        "mahasarakham university",
    ],
    "Thaksin University": [
        "tsu", "thaksin", "thaksin univ", "thaksin univ.", "thaksin university",
    ],
    "Ramkhamhaeng University": [
        "ru", "ramkhamhaeng", "ramkhamhaeng univ", "ramkhamhaeng univ.",
        "ramkhamhaeng university",
    ],
    "Suan Sunandha Rajabhat University": [
        "ssru", "suan sunandha", "suan sunandha rajabhat", "suan sunandha univ",
        "suan sunandha rajabhat university",
    ],
    "Suan Dusit University": [
        "sdu", "suan dusit", "suan dusit univ", "suan dusit univ.", "suan dusit university",
    ],
    "National Institute of Development Administration": [
        "nida", "national institute of development administration",
    ],
    "Bangkok University": [
        "bu", "bangkok univ", "bangkok univ.", "bangkok university",
    ],
    "Assumption University": [
        "au", "abac", "assumption", "assumption univ", "assumption univ.",
        "assumption university",
    ],
    "Rangsit University": [
        "rsu", "rangsit", "rangsit univ", "rangsit univ.", "rangsit university",
    ],
    "Sripatum University": [
        "spu", "sripatum", "sripatum univ", "sripatum univ.", "sripatum university",
    ],
    "Sukhothai Thammathirat Open University": [
        "stou", "sukhothai thammathirat", "sukhothai thammathirat open university",
    ],
    "Rajamangala University of Technology Thanyaburi": [
        "rmutt", "thanyaburi", "rajamangala university of technology thanyaburi",
    ],
    "Rajamangala University of Technology Krungthep": [
        "rmutk", "krungthep", "rajamangala university of technology krungthep",
    ],
    "Rajamangala University of Technology Phra Nakhon": [
        "rmutp", "phra nakhon", "rajamangala university of technology phra nakhon",
    ],
    "University of the Thai Chamber of Commerce": [
        "utcc", "thai chamber of commerce", "university of the thai chamber of commerce",
    ],
    "Chiang Mai Rajabhat University": [
        "cmru", "chiang mai rajabhat", "chiang mai rajabhat university",
    ],
}

# Compiled lookup dictionary: normalized key -> Canonical English Name
ALIAS_LOOKUP: dict[str, str] = {}
for canonical_en, aliases in _RAW_ALIASES.items():
    ALIAS_LOOKUP[_normalize_key(canonical_en)] = canonical_en
    for alias in aliases:
        ALIAS_LOOKUP[_normalize_key(alias)] = canonical_en

# Also inject Thai canonical names
for th_name, en_name in CANONICAL_TH_TO_EN.items():
    ALIAS_LOOKUP[_normalize_key(th_name)] = en_name


def canonicalize_university_en(name: str | None) -> str:
    """Return the official canonical English name for any recognized university alias.

    If unrecognized or None, returns stripped original name or empty string.
    """
    if not name:
        return ""
    norm = _normalize_key(name)
    if norm in ALIAS_LOOKUP:
        return ALIAS_LOOKUP[norm]
    # Check direct canonical EN
    for canonical in CANONICAL_EN_TO_TH:
        if canonical.lower() == name.strip().lower():
            return canonical
    return name.strip()


def canonicalize_university_th(name: str | None) -> str:
    """Return the official canonical Thai name for any recognized university alias.

    If unrecognized or None, returns stripped original name or empty string.
    """
    if not name:
        return ""
    en = canonicalize_university_en(name)
    if en in CANONICAL_EN_TO_TH:
        return CANONICAL_EN_TO_TH[en]
    return name.strip()


def get_university_dedup_key(name: str | None) -> str:
    """Return a normalized canonical lowercase string for deduplication keys.

    Guarantees that "Chula", "Chulalongkorn Univ.", "จุฬาลงกรณ์มหาวิทยาลัย",
    and "Chulalongkorn University" all map to the exact same key.
    """
    if not name:
        return ""
    canonical_en = canonicalize_university_en(name)
    return canonical_en.strip().lower()
