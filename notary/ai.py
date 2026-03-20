"""ScholarAgent — Gemini-powered SC Notary law reference assistant."""

from pathlib import Path

from google import genai
from google.genai import types as gentypes

from . import config as cfg
from .log import get_logger

log = get_logger("notary.ai")
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

SYSTEM_PROMPT_TEMPLATE = """\
You are the Notary Scholar assistant for {business_name}, a notary public practice in South Carolina \
operated by {notary_name}. Your sole purpose is to help the notary understand South Carolina notary \
law and procedures.

STRICT RULES — you must follow these without exception:
1. Answer ONLY from the SC Notary Public Reference Manual provided below. Do not use outside knowledge.
2. NEVER draft, compose, or suggest wording for any legal document, affidavit, contract, deed, will, \
   power of attorney, or any other legal instrument. Refuse politely and explain this is the unauthorized \
   practice of law (UPL).
3. NEVER give legal advice. You explain notary procedures, not legal strategy or outcomes.
4. If a question is outside the manual or requires legal judgment, say so clearly and direct the user \
   to consult the SC Secretary of State's office or a licensed SC attorney.
5. Always be accurate, cite the relevant section of the manual when possible, and be concise.
6. You may help the notary understand what type of notarial act is appropriate for a given document, \
   explain certificate wording requirements, and clarify procedural steps.

--- SC NOTARY PUBLIC REFERENCE MANUAL ---
{manual_content}
--- END OF MANUAL ---
{supplemental_section}"""

SUPPLEMENTAL_TEMPLATE = """

--- SUPPLEMENTAL REFERENCE DOCUMENT: {doc_name} ---
{supplemental_content}
--- END OF SUPPLEMENTAL DOCUMENT ---

When answering, draw from both the SC Notary Manual above and this supplemental document. \
The manual takes precedence on matters of SC notary law."""


class ScholarAgent:
    """Gemini chat agent with the SC Notary Manual injected as context."""

    def __init__(self, supplemental_content: str = "", supplemental_name: str = ""):
        config = cfg.load()
        api_key = cfg.get_gemini_key()
        if not api_key:
            raise RuntimeError("No Gemini API key configured. Go to Settings to add your key.")

        self.client = genai.Client(api_key=api_key)
        self.model_name = config.get("gemini_model", "gemini-2.5-flash")
        log.info("ScholarAgent initializing — model: %s", self.model_name)

        manual_content = self._load_manual()

        if supplemental_content:
            supplemental_section = SUPPLEMENTAL_TEMPLATE.format(
                doc_name=supplemental_name or "Supplemental Document",
                supplemental_content=supplemental_content,
            )
            log.info("Supplemental document loaded: %s (%d chars)", supplemental_name, len(supplemental_content))
        else:
            supplemental_section = ""

        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            business_name=config.get("business_name", "Stamp and Certify Co"),
            notary_name=config.get("notary_name", "the notary"),
            manual_content=manual_content,
            supplemental_section=supplemental_section,
        )

        self.history: list = []

    def _load_manual(self) -> str:
        """Load manual from knowledge/. Supports .pdf and .md files."""
        pdfs = list(KNOWLEDGE_DIR.glob("*.pdf"))
        mds = list(KNOWLEDGE_DIR.glob("*.md"))

        if pdfs:
            log.info("Loading manual from PDF: %s", pdfs[0].name)
            return self._extract_pdf(pdfs[0])
        if mds:
            log.info("Loading manual from markdown: %s", mds[0].name)
            return mds[0].read_text(encoding="utf-8")

        log.warning("No manual found in knowledge/")
        return (
            "[SC Notary Public Reference Manual not found. "
            "Please place sc_notary_manual.pdf (or .md) in the knowledge/ directory. "
            "Until then, answer general SC notary questions to the best of your ability "
            "while still refusing to give legal advice or draft documents.]"
        )

    def _extract_pdf(self, path: Path) -> str:
        """Extract all text from a PDF using pypdf."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except ImportError:
            return (
                "[pypdf is not installed. Run: pip install pypdf]\n"
                "[Cannot read PDF without pypdf.]"
            )
        except Exception as e:
            return f"[Error reading PDF: {e}]"

    @staticmethod
    def extract_uploaded_file(file_bytes: bytes, filename: str) -> str:
        """Extract text from an uploaded file (PDF or text). Called from UI."""
        if filename.lower().endswith(".pdf"):
            try:
                import io
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(file_bytes))
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n\n".join(pages)
            except Exception as e:
                return f"[Error reading uploaded PDF: {e}]"
        else:
            try:
                return file_bytes.decode("utf-8")
            except Exception as e:
                return f"[Error reading uploaded file: {e}]"

    def send(self, user_message: str) -> str:
        """Send a message, maintain history, return response text."""
        self.history.append(gentypes.Content(role="user", parts=[gentypes.Part(text=user_message)]))

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=self.history,
            config=gentypes.GenerateContentConfig(
                system_instruction=self.system_prompt,
            ),
        )

        reply = response.text
        self.history.append(gentypes.Content(role="model", parts=[gentypes.Part(text=reply)]))
        log.debug("Scholar exchange — user: %d chars, reply: %d chars", len(user_message), len(reply))
        return reply

    def summarize(self) -> str:
        """Ask Gemini to summarize the current conversation. Does not affect history."""
        if not self.history:
            return ""
        transcript = self.get_transcript()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=f"Please summarize the following notary consultation in 3-5 sentences. "
                     f"Focus on the key questions asked and the guidance provided:\n\n{transcript}",
            config=gentypes.GenerateContentConfig(
                system_instruction="You are summarizing a legal reference consultation. Be concise and factual.",
            ),
        )
        return response.text

    def get_transcript(self) -> str:
        """Return the conversation as a readable plain-text string."""
        parts = []
        for msg in self.history:
            role = "Notary" if msg.role == "user" else "Scholar"
            text = msg.parts[0].text if msg.parts else ""
            parts.append(f"{role}:\n{text}")
        return "\n\n---\n\n".join(parts)

    def reset(self) -> None:
        """Clear chat history."""
        self.history = []
