"""
Unit and regression tests for Dream-RSI simulators and harnesses:
1. Faculty Recovery Replay Simulator
2. Deduplication Policy Simulator
3. DSA Algorithm Engineering Harness
"""

import pytest
from scripts.dream_rsi.simulator_faculty_recovery import (
    FacultyProbeObservation,
    FacultyRecoveryReplaySimulator,
    NaiveSequentialPolicy,
    FixedParallelPolicy,
    AdaptiveDreamPolicy,
)
from scripts.dream_rsi.simulator_dedup_policy import (
    DedupReplaySimulator,
    DedupPolicyConfig,
    FacultyPairObservation,
)
from scripts.dream_rsi.benchmark_dsa_engineering import (
    AlgorithmEngineeringHarness,
    canonical_tokenize_mixed,
    candidate1_tokenize_mixed,
    candidate2_tokenize_mixed,
)


def test_faculty_recovery_replay_objective_calculation():
    """Verify Dream-RSI objective math: V = quality - beta1 * cost + beta2 * parallelism."""
    obs_list = [
        FacultyProbeObservation(
            record_id=f"rec_{i}",
            full_name_th=f"อาจารย์ {i}",
            university_th="มหาวิทยาลัย",
            faculty_th="คณะ",
            profile_url=f"https://uni.ac.th/person/{i}",
            verdict="AUTHENTIC_ACADEMIC_EMAIL_FOUND" if i % 2 == 0 else "EMPTY_PROFILE_NO_EMAIL",
            recovered_email=f"aj_{i}@uni.ac.th" if i % 2 == 0 else None,
            cost=1,
        )
        for i in range(10)
    ]

    sim = FacultyRecoveryReplaySimulator(observations=obs_list, beta1=0.01, beta2=0.05)
    policy = FixedParallelPolicy(name="TestParallelW4", max_workers=4)

    metrics = sim.evaluate_policy(policy, budget=10, max_rounds=5)

    assert metrics.total_probes == 10
    # 10 items with max_workers=4 takes ceil(10/4) = 3 rounds
    assert metrics.total_rounds == 3
    assert metrics.total_recovered == 5  # even numbers (0, 2, 4, 6, 8)

    # Manual check:
    # quality = 5.0
    # cost = 10.0 * 0.01 = 0.10
    # parallelism = (10 / 3) * 0.05 = 0.16666...
    # score = 5.0 - 0.10 + 0.1667 = 5.0667
    expected_score = round(5.0 - (0.01 * 10) + (0.05 * (10 / 3)), 4)
    assert abs(metrics.score - expected_score) < 1e-3


def test_adaptive_dream_policy_skips_empty_urls():
    """Verify AdaptiveDreamPolicy skips empty URLs and prioritizes actionable profiles."""
    obs_list = [
        FacultyProbeObservation(
            record_id="no_url_1",
            full_name_th="อาจารย์ A",
            university_th="มหาวิทยาลัย A",
            faculty_th="คณะ A",
            profile_url="",
            verdict="NO_PROFILE_URL_PUBLISHED",
            recovered_email=None,
        ),
        FacultyProbeObservation(
            record_id="has_url_2",
            full_name_th="อาจารย์ B",
            university_th="มหาวิทยาลัย B",
            faculty_th="คณะ B",
            profile_url="https://uni.ac.th/profile/b",
            verdict="AUTHENTIC_ACADEMIC_EMAIL_FOUND",
            recovered_email="b@uni.ac.th",
        ),
    ]

    sim = FacultyRecoveryReplaySimulator(observations=obs_list, beta1=0.01, beta2=0.05)
    policy = AdaptiveDreamPolicy(name="Adaptive", max_workers=2, skip_empty_urls=True)

    metrics = sim.evaluate_policy(policy, budget=2, max_rounds=2)
    assert metrics.total_recovered == 1
    assert metrics.total_probes == 1  # Only probed the valid URL, skipped no_url_1


def test_dedup_simulator_guards_against_false_merges():
    """Verify DedupReplaySimulator correctly identifies false duplicates and penalizes FPs."""
    dataset = DedupReplaySimulator.create_benchmark_dataset()
    sim = DedupReplaySimulator(dataset=dataset, fp_penalty=100.0, fn_penalty=1.0)

    # Section 9 Calibrated Policy: Must have 100% precision (0 false positives)
    calibrated_cfg = DedupPolicyConfig(
        name="Calibrated-T90-Section9",
        thai_fuzz_threshold=90.0,
        eng_fuzz_threshold=90.0,
        require_same_university=True,
        allow_email_exact_merge=True,
    )
    metrics = sim.evaluate_policy(calibrated_cfg)
    assert metrics.false_positives == 0
    assert metrics.precision == 1.0
    assert metrics.score > 0

    # Careless policy: Low threshold and no university guard -> Must trigger false positives
    careless_cfg = DedupPolicyConfig(
        name="Careless-CrossUni",
        thai_fuzz_threshold=70.0,
        eng_fuzz_threshold=70.0,
        require_same_university=False,
    )
    careless_metrics = sim.evaluate_policy(careless_cfg)
    assert careless_metrics.false_positives > 0
    assert careless_metrics.score < 0  # Penalized heavily


def test_dsa_engineering_parity_verification():
    """Verify AlgorithmEngineeringHarness guarantees exact bit-level parity with canonical code."""
    harness = AlgorithmEngineeringHarness()

    # Candidate 1 and Candidate 2 must have 100% parity
    valid1, err1 = harness.verify_parity(candidate1_tokenize_mixed, canonical_tokenize_mixed)
    assert valid1 is True, f"Candidate 1 failed: {err1}"

    valid2, err2 = harness.verify_parity(candidate2_tokenize_mixed, canonical_tokenize_mixed)
    assert valid2 is True, f"Candidate 2 failed: {err2}"

    # Deliberately broken candidate must be detected and rejected
    def broken_candidate(text: str):
        return text.split()  # Whitespace split violates character bigram invariant!

    valid_broken, err_broken = harness.verify_parity(broken_candidate, canonical_tokenize_mixed)
    assert valid_broken is False
    assert "Parity mismatch" in err_broken
