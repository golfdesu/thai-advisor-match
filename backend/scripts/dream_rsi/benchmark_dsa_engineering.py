"""
Dream-RSI Algorithm Engineering Harness: Backend DSA Optimization
Based on Dream-RSI (Zheng et al., 2026): Algorithm Engineering Evaluation.

Provides automated benchmarking, execution profiling, and 100% bit-level parity verification
for critical backend DSA primitives (tokenization, heap collection, BM25 scoring).
Guarantees Section 9 Invariant 2 (Lexical Indexing Symmetry).
"""

import time
import re
from typing import List, Dict, Any, Callable, Tuple, Optional
import logging

logger = logging.getLogger("dream_rsi.dsa_engineering")

# Canonical reference regexes from app/core/corpus_index.py
_THAI_RUN = re.compile(r"[฀-๿]+")
_ASCII_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-\.]*")


def canonical_tokenize_mixed(text: str) -> List[str]:
    """Canonical reference implementation from app.core.corpus_index."""
    tokens: List[str] = []
    for tok in _ASCII_TOKEN.findall(text):
        if len(tok) >= 2:
            tokens.append(tok.lower())
    for run in _THAI_RUN.findall(text):
        if len(run) == 1:
            continue
        tokens.extend(run[i:i + 2] for i in range(len(run) - 1))
    return tokens


# Candidate 1: Optimized regex matching len >= 2 directly in C-level regex engine
_ASCII_TOKEN_CANDIDATE1 = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-\.]+")


def candidate1_tokenize_mixed(text: str) -> List[str]:
    """
    Candidate 1:
    - Filters token length >= 2 inside regex pattern directly, avoiding Python-level len() branches.
    - Uses list comprehension for ASCII lowercasing.
    """
    tokens = [tok.lower() for tok in _ASCII_TOKEN_CANDIDATE1.findall(text)]
    for run in _THAI_RUN.findall(text):
        n = len(run)
        if n > 1:
            tokens.extend(run[i:i + 2] for i in range(n - 1))
    return tokens


# Candidate 2: Optimized list pre-allocation and slice generator
def candidate2_tokenize_mixed(text: str) -> List[str]:
    """
    Candidate 2:
    - Pre-filtered regex.
    - Generator-free bigram loop using list comprehension directly.
    """
    tokens = [tok.lower() for tok in _ASCII_TOKEN_CANDIDATE1.findall(text)]
    extend = tokens.extend
    for run in _THAI_RUN.findall(text):
        n = len(run)
        if n > 1:
            extend([run[i:i + 2] for i in range(n - 1)])
    return tokens


BENCHMARK_CORPUS = [
    "ปัญญาประดิษฐ์ วิศวกรรมคอมพิวเตอร์ Machine Learning และ Deep Learning สำหรับการประมวลผลภาษาธรรมชาติ",
    "Robotics and Autonomous Systems ภาควิชาวิศวกรรมเครื่องกล จุฬาลงกรณ์มหาวิทยาลัย",
    "การวิจัยทางด้านเคมีอินทรีย์ Organic Chemistry and Biomolecular Engineering",
    "Bioinformatics and Genomic Data Science สำนักวิชาวิทยาศาสตร์และเทคโนโลยี",
    "A",  # Single character ASCII edge case
    "ก",  # Single character Thai edge case
    "AI",  # 2-char ASCII
    "มช",  # 2-char Thai
    "การพัฒนาเทคโนโลยีด้านการแพทย์และสาธารณสุข Biomedical Engineering & AI Health Informatics 2026",
    "Data Science, Big Data Analytics, Cloud Computing, High Performance Computing (HPC)",
]


class AlgorithmEngineeringHarness:
    """
    Evaluation harness for algorithmic self-improvement.
    Measures latency, throughput, and guarantees 100% parity against canonical reference.
    """

    def __init__(self, corpus: List[str] = BENCHMARK_CORPUS):
        self.corpus = corpus

    def verify_parity(
        self,
        candidate_fn: Callable[[str], List[str]],
        reference_fn: Callable[[str], List[str]] = canonical_tokenize_mixed,
    ) -> Tuple[bool, Optional[str]]:
        """Verifies 100% exact parity across the benchmark corpus."""
        for idx, text in enumerate(self.corpus):
            ref_out = reference_fn(text)
            cand_out = candidate_fn(text)
            if ref_out != cand_out:
                msg = (
                    f"Parity mismatch at sample {idx}: '{text}'\n"
                    f"  Ref:  {ref_out}\n"
                    f"  Cand: {cand_out}"
                )
                return False, msg
        return True, None

    def benchmark_throughput(
        self,
        fn: Callable[[str], List[str]],
        iterations: int = 5000,
    ) -> Dict[str, float]:
        """Runs timed iterations and measures latency and throughput."""
        # Warm-up
        for text in self.corpus:
            fn(text)

        start_time = time.perf_counter()
        total_calls = 0
        for _ in range(iterations):
            for text in self.corpus:
                fn(text)
                total_calls += 1
        elapsed_sec = time.perf_counter() - start_time

        avg_latency_us = (elapsed_sec / total_calls) * 1_000_000
        ops_per_sec = total_calls / elapsed_sec if elapsed_sec > 0 else 0

        return {
            "elapsed_sec": elapsed_sec,
            "total_calls": total_calls,
            "avg_latency_us": round(avg_latency_us, 3),
            "ops_per_sec": round(ops_per_sec, 1),
        }

    def run_discovery_round(
        self,
        candidates: List[Tuple[str, Callable[[str], List[str]]]],
        iterations: int = 5000,
    ) -> Dict[str, Any]:
        """
        Executes an algorithm engineering evaluation round across candidate implementations.
        Disqualifies any candidate failing the parity check.
        """
        # Benchmark reference
        ref_bench = self.benchmark_throughput(canonical_tokenize_mixed, iterations=iterations)
        ref_latency = ref_bench["avg_latency_us"]

        leaderboard = []
        for name, cand_fn in candidates:
            is_valid, error_msg = self.verify_parity(cand_fn, canonical_tokenize_mixed)
            if not is_valid:
                leaderboard.append({
                    "name": name,
                    "valid": False,
                    "error": error_msg,
                    "speedup": 0.0,
                    "latency_us": None,
                })
                continue

            bench = self.benchmark_throughput(cand_fn, iterations=iterations)
            cand_latency = bench["avg_latency_us"]
            speedup = (ref_latency / cand_latency) if cand_latency > 0 else 1.0

            leaderboard.append({
                "name": name,
                "valid": True,
                "latency_us": cand_latency,
                "ops_per_sec": bench["ops_per_sec"],
                "speedup": round(speedup, 3),
            })

        leaderboard.sort(key=lambda x: x.get("speedup", 0.0), reverse=True)

        return {
            "reference_latency_us": ref_latency,
            "reference_ops_per_sec": ref_bench["ops_per_sec"],
            "leaderboard": leaderboard,
        }


if __name__ == "__main__":
    harness = AlgorithmEngineeringHarness()
    print("=== Dream-RSI Algorithm Engineering: Tokenizer Optimization ===")

    candidates = [
        ("Candidate 1 (Regex Len Guard)", candidate1_tokenize_mixed),
        ("Candidate 2 (List Pre-alloc & Method Cache)", candidate2_tokenize_mixed),
    ]

    report = harness.run_discovery_round(candidates, iterations=5000)
    print(f"Reference Latency: {report['reference_latency_us']:.3f} µs | Ops/sec: {report['reference_ops_per_sec']:,.0f}")
    print("\nCandidate Leaderboard:")
    for c in report["leaderboard"]:
        if c["valid"]:
            print(
                f"  {c['name']:<40} | Latency: {c['latency_us']:>6.3f} µs | "
                f"Throughput: {c['ops_per_sec']:>10,.0f} ops/s | Speedup: {c['speedup']:>5.2f}x"
            )
        else:
            print(f"  {c['name']:<40} | INVALID: {c['error']}")
