"""
WikiSkill Proposer & Gating Engine (Layer 3: Skill Evolution)
Based on WikiSkill Architecture: https://arxiv.org/html/2608.27454v1
"""
import os
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from scripts.wikiskill.wiki_maintainer import WikiMaintainer


class SkillPatchProposal:
    """Represents a proposed patch to a skill markdown file."""
    def __init__(
        self,
        skill_name: str,
        target_file: str,
        section_heading: str,
        proposed_content: str,
        rationale: str
    ):
        self.skill_name = skill_name
        self.target_file = target_file
        self.section_heading = section_heading
        self.proposed_content = proposed_content
        self.rationale = rationale
        self.status = "proposed"  # proposed, accepted, rejected


class SkillProposer:
    """
    Analyzes Wiki insights and proposes atomic, validated patches
    to .claude/skills/ markdown instructions.
    """

    def __init__(
        self,
        skills_dir: str = "Teacher/.claude/skills",
        wiki_maintainer: Optional[WikiMaintainer] = None
    ):
        self.skills_dir = skills_dir
        self.wiki_maintainer = wiki_maintainer or WikiMaintainer()

    def propose_university_endpoint_patch(
        self,
        university_en: str,
        skill_name: str = "data-acquire-faculty-elites"
    ) -> Optional[SkillPatchProposal]:
        """Proposes adding newly verified endpoints to a skill file."""
        endpoints = self.wiki_maintainer.lookup_university_endpoints(university_en)
        if not endpoints:
            return None

        skill_file = os.path.join(self.skills_dir, skill_name, "SKILL.md")
        if not os.path.exists(skill_file):
            return None

        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if endpoints are already documented
        unmentioned = [ep for ep in endpoints if ep not in content]
        if not unmentioned:
            return None

        proposed_text = f"\n- **Verified {university_en} Endpoints:**\n" + "\n".join([f"  - `{ep}`" for ep in unmentioned])

        return SkillPatchProposal(
            skill_name=skill_name,
            target_file=skill_file,
            section_heading="## 2. CLI Execution Standard",
            proposed_content=proposed_text,
            rationale=f"Add {len(unmentioned)} newly verified endpoints from WikiSkill knowledge compilation"
        )

    def apply_patch_with_gating(
        self,
        proposal: SkillPatchProposal,
        validation_fn=None
    ) -> bool:
        """
        Applies proposed patch only if validation gate passes.
        Wiki knowledge is never rolled back, but skill changes are strictly gated.
        """
        if not os.path.exists(proposal.target_file):
            proposal.status = "rejected"
            return False

        with open(proposal.target_file, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Append proposed patch under target section
        if proposal.section_heading in original_content:
            parts = original_content.split(proposal.section_heading, 1)
            updated_content = parts[0] + proposal.section_heading + "\n" + proposal.proposed_content + parts[1]
        else:
            updated_content = original_content + "\n" + proposal.proposed_content

        # Write tentatively
        with open(proposal.target_file, "w", encoding="utf-8") as f:
            f.write(updated_content)

        # Validation Gate
        is_valid = True
        if validation_fn:
            try:
                is_valid = validation_fn()
            except Exception as e:
                is_valid = False

        if is_valid:
            proposal.status = "accepted"
            self._log_skill_patch(proposal, accepted=True)
            return True
        else:
            # Rollback
            with open(proposal.target_file, "w", encoding="utf-8") as f:
                f.write(original_content)
            proposal.status = "rejected"
            self._log_skill_patch(proposal, accepted=False)
            return False

    def _log_skill_patch(self, proposal: SkillPatchProposal, accepted: bool):
        """Logs patch decision to wiki evolution log."""
        log_path = os.path.join(self.wiki_maintainer.wiki_dir, "evolution_log.md")
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        status_str = "ACCEPTED" if accepted else "REJECTED (Rolled Back)"

        entry = f"""
### [{now_str}] Skill Evolution Patch ({status_str})
- **Target Skill:** `{proposal.skill_name}`
- **Target File:** `{proposal.target_file}`
- **Rationale:** {proposal.rationale}
"""
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
