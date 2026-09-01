"""
Unit tests for WikiSkill Architecture (arXiv:2608.27454v1)
"""
import pytest
import os
import json
import time

from scripts.wikiskill.trace_logger import TraceLogger, ExecutionTraceEntry
from scripts.wikiskill.wiki_maintainer import WikiMaintainer
from scripts.wikiskill.skill_proposer import SkillProposer, SkillPatchProposal


def test_trace_logger_append_and_read(tmp_path):
    """Verify trace logger writes and reads immutable execution traces."""
    logger = TraceLogger(trace_dir=str(tmp_path))

    trace = ExecutionTraceEntry(
        trace_id="test_t1",
        session_id="session_cmu_01",
        university_th="มหาวิทยาลัยเชียงใหม่",
        university_en="Chiang Mai University",
        faculty_th="คณะวิศวกรรมศาสตร์",
        target_url="https://me.eng.cmu.ac.th/staff/professor",
        http_status=200,
        success=True,
        extracted_profiles_count=9
    )

    log_file = logger.log_trace(trace)
    assert os.path.exists(log_file)

    session_traces = logger.read_session_traces("session_cmu_01")
    assert len(session_traces) == 1
    assert session_traces[0].target_url == "https://me.eng.cmu.ac.th/staff/professor"
    assert session_traces[0].extracted_profiles_count == 9


def test_wiki_maintainer_compilation(tmp_path):
    """Verify wiki maintainer compiles traces into structured university knowledge."""
    wiki_dir = str(tmp_path / "wiki")
    maintainer = WikiMaintainer(wiki_dir=wiki_dir)

    traces = [
        ExecutionTraceEntry(
            trace_id="t1",
            session_id="s1",
            university_th="มหาวิทยาลัยเชียงใหม่",
            university_en="Chiang Mai University",
            faculty_th="วิศวกรรมเครื่องกล",
            target_url="https://me.eng.cmu.ac.th/staff/professor",
            http_status=200,
            success=True,
            extracted_profiles_count=12
        ),
        ExecutionTraceEntry(
            trace_id="t2",
            session_id="s1",
            university_th="มหาวิทยาลัยเชียงใหม่",
            university_en="Chiang Mai University",
            faculty_th="วิศวกรรมเครื่องกล",
            target_url="https://me.eng.cmu.ac.th/personnel/academic-staff",
            http_status=404,
            success=False,
            error_message="404 Not Found"
        )
    ]

    summary = maintainer.compile_from_traces(traces)
    assert summary["new_verified_endpoints"] == 1
    assert summary["new_dead_links_recorded"] == 1

    # Verify synthesized markdown
    cmu_file = os.path.join(wiki_dir, "universities", "chiang_mai_university.md")
    assert os.path.exists(cmu_file)

    with open(cmu_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "https://me.eng.cmu.ac.th/staff/professor" in content
    assert "https://me.eng.cmu.ac.th/personnel/academic-staff" in content

    # Test fast lookup
    endpoints = maintainer.lookup_university_endpoints("Chiang Mai University")
    assert "https://me.eng.cmu.ac.th/staff/professor" in endpoints


def test_skill_proposer_and_gating(tmp_path):
    """Verify skill proposal generation and gating (accept on pass, rollback on fail)."""
    wiki_dir = str(tmp_path / "wiki")
    skills_dir = str(tmp_path / "skills")
    os.makedirs(os.path.join(skills_dir, "test-skill"), exist_ok=True)

    skill_file = os.path.join(skills_dir, "test-skill", "SKILL.md")
    with open(skill_file, "w", encoding="utf-8") as f:
        f.write("# Test Skill\n\n## 2. CLI Execution Standard\nRun command here\n")

    maintainer = WikiMaintainer(wiki_dir=wiki_dir)
    # Mock knowledge entry
    maintainer._update_university_wiki("kmitl", [
        ExecutionTraceEntry(
            trace_id="t3",
            session_id="s2",
            university_th="สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
            university_en="KMITL",
            target_url="https://engineer.kmitl.ac.th/staff",
            success=True,
            extracted_profiles_count=15
        )
    ], {"new_verified_endpoints": 1, "new_dead_links_recorded": 0, "updated_universities": set()})

    proposer = SkillProposer(skills_dir=skills_dir, wiki_maintainer=maintainer)

    # 1. Propose Patch
    proposal = proposer.propose_university_endpoint_patch("KMITL", skill_name="test-skill")
    assert proposal is not None
    assert "engineer.kmitl.ac.th" in proposal.proposed_content

    # 2. Test Gating: Fail scenario (should rollback)
    fail_res = proposer.apply_patch_with_gating(proposal, validation_fn=lambda: False)
    assert fail_res is False
    with open(skill_file, "r", encoding="utf-8") as f:
        assert "engineer.kmitl.ac.th" not in f.read()

    # 3. Test Gating: Pass scenario (should accept)
    pass_res = proposer.apply_patch_with_gating(proposal, validation_fn=lambda: True)
    assert pass_res is True
    with open(skill_file, "r", encoding="utf-8") as f:
        assert "engineer.kmitl.ac.th" in f.read()
