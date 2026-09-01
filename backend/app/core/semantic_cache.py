"""
Zero-Token & Zero-Latency Semantic Caching Service
Powered by PostgreSQL pgvector (Cosine Similarity >= 0.95)
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.db_models import SemanticCacheDB
from app.core.embedding_service import embedding_service
from app.core.dsa_utils import LRUCache

logger = logging.getLogger("semantic_cache")

# Fast In-Memory L1 Cache to avoid database roundtrip for exact/frequent queries
L1_MEMORY_CACHE = LRUCache[str, Dict[str, Any]](capacity=500)


class SemanticCacheService:
    """
    Two-Tier Semantic Caching Engine:
    - Tier 1: In-Memory L1 Hash Map (0.001ms, Exact hit)
    - Tier 2: Supabase PostgreSQL pgvector L2 Semantic Search (1-5ms, Cosine Similarity >= 0.95)
    """

    def __init__(self, similarity_threshold: float = 0.90):
        self.similarity_threshold = similarity_threshold
        # In cosine distance: distance = 1 - similarity. So threshold 0.90 -> max distance 0.10
        self.max_cosine_distance = 1.0 - similarity_threshold

    def get(
        self,
        db: Session,
        cache_type: str,
        query_text: str,
        embedding: Optional[list[float]] = None
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Retrieves cached response if semantic similarity >= threshold.
        Returns: (cached_payload, is_cache_hit)
        """
        if not query_text or not query_text.strip():
            return None, False

        clean_query = query_text.strip().lower()
        l1_key = f"{cache_type}:{clean_query}"

        # 1. Tier 1: Check L1 In-Memory Cache
        l1_hit = L1_MEMORY_CACHE.get(l1_key)
        if l1_hit is not None:
            logger.info(f"⚡ [L1 Memory Cache Hit] {l1_key}")
            return l1_hit, True

        # 2. Tier 2: Check pgvector L2 Semantic Database Cache
        try:
            if embedding is None:
                embedding = embedding_service.get_embedding(query_text)

            if not embedding:
                return None, False

            # Query closest vector in semantic_cache
            # Using cosine distance operator '<=>'
            distance_col = SemanticCacheDB.embedding.cosine_distance(embedding)
            cached_entry = (
                db.query(SemanticCacheDB, distance_col.label("distance"))
                .filter(SemanticCacheDB.cache_type == cache_type)
                .order_by(distance_col.asc())
                .first()
            )

            if cached_entry:
                obj, distance = cached_entry
                if distance is not None and float(distance) <= self.max_cosine_distance:
                    # Semantic Hit!
                    obj.hit_count = (obj.hit_count or 1) + 1
                    obj.updated_at = datetime.utcnow()
                    db.commit()

                    payload = obj.cache_payload
                    # Store back to L1
                    L1_MEMORY_CACHE.put(l1_key, payload)
                    logger.info(f"🎯 [L2 Semantic Cache Hit (Distance: {distance:.4f})] '{query_text}' -> '{obj.query_text}'")
                    return payload, True

        except Exception as e:
            logger.warning(f"Semantic cache lookup failed: {e}")

        return None, False

    def set(
        self,
        db: Session,
        cache_type: str,
        query_text: str,
        payload: Dict[str, Any],
        embedding: Optional[list[float]] = None
    ):
        """Stores query and LLM result into L1 & L2 Semantic Cache."""
        if not query_text or not payload:
            return

        clean_query = query_text.strip()
        l1_key = f"{cache_type}:{clean_query.lower()}"

        # 1. Store to L1
        L1_MEMORY_CACHE.put(l1_key, payload)

        # 2. Store to PostgreSQL pgvector L2
        try:
            if embedding is None:
                embedding = embedding_service.get_embedding(clean_query)

            if not embedding:
                return

            new_cache = SemanticCacheDB(
                id=f"cache_{uuid.uuid4().hex[:12]}",
                cache_type=cache_type,
                query_text=clean_query,
                cache_payload=payload,
                hit_count=1,
                embedding=embedding
            )
            db.add(new_cache)
            db.commit()
            logger.info(f"💾 [Semantic Cache Stored] {cache_type}: '{clean_query[:50]}...'")

        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to persist semantic cache: {e}")


# Global Singleton with 0.90 similarity threshold (distance <= 0.10)
semantic_cache_service = SemanticCacheService(similarity_threshold=0.90)
