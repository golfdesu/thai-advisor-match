from app.api.routes_faculty import load_faculty_data
from app.core.embedding_service import embedding_service


def test_faculty_loading():
    faculty = load_faculty_data()
    assert len(faculty) >= 19
    print(f"Loaded {len(faculty)} faculty members successfully.")


def test_semantic_matching():
    faculty = load_faculty_data()
    
    # Test query 1: Microgrids & EV
    query = "ไมโครกริดและยานยนต์ไฟฟ้า พลังงานหมุนเวียน"
    results = embedding_service.rank_faculty(query, faculty, top_k=3)
    assert len(results) > 0
    top_match = results[0]
    print(f"\nQuery: '{query}' -> Top Match: {top_match.faculty.full_name_th} ({top_match.match_score}%)")
    print(f"Explanation: {top_match.ai_explanation}")
    assert top_match.match_score > 40.0

    # Test query 2: Biomedical & AI
    query2 = "การประมวลผลภาพทางการแพทย์ และ ปัญญาประดิษฐ์ AI"
    results2 = embedding_service.rank_faculty(query2, faculty, top_k=3)
    assert len(results2) > 0
    top_match2 = results2[0]
    print(f"\nQuery: '{query2}' -> Top Match: {top_match2.faculty.full_name_th} ({top_match2.match_score}%)")
    print(f"Explanation: {top_match2.ai_explanation}")
    assert top_match2.match_score > 30.0


if __name__ == "__main__":
    test_faculty_loading()
    test_semantic_matching()
    print("\n All test assertions passed!")
