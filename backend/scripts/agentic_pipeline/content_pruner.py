"""
Deterministic Content Pruner for University Faculty Webpages
Inspired by Microsoft LLMLingua-2 & Trafilatura DOM Heuristics
Extracts high-density academic staff containers, eliminates boilerplate navbars/footers,
and reduces input tokens by 50% - 75% before passing to LLMs.
"""
import re
from typing import List, Tuple
from bs4 import BeautifulSoup, Tag, NavigableString


# Keywords indicating academic staff information density
ACADEMIC_KEYWORDS = {
    "ศาสตราจารย์", "รองศาสตราจารย์", "ผู้ช่วยศาสตราจารย์", "อาจารย์",
    "ศ.ดร.", "รศ.ดร.", "ผศ.ดร.", "อ.ดร.", "ดร.", "ศ.", "รศ.", "ผศ.", "อ.",
    "professor", "assoc.", "asst.", "lecturer", "dr.", "ph.d.", "m.sc.", "b.sc.",
    "faculty", "staff", "personnel", "research", "email", "interests", "publications",
    "ภาควิชา", "สาขาวิชา", "ประวัติ", "ผลงาน", "ความเชี่ยวชาญ", "การศึกษา"
}

# Tags and classes strictly representing boilerplate noise
NOISE_TAGS = {"script", "style", "svg", "noscript", "iframe", "header", "footer", "nav"}
NOISE_CLASSES_IDS = re.compile(
    r"(header|footer|navbar|navigation|sidebar|menu|breadcrumb|pagination|cookie|popup|modal|banner|advert|widget)",
    re.IGNORECASE
)


class ContentPruner:
    """
    High-Performance Heuristic Content Pruner.
    Extracts core content blocks with high academic entity density.
    """

    @staticmethod
    def prune_html(html_content: str, max_output_chars: int = 25000) -> str:
        """
        Prunes raw HTML and extracts only dense academic containers.
        Returns cleaned, compressed text preserving structural line breaks.
        """
        if not html_content:
            return ""

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # 1. Remove explicit noise tags
            for tag in soup(NOISE_TAGS):
                tag.decompose()

            # 2. Decompose elements matching noise class/id patterns
            for el in soup.find_all(attrs={"class": NOISE_CLASSES_IDS}):
                # Keep if it contains an exceptionally high number of academic keywords
                text = el.get_text()
                if not ContentPruner._is_high_value_container(text):
                    el.decompose()

            for el in soup.find_all(attrs={"id": NOISE_CLASSES_IDS}):
                text = el.get_text()
                if not ContentPruner._is_high_value_container(text):
                    el.decompose()

            # 3. Locate candidate high-density containers (tables, cards, article, main)
            candidate_blocks: List[Tuple[int, str]] = []

            # Check main or body
            container = soup.find("main") or soup.find("article") or soup.find("body") or soup

            # Scan tables, grids, and staff card lists
            staff_containers = container.find_all(["table", "ul", "div", "section"])
            visited_nodes = set()

            for node in staff_containers:
                if id(node) in visited_nodes:
                    continue

                text = node.get_text(separator="\n", strip=True)
                score = ContentPruner._calculate_academic_density_score(text)
                if score >= 3 and len(text) > 80:
                    candidate_blocks.append((score, text))
                    # Mark all children visited to avoid duplicate nested text
                    for child in node.find_all(["table", "ul", "div", "section"]):
                        visited_nodes.add(id(child))

            # 4. If dense containers found, sort by density and join
            if candidate_blocks:
                # Deduplicate and sort highest score first
                seen_texts = set()
                final_texts = []
                for _, block_text in sorted(candidate_blocks, key=lambda x: x[0], reverse=True):
                    sample = block_text[:100]
                    if sample not in seen_texts:
                        seen_texts.add(sample)
                        final_texts.append(block_text)

                combined = "\n\n---\n\n".join(final_texts)
                return combined[:max_output_chars]

            # Fallback: General text cleaning
            cleaned_text = container.get_text(separator="\n", strip=True)
            # Remove excessive consecutive blank lines
            cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
            return cleaned_text[:max_output_chars]

        except Exception:
            return html_content[:max_output_chars]

    @staticmethod
    def _is_high_value_container(text: str) -> bool:
        """Determines if a container has too many academic markers to be dismissed as noise."""
        if not text:
            return False
        count = sum(1 for kw in ACADEMIC_KEYWORDS if kw in text.lower())
        return count >= 4

    @staticmethod
    def _calculate_academic_density_score(text: str) -> int:
        """Scores text block based on occurrence of academic titles and entities."""
        if not text:
            return 0
        score = 0
        text_lower = text.lower()
        for kw in ACADEMIC_KEYWORDS:
            if kw in text_lower:
                score += text_lower.count(kw)
        return score
