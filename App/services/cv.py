import json
import pdfplumber
import tempfile
from App.services.llm import llm_service


EXTRACT_PROMPT = """
You are a CV parser. Extract structured information from the CV text below.
Return ONLY a valid JSON object with no extra text, no markdown, no backticks.

JSON format:
{{
  "name": "candidate full name or null",
  "education": "education background as a single descriptive string or null",
  "experience_years": 0.0,
  "topics": ["skill1", "skill2", "..."]
}}

Rules:
- topics must include: technical skills, programming languages, frameworks, tools, domains
- experience_years should be a float (e.g. 3.5), estimate from dates if not explicit, 0 if unknown
- education should be a concise string e.g. "BSc Computer Science, Cairo University, 2020"
- topics should be specific, avoid vague words like "communication" or "teamwork"

CV Text:
{cv_text}
"""

SUMMARY_PROMPT = """
Write a concise 3-sentence professional summary of the following CV.
Focus on: who they are, what they specialize in, and their experience level.
Return only the summary text, no labels or extra formatting.

CV Text:
{cv_text}
"""


class CVService:

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract raw text from PDF bytes using pdfplumber."""
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            with pdfplumber.open(tmp.name) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()

    @staticmethod
    async def analyze_cv(full_text: str) -> dict:
        """Use LLM to extract structured info from CV text."""
        prompt = EXTRACT_PROMPT.format(cv_text=full_text[:6000])  # cap to avoid token overflow
        raw = await llm_service.chat([{"role": "user", "content": prompt}])

        try:
            # Strip any accidental markdown fences just in case
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(cleaned)
        except Exception:
            # Fallback: return empty structure so upload doesn't crash
            return {
                "name": None,
                "education": None,
                "experience_years": 0.0,
                "topics": []
            }

    @staticmethod
    async def generate_summary(full_text: str) -> str:
        """Generate a professional summary of the CV."""
        prompt = SUMMARY_PROMPT.format(cv_text=full_text[:6000])
        return await llm_service.chat([{"role": "user", "content": prompt}])

    @staticmethod
    async def build_skill_rows(analyzed: dict) -> list[dict]:
        """
        Build skill rows to embed and store.
        Each row: { skill: str, category: str, embedding: list[float] }

        We embed 3 categories:
          - topics        → individual skill strings
          - education     → education string
          - experience    → "X years of experience" string
        """
        rows = []
        texts_to_embed = []
        meta = []

        # Topics
        for topic in analyzed.get("topics", []):
            if topic and topic.strip():
                texts_to_embed.append(topic.strip())
                meta.append({"skill": topic.strip(), "category": "topic"})

        # Education
        education = analyzed.get("education")
        if education:
            texts_to_embed.append(education)
            meta.append({"skill": education, "category": "education"})

        # Experience
        exp = analyzed.get("experience_years")
        if exp and exp > 0:
            exp_str = f"{exp} years of experience"
            texts_to_embed.append(exp_str)
            meta.append({"skill": exp_str, "category": "experience"})

        if not texts_to_embed:
            return rows

        # Batch embed all at once
        embeddings = await llm_service.emb(texts_to_embed)

        for i, emb in enumerate(embeddings):
            rows.append({
                "skill": meta[i]["skill"],
                "category": meta[i]["category"],
                "embedding": emb
            })

        return rows


cv_service = CVService()
