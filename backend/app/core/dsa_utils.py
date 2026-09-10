"""
Advanced Data Structures and Algorithms (DSA) Engine for Thai EduCenter:
1. LRUCache (Doubly Linked List + Hash Map) for O(1) Vector Caching
2. Trie (Prefix Tree) for Substring & Keyword Multi-Pattern Matching
3. TopKMinHeap for Optimal Top-K Elements Selection (O(N log K) instead of O(N log N))
4. InvertedIndex for Fast Multi-Token In-Memory Intersections & Search Scoring
"""

import threading
import math
from typing import TypeVar, Generic, Optional, Dict, List, Tuple, Any, Iterator, Callable
import heapq

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")


class _LRUNode(Generic[K, V]):
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key: K, val: V):
        self.key: K = key
        self.val: V = val
        self.prev: Optional["_LRUNode[K, V]"] = None
        self.next: Optional["_LRUNode[K, V]"] = None


class LRUCache(Generic[K, V]):
    """
    Thread-safe true O(1) LRU Cache using a Doubly Linked List and Hash Map.
    Guarantees strict O(1) time complexity for get(), put(), and eviction.
    """

    def __init__(self, capacity: int = 2048):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self.map: Dict[K, _LRUNode[K, V]] = {}
        self.lock = threading.Lock()

        # Sentinel pseudo head and tail nodes
        self.head = _LRUNode(None, None)  # type: ignore
        self.tail = _LRUNode(None, None)  # type: ignore
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: _LRUNode[K, V]) -> None:
        """Remove an existing node from the linked list in O(1)."""
        prev_node = node.prev
        next_node = node.next
        if prev_node:
            prev_node.next = next_node
        if next_node:
            next_node.prev = prev_node

    def _add_to_head(self, node: _LRUNode[K, V]) -> None:
        """Insert a node right after the head sentinel (Most Recently Used) in O(1)."""
        node.next = self.head.next
        node.prev = self.head
        if self.head.next:
            self.head.next.prev = node
        self.head.next = node

    def get(self, key: K) -> Optional[V]:
        """Fetch value by key in O(1) and move node to head."""
        with self.lock:
            if key not in self.map:
                return None
            node = self.map[key]
            self._remove(node)
            self._add_to_head(node)
            return node.val

    def put(self, key: K, value: V) -> None:
        """Store key-value pair in O(1). Evicts least recently used node if at capacity."""
        with self.lock:
            if key in self.map:
                node = self.map[key]
                node.val = value
                self._remove(node)
                self._add_to_head(node)
                return

            if len(self.map) >= self.capacity:
                # Evict least recently used (node before tail sentinel)
                lru_node = self.tail.prev
                if lru_node and lru_node != self.head:
                    self._remove(lru_node)
                    self.map.pop(lru_node.key, None)

            new_node = _LRUNode(key, value)
            self.map[key] = new_node
            self._add_to_head(new_node)

    def __len__(self) -> int:
        with self.lock:
            return len(self.map)

    def clear(self) -> None:
        with self.lock:
            self.map.clear()
            self.head.next = self.tail
            self.tail.prev = self.head


class TrieNode:
    __slots__ = ("children", "is_end", "value", "matched_keywords")

    def __init__(self):
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end: bool = False
        self.value: Optional[str] = None
        self.matched_keywords: List[str] = []


class Trie:
    """
    Prefix Tree (Trie) for high-performance multi-keyword search, prefix indexing,
    and fast substring token matching.
    """

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, value: Optional[str] = None) -> None:
        """Insert word into Trie in O(L) time where L = len(word)."""
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.value = value or word

    def search(self, word: str) -> bool:
        """Exact word match check in O(L)."""
        node = self.root
        for char in word.lower():
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def starts_with(self, prefix: str) -> bool:
        """Prefix check in O(P) time where P = len(prefix)."""
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return False
            node = node.children[char]
        return True

    def find_all_matches_in_text(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Scan text for all indexed keywords in single pass O(N * M) or O(N).
        Returns list of (matched_word, start_idx, end_idx).
        """
        matches = []
        n = len(text)
        text_lower = text.lower()

        for i in range(n):
            node = self.root
            for j in range(i, n):
                char = text_lower[j]
                if char not in node.children:
                    break
                node = node.children[char]
                if node.is_end and node.value:
                    matches.append((node.value, i, j + 1))
        return matches


class TopKHeap(Generic[T]):
    """
    Min-Heap based Top-K collector.
    Guarantees O(N log K) time complexity and O(K) space complexity
    instead of sorting the entire N-sized array in O(N log N).
    """

    def __init__(self, k: int):
        if k <= 0:
            raise ValueError("K must be positive")
        self.k = k
        self.heap: List[Tuple[float, int, T]] = []
        self._counter = 0

    def push(self, score: float, item: T) -> None:
        """Push an item with score into the min-heap."""
        self._counter += 1
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, (score, self._counter, item))
        else:
            if score > self.heap[0][0]:
                heapq.heapreplace(self.heap, (score, self._counter, item))

    def get_top_k_descending(self) -> List[T]:
        """Returns the collected Top-K items sorted by score in descending order."""
        # Pop from min-heap yields ascending order, reverse gives descending
        sorted_items = []
        temp = list(self.heap)
        while temp:
            score, _, item = heapq.heappop(temp)
            sorted_items.append((score, item))
        return [item for _, item in reversed(sorted_items)]

    def get_top_k_with_scores(self) -> List[Tuple[float, T]]:
        """Returns (score, item) pairs in descending order."""
        sorted_items = []
        temp = list(self.heap)
        while temp:
            score, _, item = heapq.heappop(temp)
            sorted_items.append((score, item))
        return list(reversed(sorted_items))


class FastInvertedIndex:
    """
    Inverted Index structure for sub-millisecond document/faculty keyword scoring.
    Token -> Posting List with Term Frequencies.
    """

    def __init__(self):
        self.index: Dict[str, Dict[str, int]] = {}  # token -> {doc_id: frequency}
        self.doc_lengths: Dict[str, int] = {}       # doc_id -> total tokens

    def add_document(self, doc_id: str, text: str, tokens: Optional[List[str]] = None) -> None:
        """Tokenize and add document to inverted index.
        If tokens is provided, uses them directly; otherwise splits whitespace.
        """
        if tokens is None:
            tokens = [t.lower() for t in text.split() if len(t) >= 2]
        else:
            tokens = [t.lower() for t in tokens if len(t) >= 2]
        self.doc_lengths[doc_id] = len(tokens)

        for token in tokens:
            if token not in self.index:
                self.index[token] = {}
            self.index[token][doc_id] = self.index[token].get(doc_id, 0) + 1

    def score_query(self, query_tokens: List[str]) -> List[Tuple[str, float]]:
        """
        Calculate Okapi-BM25 scores for query tokens across all matching documents.
        Returns list of (doc_id, score) sorted descending.

        BM25 parameterisation (Robertson & Sparck Jones / Okapi):
            IDF(q)  = ln( (N - n(q) + 0.5) / (n(q) + 0.5) + 1 )
            score   = Σ IDF(q) · tf · (k1 + 1) / (tf + k1 · (1 - b + b · |d| / avgdl))
        with the standard k1=1.2, b=0.75. The DSA audit (2026-09-10) replaced the
        previous ad-hoc `idf = 1 + 100/(n+1)` — which inverted real IDF (rewarding
        ubiquitous tokens) — and the hardcoded avgdl=50, with the corpus's true
        statistics captured at build time.
        """
        N = len(self.doc_lengths)
        if N == 0:
            return []
        if getattr(self, "_avgdl", 0) <= 0:
            total = sum(self.doc_lengths.values())
            self._avgdl = total / N if N else 1.0

        k1, b = 1.2, 0.75
        avgdl = self._avgdl
        scores: Dict[str, float] = {}
        for token in query_tokens:
            postings = self.index.get(token.lower())
            if not postings:
                continue
            n_q = len(postings)
            idf = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1.0)
            for doc_id, tf in postings.items():
                doc_len = self.doc_lengths.get(doc_id, 10)
                denom = tf + k1 * (1.0 - b + b * (doc_len / avgdl))
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * (tf * (k1 + 1.0)) / denom

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class ThreadSafeInvertedIndex:
    """
    Read-heavy wrapper around FastInvertedIndex for the shared server-startup corpus.

    The underlying index is plain (non-atomic) dicts. FastInvertedIndex's own docstring
    claims 'thread-safe for reads', but Uvicorn serves a threadpool of sync route
    handlers, and a rebuild that mutates the live dict while a request is mid-scan
    (a growing posting list) would corrupt or mis-score that request. This wrapper
    keeps every read lock-free against a frozen index object, and swaps in a freshly
    rebuilt index atomically under a write lock.

    `score_query` also caps its work with `max_docs`: without it a generic token hits a
    posting list spanning the whole corpus and the score loop becomes O(corpus) per
    request — exactly the scan the index was meant to avoid. Candidates outside the
    top-`max_docs` simply receive no lexical bonus, which is correct behaviour (they are
    not top lexical matches anyway).
    """

    def __init__(self):
        self._index: Optional[FastInvertedIndex] = None
        self._lock = threading.Lock()
        self.doc_count = 0

    def rebuild(self, docs: Dict[str, str], tokenizer: Optional[Callable[[str], List[str]]] = None) -> int:
        """Build a full new index from {doc_id: text} and publish it atomically."""
        fresh = FastInvertedIndex()
        for doc_id, text in docs.items():
            if text:
                tokens = tokenizer(text) if tokenizer else None
                fresh.add_document(doc_id, text, tokens=tokens)
        with self._lock:
            self._index = fresh
            self.doc_count = len(fresh.doc_lengths)
        return self.doc_count

    def score_query(self, query_tokens: List[str], max_docs: int = 2000) -> List[Tuple[str, float]]:
        index = self._index  # single atomic reference read; never mutated after publish
        if not index or not query_tokens:
            return []
        scored = index.score_query(query_tokens)
        if max_docs and len(scored) > max_docs:
            return scored[:max_docs]
        return scored

    def __bool__(self) -> bool:
        return self._index is not None and self.doc_count > 0
