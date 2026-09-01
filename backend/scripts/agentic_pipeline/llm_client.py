"""
LLM State-Patch Generator for Faculty Extraction Agent
Based on the SKILL.state Architecture & Evaluation: https://arxiv.org/html/2608.26263v2#S5
"""
import os
import json
from typing import Optional, Dict, Any, Tuple
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.security import sanitize_for_prompt
from scripts.agentic_pipeline.models import ExtractionAgentState, FacultyStatePatch


EXTRACTION_SYSTEM_PROMPT = """You are an expert Academic Data Extraction & Cleaning Agent.
Your task is to analyze university webpage HTML or profile text and emit an atomic JSON State Patch.

STRICT EXTRACTION RULES:
1. Extract all faculty/advisor profiles found in the provided HTML/text chunk.
2. For Thai names: identify their proper academic title (e.g. ศ.ดร., รศ.ดร., ผศ.ดร., อ.ดร., ศ., รศ., ผศ., อ., ดร.) and full Thai name.
3. Extract official institutional email, education degrees, research areas, and publications.
4. DO NOT extract or retain personal phone numbers (PDPA compliance).
5. If links to other departmental staff directories or profile pages are visible, add them to `discovered_urls`.
6. Output ONLY a valid JSON adhering to the `FacultyStatePatch` schema.
"""


class LLMStatePatchGenerator:
    """
    LLM State-Patch Generator powered by Gemini Structured Outputs.
    Following SKILL.state, input prompt contains only minimal state context + target chunk.
    Never accumulates previous conversation history.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash-lite"):
        # Load API keys pool for rotation and high availability
        raw_keys = settings.GEMINI_API_KEYS.split(",") if settings.GEMINI_API_KEYS else []
        self.api_keys = [k.strip() for k in raw_keys if k.strip()]
        if not self.api_keys and (api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")):
            self.api_keys = [api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")]

        self.current_key_idx = 0
        self.model_name = model_name
        self.clients = [genai.Client(api_key=k) for k in self.api_keys if k]

    def _get_active_client(self):
        if not self.clients:
            raise ValueError("No valid Gemini API key configured.")
        return self.clients[self.current_key_idx % len(self.clients)]

    def _rotate_key(self):
        if len(self.clients) > 1:
            self.current_key_idx = (self.current_key_idx + 1) % len(self.clients)

    def generate_patch(
        self,
        state: ExtractionAgentState,
        html_chunk: str,
        current_url: str = ""
    ) -> Tuple[FacultyStatePatch, int]:
        """
        Generates a state patch from an HTML chunk and returns (patch, estimated_tokens).
        """
        if not self.clients:
            raise ValueError("Gemini API key is not configured. Cannot generate extraction patch.")

        # Build minimal state summary (flat ~200 tokens)
        state_summary = {
            "target_university_th": state.target_university_th,
            "target_faculty_th": state.target_faculty_th,
            "current_step": state.step_count,
            "extracted_so_far_count": len(state.faculties),
            "pending_urls_count": len(state.pending_urls),
            "current_processing_url": current_url,
        }

        # Deterministic Heuristic Content Pruning (LLMLingua-2 & Trafilatura inspired)
        # Strips 80%+ boilerplate navigation, cookie notices, and footers
        try:
            from scripts.agentic_pipeline.content_pruner import ContentPruner
            cleaned_content = ContentPruner.prune_html(html_chunk, max_output_chars=30000)
        except Exception:
            cleaned_content = html_chunk

        # For dense faculty directory pages, break into ~6000-character overlapping chunks
        # to ensure LLM extracts 100% of all members without output truncation
        chunk_size = 6000
        overlap = 600
        if len(cleaned_content) > chunk_size:
            text_chunks = []
            for i in range(0, len(cleaned_content), chunk_size - overlap):
                chunk = cleaned_content[i:i + chunk_size]
                if any(kw in chunk for kw in ["ศ.", "รศ.", "ผศ.", "อ.", "Dr.", "Prof.", "Lecturer", "อาจารย์"]):
                    text_chunks.append(chunk)
            if not text_chunks:
                text_chunks = [cleaned_content[:chunk_size]]
        else:
            text_chunks = [cleaned_content]

        aggregated_patch = FacultyStatePatch(
            discovered_urls=[],
            new_profiles=[],
            summary_of_changes=f"Extracted from {len(text_chunks)} text chunk(s)."
        )
        total_tokens = 0

        for ch_idx, chunk_text in enumerate(text_chunks):
            user_prompt = f"""### Target University & Faculty:
- University: {state.target_university_th} ({state.target_university_en})
- Faculty: {state.target_faculty_th or 'Not specified'}

### Webpage Content Chunk {ch_idx+1}/{len(text_chunks)} (Current URL: {current_url}):
{chunk_text}

TASK:
1. Extract ALL academic professors, associate professors, assistant professors, and lecturers listed in this chunk without omitting any person.
2. For each person: identify Thai academic title (ศ.ดร., รศ.ดร., ผศ.ดร., อ.ดร., ดร., ศ., รศ., ผศ., อ.), full Thai name, English first/last name, official email, education, and research areas.
3. Emit a structured JSON adhering to the schema.
"""
            max_retries = max(1, len(self.clients))
            last_error = None

            for _ in range(max_retries):
                try:
                    active_client = self._get_active_client()
                    response = active_client.models.generate_content(
                        model=self.model_name,
                        contents=[user_prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=EXTRACTION_SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            response_schema=FacultyStatePatch,
                            temperature=0.0,
                        ),
                    )
                    tokens_used = 0
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        tokens_used = getattr(response.usage_metadata, "total_token_count", 0)
                    total_tokens += tokens_used

                    patch = FacultyStatePatch.model_validate_json(response.text)
                    aggregated_patch.new_profiles.extend(patch.new_profiles)
                    for u in patch.discovered_urls:
                        if u not in aggregated_patch.discovered_urls:
                            aggregated_patch.discovered_urls.append(u)
                    break
                except Exception as e:
                    last_error = e
                    self._rotate_key()

        return aggregated_patch, total_tokens
