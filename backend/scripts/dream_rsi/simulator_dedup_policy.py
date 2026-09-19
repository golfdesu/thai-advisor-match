"""
Dream-RSI Replay Simulator: 3-Pass Academic Deduplication & Entity Resolution
Based on Dream-RSI (Zheng et al., 2026): Recursive Self-Improvement through Evolving Worlds.

Converts historical candidate match traces into a deterministic Replay Simulator.
Evaluates and optimizes deduplication policies (fuzzy thresholds, multi-factor guards)
offline without risking real database corruption.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from rapidfuzz import fuzz

logger = logging.getLogger("dream_rsi.dedup_policy")


@dataclass
class FacultyPairObservation:
    """Historical pairwise candidate record with known ground-truth merge verdict."""
    pair_id: str
    faculty_a_name_th: str
    faculty_a_name_en: str
    faculty_a_uni: str
    faculty_a_dept: str
    faculty_a_email: Optional[str]
    faculty_b_name_th: str
    faculty_b_name_en: str
    faculty_b_uni: str
    faculty_b_dept: str
    faculty_b_email: Optional[str]
    is_true_duplicate: bool  # Ground truth: True if same person, False if distinct
    disqualification_reason: Optional[str] = None


@dataclass
class DedupMetrics:
    """Evaluation metrics for a deduplication policy."""
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float
    f1_score: float
    score: float


@dataclass
class DedupPolicyConfig:
    """Policy configuration for academic entity resolution."""
    name: str
    thai_fuzz_threshold: float = 95.0
    eng_fuzz_threshold: float = 95.0
    require_same_university: bool = True
    require_dept_compatibility: bool = False
    allow_email_exact_merge: bool = True
    # Blacklisted generic/departmental inboxes per Section 9
    excluded_email_prefixes: Tuple[str, ...] = (
        "info@", "contact@", "saraban@", "admin@", "support@", "dean@", "pr@"
    )


class DedupReplaySimulator:
    """
    Replay Simulator environment for Entity Resolution & Deduplication.
    Objective:
        V = True_Positives - (FP_Penalty * False_Positives) - (FN_Penalty * False_Negatives)
    Heavily penalizes False Positives to protect database integrity (Section 9 Invariant 10).
    """

    def __init__(
        self,
        dataset: List[FacultyPairObservation],
        fp_penalty: float = 100.0,
        fn_penalty: float = 1.0,
    ):
        self.dataset = dataset
        self.fp_penalty = fp_penalty
        self.fn_penalty = fn_penalty

    @classmethod
    def create_benchmark_dataset(cls) -> List[FacultyPairObservation]:
        """
        Creates a grounded benchmark dataset reflecting common academic duplicate scenarios:
        1. Exact Thai title variance (e.g. 'ผศ.ดร. มานะ' vs 'ดร. มานะ')
        2. English transliteration differences (e.g. 'Chaiwat' vs 'Chaiwat P.')
        3. Distinct faculty with identical last names or similar first names (Doctors / Twins)
        4. Cross-university name collisions (must NOT be merged if distinct individuals)
        5. Shared departmental email collisions (must NOT be merged per Section 9)
        """
        pairs = [
            # Case 1: True Duplicate - Same Thai name without title, same Uni
            FacultyPairObservation(
                pair_id="true_dup_thai_01",
                faculty_a_name_th="ผศ.ดร. มานะ ชัยสงคราม",
                faculty_a_name_en="Mana Chaisongkram",
                faculty_a_uni="จุฬาลงกรณ์มหาวิทยาลัย",
                faculty_a_dept="ภาควิชาวิศวกรรมคอมพิวเตอร์",
                faculty_a_email="mana.c@chula.ac.th",
                faculty_b_name_th="ดร. มานะ ชัยสงคราม",
                faculty_b_name_en="Mana Chaisongkram",
                faculty_b_uni="จุฬาลงกรณ์มหาวิทยาลัย",
                faculty_b_dept="ภาควิชาวิศวกรรมคอมพิวเตอร์",
                faculty_b_email="mana.c@chula.ac.th",
                is_true_duplicate=True,
            ),
            # Case 2: True Duplicate - Transliteration difference, same Uni & Email
            FacultyPairObservation(
                pair_id="true_dup_eng_translit_02",
                faculty_a_name_th="รศ.ดร. กานดา สายทอง",
                faculty_a_name_en="Kanda Saithong",
                faculty_a_uni="มหาวิทยาลัยเกษตรศาสตร์",
                faculty_a_dept="ภาควิชาพืชไร่นา",
                faculty_a_email="kanda.s@ku.ac.th",
                faculty_b_name_th="รศ.ดร. กานดา สายทอง",
                faculty_b_name_en="Kanda Saythong",
                faculty_b_uni="มหาวิทยาลัยเกษตรศาสตร์",
                faculty_b_dept="ภาควิชาพืชไร่นา",
                faculty_b_email="kanda.s@ku.ac.th",
                is_true_duplicate=True,
            ),
            # Case 3: True Duplicate - Minor typo in English name, exact email match
            FacultyPairObservation(
                pair_id="true_dup_email_03",
                faculty_a_name_th="อ.ดร. พรเทพ มั่นคง",
                faculty_a_name_en="Pornthep Munkong",
                faculty_a_uni="มหาวิทยาลัยเชียงใหม่",
                faculty_a_dept="ภาควิชาเคมี",
                faculty_a_email="pornthep.m@cmu.ac.th",
                faculty_b_name_th="อาจารย์ ดร. พรเทพ มั่นคง",
                faculty_b_name_en="Pornthep Munkong",
                faculty_b_uni="มหาวิทยาลัยเชียงใหม่",
                faculty_b_dept="ภาควิชาเคมี",
                faculty_b_email="pornthep.m@cmu.ac.th",
                is_true_duplicate=True,
            ),
            # Case 4: False Duplicate - Different persons, same family name (Siblings / Family in same Uni)
            FacultyPairObservation(
                pair_id="false_dup_family_04",
                faculty_a_name_th="ผศ.ดร. วิภา ชัยสงคราม",
                faculty_a_name_en="Wipha Chaisongkram",
                faculty_a_uni="จุฬาลงกรณ์มหาวิทยาลัย",
                faculty_a_dept="คณะวิทยาศาสตร์",
                faculty_a_email="wipha.c@chula.ac.th",
                faculty_b_name_th="ผศ.ดร. มานะ ชัยสงคราม",
                faculty_b_name_en="Mana Chaisongkram",
                faculty_b_uni="จุฬาลงกรณ์มหาวิทยาลัย",
                faculty_b_dept="คณะวิศวกรรมศาสตร์",
                faculty_b_email="mana.c@chula.ac.th",
                is_true_duplicate=False,
                disqualification_reason="Distinct individuals: different given names",
            ),
            # Case 5: False Duplicate - Same name, DIFFERENT universities (Cross-university distinct individuals)
            FacultyPairObservation(
                pair_id="false_dup_cross_uni_05",
                faculty_a_name_th="ศ.ดร. สมนึก อัครเดช",
                faculty_a_name_en="Somnuk Akaradech",
                faculty_a_uni="มหาวิทยาลัยขอนแก่น",
                faculty_a_dept="คณะแพทยศาสตร์",
                faculty_a_email="somnuk@kku.ac.th",
                faculty_b_name_th="ศ.ดร. สมนึก อัครเดช",
                faculty_b_name_en="Somnuk Akaradech",
                faculty_b_uni="มหาวิทยาลัยสงขลานครินทร์",
                faculty_b_dept="คณะวิศวกรรมศาสตร์",
                faculty_b_email="somnuk.a@psu.ac.th",
                is_true_duplicate=False,
                disqualification_reason="Distinct faculty across different universities and departments",
            ),
            # Case 6: False Duplicate - Shared departmental inbox collision (contact@eng.ku.ac.th)
            FacultyPairObservation(
                pair_id="false_dup_shared_email_06",
                faculty_a_name_th="อ. อนุชา สุวรรณ",
                faculty_a_name_en="Anucha Suwan",
                faculty_a_uni="มหาวิทยาลัยเกษตรศาสตร์",
                faculty_a_dept="คณะวิศวกรรมศาสตร์",
                faculty_a_email="contact@eng.ku.ac.th",
                faculty_b_name_th="ผศ. ชัยพร รัตนวงศ์",
                faculty_b_name_en="Chaiyaporn Rattanawong",
                faculty_b_uni="มหาวิทยาลัยเกษตรศาสตร์",
                faculty_b_dept="คณะวิศวกรรมศาสตร์",
                faculty_b_email="contact@eng.ku.ac.th",
                is_true_duplicate=False,
                disqualification_reason="Shared generic department inbox cannot be used as identity proof",
            ),
            # Case 7: True Duplicate - Title variant without email
            FacultyPairObservation(
                pair_id="true_dup_no_email_07",
                faculty_a_name_th="อาจารย์ ดร. ธีรภัทร เจริญศิลป์",
                faculty_a_name_en="Theeraphat Charoensilp",
                faculty_a_uni="มหาวิทยาลัยมหิดล",
                faculty_a_dept="คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
                faculty_a_email=None,
                faculty_b_name_th="อ.ดร. ธีรภัทร เจริญศิลป์",
                faculty_b_name_en="Teerapat Charoensilp",
                faculty_b_uni="มหาวิทยาลัยมหิดล",
                faculty_b_dept="คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
                faculty_b_email=None,
                is_true_duplicate=True,
            ),
            # Case 8: False Duplicate - Doctor title confusion (นพ. vs พญ.)
            FacultyPairObservation(
                pair_id="false_dup_doctor_gender_08",
                faculty_a_name_th="นพ. สุรชัย พงษ์ศิริ",
                faculty_a_name_en="Surachai Pongsiri",
                faculty_a_uni="มหาวิทยาลัยเชียงใหม่",
                faculty_a_dept="คณะแพทยศาสตร์",
                faculty_a_email="surachai.p@cmu.ac.th",
                faculty_b_name_th="พญ. สุรพร พงษ์ศิริ",
                faculty_b_name_en="Suraporn Pongsiri",
                faculty_b_uni="มหาวิทยาลัยเชียงใหม่",
                faculty_b_dept="คณะแพทยศาสตร์",
                faculty_b_email="suraporn.p@cmu.ac.th",
                is_true_duplicate=False,
                disqualification_reason="Distinct male and female clinical doctors",
            ),
        ]
        return pairs

    def evaluate_policy(self, config: DedupPolicyConfig) -> DedupMetrics:
        """
        Executes policy decisions against the frozen benchmark dataset.
        Returns precision, recall, F1, and overall Dream-RSI score.
        """
        tp = 0
        fp = 0
        fn = 0
        tn = 0

        for pair in self.dataset:
            # Policy Decision Logic
            predicted_duplicate = self._predict_pair(pair, config)

            if predicted_duplicate and pair.is_true_duplicate:
                tp += 1
            elif predicted_duplicate and not pair.is_true_duplicate:
                fp += 1
            elif not predicted_duplicate and pair.is_true_duplicate:
                fn += 1
            else:
                tn += 1

        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        # Score formula: Heavily penalize false positives
        score = float(tp) - (self.fp_penalty * float(fp)) - (self.fn_penalty * float(fn))

        return DedupMetrics(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            score=round(score, 2),
        )

    def _predict_pair(self, pair: FacultyPairObservation, config: DedupPolicyConfig) -> bool:
        """Applies 3-Pass logic to determine if a pair is a duplicate."""
        # University Guard
        if config.require_same_university and pair.faculty_a_uni != pair.faculty_b_uni:
            return False

        # Pass 3: Verified Personal Email Match (Prioritized if authentic)
        if config.allow_email_exact_merge and pair.faculty_a_email and pair.faculty_b_email:
            em_a = pair.faculty_a_email.strip().lower()
            em_b = pair.faculty_b_email.strip().lower()
            # Guard against excluded generic departmental emails
            is_generic_a = any(em_a.startswith(pref) for pref in config.excluded_email_prefixes)
            is_generic_b = any(em_b.startswith(pref) for pref in config.excluded_email_prefixes)
            if em_a == em_b and not is_generic_a and not is_generic_b:
                return True

        # Pass 1: Thai Name Fuzzy Ratio
        thai_clean_a = self._clean_thai_name(pair.faculty_a_name_th)
        thai_clean_b = self._clean_thai_name(pair.faculty_b_name_th)
        thai_ratio = fuzz.token_sort_ratio(thai_clean_a, thai_clean_b)

        if thai_ratio >= config.thai_fuzz_threshold:
            return True

        # Pass 2: English Name Fuzzy Ratio
        if pair.faculty_a_name_en and pair.faculty_b_name_en:
            eng_a = pair.faculty_a_name_en.strip().lower()
            eng_b = pair.faculty_b_name_en.strip().lower()
            eng_ratio = fuzz.token_sort_ratio(eng_a, eng_b)
            if eng_ratio >= config.eng_fuzz_threshold:
                return True

        return False

    def _clean_thai_name(self, name: str) -> str:
        """Strip academic titles from Thai names for comparison."""
        import re
        title_pattern = re.compile(
            r"^(ศาสตราจารย์\s*ดร\.|รองศาสตราจารย์\s*ดร\.|ผู้ช่วยศาสตราจารย์\s*ดร\.|"
            r"อาจารย์\s*ดร\.|ศ\.ดร\.|รศ\.ดร\.|ผศ\.ดร\.|อ\.ดร\.|ศ\.|รศ\.|ผศ\.|อ\.|"
            r"ดร\.|นพ\.|พญ\.|ทพ\.|ภก\.|ภญ\.|นาย|นาง|นางสาว)\s*",
            re.IGNORECASE
        )
        return title_pattern.sub("", name).strip()

    def dream_sweep(self, configs: List[DedupPolicyConfig]) -> Dict[str, Any]:
        """Runs a dream sweep over candidate deduplication policy configs."""
        results = []
        best_config = None
        best_score = float("-inf")
        best_metrics = None

        for cfg in configs:
            metrics = self.evaluate_policy(cfg)
            entry = {
                "config_name": cfg.name,
                "thai_threshold": cfg.thai_fuzz_threshold,
                "eng_threshold": cfg.eng_fuzz_threshold,
                "require_same_uni": cfg.require_same_university,
                "score": metrics.score,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "tp": metrics.true_positives,
                "fp": metrics.false_positives,
                "fn": metrics.false_negatives,
            }
            results.append(entry)

            if metrics.score > best_score:
                best_score = metrics.score
                best_config = cfg
                best_metrics = metrics

        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "best_config": best_config.name if best_config else None,
            "best_score": best_score,
            "best_metrics": best_metrics,
            "leaderboard": results,
        }


if __name__ == "__main__":
    dataset = DedupReplaySimulator.create_benchmark_dataset()
    sim = DedupReplaySimulator(dataset=dataset, fp_penalty=100.0, fn_penalty=1.0)
    print(f"Loaded {len(dataset)} historical entity resolution benchmark pairs.")

    candidate_configs = [
        # Over-aggressive: low threshold, allows cross-university
        DedupPolicyConfig(
            name="Aggressive-T75-CrossUni",
            thai_fuzz_threshold=75.0,
            eng_fuzz_threshold=75.0,
            require_same_university=False,
        ),
        # Moderate: standard 85 threshold, ignores email exclusions
        DedupPolicyConfig(
            name="Loose-T85-NoEmailGuard",
            thai_fuzz_threshold=85.0,
            eng_fuzz_threshold=85.0,
            require_same_university=True,
            excluded_email_prefixes=(),  # Doesn't exclude contact@
        ),
        # Over-conservative: 100% exact match only
        DedupPolicyConfig(
            name="OverConservative-T100",
            thai_fuzz_threshold=100.0,
            eng_fuzz_threshold=100.0,
            require_same_university=True,
        ),
        # Dream-RSI Calibrated: 90% threshold + Strict Uni Guard + Email Guard (Section 9)
        DedupPolicyConfig(
            name="Calibrated-T90-Section9",
            thai_fuzz_threshold=90.0,
            eng_fuzz_threshold=90.0,
            require_same_university=True,
            allow_email_exact_merge=True,
        ),
    ]

    sweep_result = sim.dream_sweep(candidate_configs)
    print("\n=== Dream-RSI Deduplication Policy Sweep Results ===")
    print(f"Optimal Policy: {sweep_result['best_config']} (Score: {sweep_result['best_score']})")
    for r in sweep_result["leaderboard"]:
        print(
            f"  {r['config_name']:<28} | Score: {r['score']:>7.2f} | Precision: {r['precision']:>6.2%} | "
            f"Recall: {r['recall']:>6.2%} | F1: {r['f1_score']:>6.2%} | FP: {r['fp']} | FN: {r['fn']}"
        )
