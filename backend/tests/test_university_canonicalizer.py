# -*- coding: utf-8 -*-
"""Unit tests for the central university canonicalizer."""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.core.university_canonicalizer import (
    canonicalize_university_en,
    canonicalize_university_th,
    get_university_dedup_key,
)


def test_english_canonicalization_known_aliases():
    assert canonicalize_university_en("Chula") == "Chulalongkorn University"
    assert canonicalize_university_en("chulalongkorn univ.") == "Chulalongkorn University"
    assert canonicalize_university_en("CU") == "Chulalongkorn University"
    assert canonicalize_university_en("KMUTT") == "King Mongkut's University of Technology Thonburi"
    assert canonicalize_university_en("KMITL") == "King Mongkut's Institute of Technology Ladkrabang"
    assert canonicalize_university_en("KMUTNB") == "King Mongkut's University of Technology North Bangkok"
    assert canonicalize_university_en("PSU") == "Prince of Songkla University"
    assert canonicalize_university_en("prince of songkla univ") == "Prince of Songkla University"
    assert canonicalize_university_en("cmu") == "Chiang Mai University"
    assert canonicalize_university_en("Chiang Mai Univ.") == "Chiang Mai University"
    assert canonicalize_university_en("MU") == "Mahidol University"
    assert canonicalize_university_en("TU") == "Thammasat University"
    assert canonicalize_university_en("KKU") == "Khon Kaen University"
    assert canonicalize_university_en("KU") == "Kasetsart University"
    assert canonicalize_university_en("SUT") == "Suranaree University of Technology"
    assert canonicalize_university_en("MFU") == "Mae Fah Luang University"
    assert canonicalize_university_en("NIDA") == "National Institute of Development Administration"


def test_thai_to_english_canonicalization():
    assert canonicalize_university_en("จุฬาลงกรณ์มหาวิทยาลัย") == "Chulalongkorn University"
    assert canonicalize_university_en("มหาวิทยาลัยมหิดล") == "Mahidol University"
    assert canonicalize_university_en("มหาวิทยาลัยเชียงใหม่") == "Chiang Mai University"
    assert canonicalize_university_en("มหาวิทยาลัยเกษตรศาสตร์") == "Kasetsart University"
    assert canonicalize_university_en("มหาวิทยาลัยธรรมศาสตร์") == "Thammasat University"
    assert canonicalize_university_en("สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)") == "National Institute of Development Administration"


def test_english_to_thai_canonicalization():
    assert canonicalize_university_th("Chulalongkorn University") == "จุฬาลงกรณ์มหาวิทยาลัย"
    assert canonicalize_university_th("Chula") == "จุฬาลงกรณ์มหาวิทยาลัย"
    assert canonicalize_university_th("cmu") == "มหาวิทยาลัยเชียงใหม่"
    assert canonicalize_university_th("kmitl") == "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง"


def test_dedup_key_symmetry():
    # All aliases must yield the identical lowercase canonical key
    expected_cu = "chulalongkorn university"
    assert get_university_dedup_key("Chula") == expected_cu
    assert get_university_dedup_key("Chulalongkorn University") == expected_cu
    assert get_university_dedup_key("chulalongkorn univ.") == expected_cu
    assert get_university_dedup_key("cu") == expected_cu
    assert get_university_dedup_key("จุฬาลงกรณ์มหาวิทยาลัย") == expected_cu

    expected_kmutt = "king mongkut's university of technology thonburi"
    assert get_university_dedup_key("KMUTT") == expected_kmutt
    assert get_university_dedup_key("King Mongkut's University of Technology Thonburi") == expected_kmutt
    assert get_university_dedup_key("thonburi") == expected_kmutt


def test_empty_and_unknown_handling():
    assert canonicalize_university_en(None) == ""
    assert canonicalize_university_en("") == ""
    assert canonicalize_university_en("   ") == ""
    assert canonicalize_university_en("Oxford University") == "Oxford University"
    assert get_university_dedup_key(None) == ""
    assert get_university_dedup_key("") == ""
    assert get_university_dedup_key("Oxford University") == "oxford university"
