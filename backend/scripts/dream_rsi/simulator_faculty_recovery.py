"""
Dream-RSI Replay Simulator: Autonomous Faculty Email & Profile Recovery
Based on Dream-RSI (Zheng et al., 2026): Recursive Self-Improvement through Evolving Worlds.

Converts historical faculty investigation traces into a deterministic Replay Simulator.
Evaluates exploration policies (batching, prioritization, stopping rules) offline
with zero network egress and zero LLM cost.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Set
import json
import logging
from pathlib import Path

logger = logging.getLogger("dream_rsi.faculty_recovery")


@dataclass
class FacultyProbeObservation:
    """Recorded observation of a single faculty probe."""
    record_id: str
    full_name_th: str
    university_th: str
    faculty_th: str
    profile_url: str
    verdict: str
    recovered_email: Optional[str] = None
    cost: int = 1  # 1 probe cost


@dataclass
class ReplayMetrics:
    """Metrics produced by evaluating an exploration policy in the replay simulator."""
    total_recovered: int
    total_probes: int
    total_rounds: int
    score: float
    precision: float
    average_batch_size: float


class ExplorationPolicy:
    """Base interface for exploration policies in the Replay Simulator."""

    def __init__(self, name: str, max_workers: int = 8):
        self.name = name
        self.max_workers = max_workers

    def select_batch(
        self,
        unexplored: List[FacultyProbeObservation],
        revealed: List[FacultyProbeObservation],
        budget_remaining: int,
    ) -> List[FacultyProbeObservation]:
        """Select a batch of up to max_workers items to probe next."""
        raise NotImplementedError


class NaiveSequentialPolicy(ExplorationPolicy):
    """Baseline policy: Probes sequentially 1 by 1 in natural order without filtering."""

    def select_batch(
        self,
        unexplored: List[FacultyProbeObservation],
        revealed: List[FacultyProbeObservation],
        budget_remaining: int,
    ) -> List[FacultyProbeObservation]:
        if not unexplored or budget_remaining <= 0:
            return []
        return [unexplored[0]]


class FixedParallelPolicy(ExplorationPolicy):
    """Baseline policy: Probes in fixed parallel batches of size W without prioritization."""

    def select_batch(
        self,
        unexplored: List[FacultyProbeObservation],
        revealed: List[FacultyProbeObservation],
        budget_remaining: int,
    ) -> List[FacultyProbeObservation]:
        if not unexplored or budget_remaining <= 0:
            return []
        k = min(self.max_workers, len(unexplored), budget_remaining)
        return unexplored[:k]


class AdaptiveDreamPolicy(ExplorationPolicy):
    """
    Dream-RSI Derived Adaptive Policy:
    1. Heuristic Prioritization: Prioritizes records with individual profile URLs over empty/missing URLs.
    2. Skip Dead Frontiers: Immediately skips candidates with no profile URL published (zero expected recovery).
    3. Parallel Batching: Dynamically fills worker slots up to max_workers with promising candidates.
    4. Early Stopping: Ceases exploration when remaining frontier has zero expected yield.
    """

    def __init__(
        self,
        name: str = "AdaptiveDreamPolicy",
        max_workers: int = 8,
        skip_empty_urls: bool = True,
        min_promising_ratio: float = 0.05,
    ):
        super().__init__(name, max_workers)
        self.skip_empty_urls = skip_empty_urls
        self.min_promising_ratio = min_promising_ratio

    def select_batch(
        self,
        unexplored: List[FacultyProbeObservation],
        revealed: List[FacultyProbeObservation],
        budget_remaining: int,
    ) -> List[FacultyProbeObservation]:
        if not unexplored or budget_remaining <= 0:
            return []

        # Filter and rank candidates
        candidates = []
        for obs in unexplored:
            has_url = bool(obs.profile_url and obs.profile_url.strip())
            if self.skip_empty_urls and not has_url:
                continue

            # Prioritize individual profiles over generic multi-faculty directories
            is_individual = any(
                token in obs.profile_url.lower()
                for token in ["person", "staff", "faculty", "profile", "teacher", "ajarn"]
            )
            priority = 2 if is_individual else (1 if has_url else 0)
            candidates.append((priority, obs))

        if not candidates:
            return []

        # Sort descending by priority
        candidates.sort(key=lambda x: x[0], reverse=True)
        k = min(self.max_workers, len(candidates), budget_remaining)
        return [obs for _, obs in candidates[:k]]


class FacultyRecoveryReplaySimulator:
    """
    Replay Simulator environment constructed from historical audit/investigation checkpoints.
    Follows Dream-RSI Section 3 mathematical formulation:
    V = discovery_quality - beta1 * execution_cost + beta2 * parallelism_bonus
    """

    def __init__(
        self,
        observations: List[FacultyProbeObservation],
        beta1: float = 0.01,
        beta2: float = 0.05,
    ):
        self.raw_observations = observations
        self.beta1 = beta1
        self.beta2 = beta2

    @classmethod
    def from_checkpoint_file(
        cls,
        filepath: str,
        beta1: float = 0.01,
        beta2: float = 0.05,
    ) -> "FacultyRecoveryReplaySimulator":
        """Load simulator state from a historical agent checkpoint JSON."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data.get("investigated_records", [])
        observations: List[FacultyProbeObservation] = []
        for r in records:
            obs = FacultyProbeObservation(
                record_id=r.get("id", ""),
                full_name_th=r.get("full_name_th", ""),
                university_th=r.get("university_th", ""),
                faculty_th=r.get("faculty_th", ""),
                profile_url=r.get("profile_url", "") or "",
                verdict=r.get("verdict", ""),
                recovered_email=r.get("recovered_email"),
                cost=1,
            )
            observations.append(obs)

        return cls(observations=observations, beta1=beta1, beta2=beta2)

    def evaluate_policy(
        self,
        policy: ExplorationPolicy,
        budget: int = 500,
        max_rounds: int = 100,
    ) -> ReplayMetrics:
        """
        Simulate an exploration policy over the frozen replay world.
        Deterministic replay: Returns stored observations for selected nodes without live execution.
        """
        unexplored = list(self.raw_observations)
        unexplored_set: Set[str] = {obs.record_id for obs in unexplored}
        revealed: List[FacultyProbeObservation] = []

        total_probes = 0
        total_rounds = 0
        total_recovered = 0

        while unexplored and total_probes < budget and total_rounds < max_rounds:
            budget_remaining = budget - total_probes
            batch = policy.select_batch(unexplored, revealed, budget_remaining)
            if not batch:
                break

            total_rounds += 1
            for obs in batch:
                if obs.record_id in unexplored_set:
                    unexplored_set.remove(obs.record_id)
                    unexplored.remove(obs)
                    revealed.append(obs)
                    total_probes += obs.cost
                    if obs.verdict == "AUTHENTIC_ACADEMIC_EMAIL_FOUND" and obs.recovered_email:
                        total_recovered += 1

        # Calculate Dream-RSI Objective:
        # V = discovery_quality - beta1 * execution_cost + beta2 * (execution_cost / max(1, rounds))
        discovery_quality = float(total_recovered)
        execution_cost = float(total_probes)
        parallelism_bonus = (
            execution_cost / max(1.0, float(total_rounds)) if total_rounds > 0 else 0.0
        )
        score = (
            discovery_quality
            - (self.beta1 * execution_cost)
            + (self.beta2 * parallelism_bonus)
        )

        precision = (
            (float(total_recovered) / float(total_probes)) if total_probes > 0 else 0.0
        )
        avg_batch_size = (
            (float(total_probes) / float(total_rounds)) if total_rounds > 0 else 0.0
        )

        return ReplayMetrics(
            total_recovered=total_recovered,
            total_probes=total_probes,
            total_rounds=total_rounds,
            score=round(score, 4),
            precision=round(precision, 4),
            average_batch_size=round(avg_batch_size, 2),
        )

    def dream_optimize(
        self,
        candidate_policies: List[ExplorationPolicy],
        budget: int = 500,
    ) -> Dict[str, Any]:
        """
        Dream-RSI Dreaming Phase:
        Evaluates a fleet of alternative exploration policies over the replay simulator
        and selects the policy that maximizes the replay score V.
        """
        leaderboard = []
        best_policy = None
        best_score = float("-inf")
        best_metrics = None

        for policy in candidate_policies:
            metrics = self.evaluate_policy(policy, budget=budget)
            entry = {
                "policy_name": policy.name,
                "score": metrics.score,
                "recovered_emails": metrics.total_recovered,
                "total_probes": metrics.total_probes,
                "total_rounds": metrics.total_rounds,
                "average_batch_size": metrics.average_batch_size,
                "precision": metrics.precision,
            }
            leaderboard.append(entry)

            if metrics.score > best_score:
                best_score = metrics.score
                best_policy = policy
                best_metrics = metrics

        leaderboard.sort(key=lambda x: x["score"], reverse=True)

        return {
            "best_policy": best_policy.name if best_policy else None,
            "best_score": best_score,
            "best_metrics": best_metrics,
            "leaderboard": leaderboard,
        }


if __name__ == "__main__":
    import sys
    checkpoint_file = Path("backend/data/agent_states/comprehensive_investigation_937_faculty.json")
    if not checkpoint_file.exists():
        print(f"Checkpoint not found at {checkpoint_file}")
        sys.exit(1)

    print(f"Loading Dream-RSI Replay Simulator from {checkpoint_file}...")
    sim = FacultyRecoveryReplaySimulator.from_checkpoint_file(str(checkpoint_file))
    print(f"Loaded {len(sim.raw_observations)} frozen historical observations.")

    policies = [
        NaiveSequentialPolicy(name="Sequential-W1", max_workers=1),
        FixedParallelPolicy(name="Parallel-W4", max_workers=4),
        FixedParallelPolicy(name="Parallel-W8", max_workers=8),
        AdaptiveDreamPolicy(name="AdaptiveDream-W8-SkipEmpty", max_workers=8, skip_empty_urls=True),
        AdaptiveDreamPolicy(name="AdaptiveDream-W16-SkipEmpty", max_workers=16, skip_empty_urls=True),
    ]

    result = sim.dream_optimize(policies, budget=500)
    print("\n=== Dream-RSI Policy Optimization Results ===")
    print(f"Optimal Policy: {result['best_policy']} (Score: {result['best_score']})")
    for r in result["leaderboard"]:
        print(
            f"  {r['policy_name']:<30} | Score: {r['score']:>7.3f} | Recovered: {r['recovered_emails']:>2} | "
            f"Probes: {r['total_probes']:>3} | Rounds: {r['total_rounds']:>3} | Batch: {r['average_batch_size']:>4.1f}"
        )
