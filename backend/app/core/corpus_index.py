"""
Startup-built in-memory lexical index over the faculty corpus (AGENTS.md §5.2
"Fast Inverted Index … sub-millisecond lexical fallback" — previously the class
existed in dsa_utils but was never instantiated; DSA audit 2026-09-10).

Design decisions (from the hybrid-search research pass):
- Corpus = faculties.embedding_text (interests + publications + dept labels, the
  same text the stored vectors were built from), so lexical and dense scores rank
  the same evidence.
- Tokenizer: whitespace tokens for ASCII runs (English already word-segmented),
  character BIGRAMS for Thai runs (no spaces between words; bigrams catch
  วิทยา within วิทยาการข้อมูล without a pythainlp dependency).
- Scoring: Okapi BM25 (fixed IDF in dsa_utils; true corpus avgdl captured at build).
- Consumers: routes_search feeds a capped lexical bonus into the composite score
  (hybrid dense+lexical). RRF fusion is the researched next step — deliberately
  NOT applied yet: the additive composite with calibrated bonuses currently
  outperforms (Thai mean best 72.2 → 93.1 after the synonym expansion), and the
  benchmark floors must keep holding after any fusion swap.
"""
import logging
import re

from sqlalchemy.orm import load_only

from app.core.dsa_utils import ThreadSafeInvertedIndex
from app.models.db_models import FacultyDB

logger = logging.getLogger("corpus_index")

# Shared by build-time (documents) and query-time — MUST stay symmetric or
# query tokens would never match posting-list keys.
_THAI_RUN = re.compile(r"[฀-๿]+")
_ASCII_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-\.]*")


def tokenize_mixed(text: str) -> list[str]:
    """Whitespace tokens for latin/digits; character bigrams for Thai runs."""
    tokens: list[str] = []
    for tok in _ASCII_TOKEN.findall(text):
        if len(tok) >= 2:
            tokens.append(tok.lower())
    for run in _THAI_RUN.findall(text):
        if len(run) == 1:
            continue
        # bigrams cover 2-char roots; a unigram would be pure noise, so minimum 2 chars
        tokens.extend(run[i:i + 2] for i in range(len(run) - 1))
    return tokens


# Singleton shared by the startup loader and all request handlers.
FACULTY_LEXICAL_INDEX = ThreadSafeInvertedIndex()


def build_faculty_lexical_index(session_factory) -> int:
    """Load faculty corpus text and (re)build the shared index. Returns doc count.

    Called from FastAPI's startup lifespan; also exposed for tests/scripts.
    Failure is logged, never raised — search must keep working dense-only.
    """
    try:
        db = session_factory()
        try:
            rows = (
                db.query(FacultyDB)
                .options(load_only(FacultyDB.id, FacultyDB.embedding_text))
                .filter(FacultyDB.embedding_text.isnot(None))
                .all()
            )
            docs = {r.id: (r.embedding_text or "") for r in rows}
        finally:
            db.close()
        n = FACULTY_LEXICAL_INDEX.rebuild(docs, tokenizer=tokenize_mixed)
        logger.info(f"📚 [Corpus Index] lexical BM25 index built over {n} faculty docs")
        return n
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Corpus lexical index build failed (dense-only scoring continues): {e}")
        return 0
