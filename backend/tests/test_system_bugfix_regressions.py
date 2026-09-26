# -*- coding: utf-8 -*-
"""DB-free regressions for the 2026-09-26 system bug sweep."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api import routes_career_quiz, routes_labs
from app.api.routes_courses import TH_SLANG_MAP, normalize_query_slang
from app.core.embedding_service import embedding_service
from app.core.security import RateLimiter, _client_ip, sanitize_for_prompt
from app.models.schema import LabSearchRequest


def test_lab_search_empty_query_passes_plain_none_search(monkeypatch):
    """search_labs called list_labs without `search`, leaking the Query(None) default (-> 500)."""
    captured = {}

    def fake_list_labs(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(routes_labs, "list_labs", fake_list_labs)
    resp = routes_labs.search_labs(LabSearchRequest(query="", university="all"), db=MagicMock())
    assert resp.total_matched == 0
    assert captured["search"] is None


def test_lab_domain_filter_guards_non_array_json():
    assert "jsonb_typeof(research_domains::jsonb) = 'array'" in routes_labs._DOMAIN_FILTER_SQL


def test_career_quiz_passes_key_to_client(monkeypatch):
    """_get_client() was called without its required key -> TypeError swallowed -> LLM never ran."""
    seen = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            return SimpleNamespace(text='{"archetype_title": "X"}')

    def fake_get_client(key):
        seen["key"] = key
        return SimpleNamespace(models=FakeModels())

    monkeypatch.setattr(embedding_service, "_current_key", lambda: "k1")
    monkeypatch.setattr(embedding_service, "_get_client", fake_get_client)
    assert routes_career_quiz._call_gemini_with_retry("prompt") == {"archetype_title": "X"}
    assert seen["key"] == "k1"


def test_embedding_inflight_results_do_not_leak(monkeypatch):
    monkeypatch.setattr(embedding_service, "_do_embed", lambda text, retries, deadline: [0.1] * 768)
    embedding_service._inflight_results.clear()
    for i in range(20):
        embedding_service.get_embedding(f"leak probe query {i}")
    assert embedding_service._inflight_results == {}


def test_slang_normalization_is_idempotent_on_formal_terms():
    for value in set(TH_SLANG_MAP.values()):
        assert normalize_query_slang(value) == value
    assert normalize_query_slang("นิติศาสตร์") == "นิติศาสตร์"
    assert normalize_query_slang("วิทยาการคอมพิวเตอร์") == "วิทยาการคอมพิวเตอร์"
    assert normalize_query_slang("บริหารธุรกิจ") == "บริหารธุรกิจ"
    assert normalize_query_slang("นิติ") == "นิติศาสตร์"
    assert normalize_query_slang("หมอฟัน") == "ทันตแพทยศาสตร์"


def test_dashed_thai_national_id_is_redacted():
    for text in ["1-1234-56789-12-3", "1 1234 56789 12 3", "เลข1234567890123ครับ"]:
        assert "REDACTED" in sanitize_for_prompt(text)
    assert sanitize_for_prompt("ปี 2567 หน่วยกิต 36") == "ปี 2567 หน่วยกิต 36"


def _req(headers, peer="10.0.0.9"):
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=peer))


def test_client_ip_ignores_spoofed_forwarded_for():
    # nginx: X-Real-IP = $remote_addr, X-Forwarded-For = <client-supplied>, <remote_addr>
    req = _req({"X-Real-IP": "203.0.113.7", "X-Forwarded-For": "6.6.6.6, 203.0.113.7"})
    assert _client_ip(req) == "203.0.113.7"
    assert _client_ip(_req({"X-Forwarded-For": "6.6.6.6, 198.51.100.2"})) == "198.51.100.2"
    assert _client_ip(_req({})) == "10.0.0.9"


def test_rate_limiter_caps_tracked_ips():
    limiter = RateLimiter(requests_per_minute=5, max_tracked_ips=100)
    for i in range(1000):
        limiter.is_allowed(f"10.1.{i // 256}.{i % 256}")
    assert len(limiter.records) <= 100
