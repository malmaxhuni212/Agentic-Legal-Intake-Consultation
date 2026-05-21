"""
Legal Intake & Retainer Generation System — FastAPI Backend Pipeline
====================================================================
Dual-model Groq architecture:
  • Node 1 (Extraction)  → llama-3.1-8b-instant  via instructor
  • Node 2 (Conflict)    → mock CRM gate
  • Node 3 (Synthesis)   → llama-3.3-70b-versatile
  • Node 4 (PDF)         → markdown2 → pdfkit
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import markdown2
import pdfkit
import instructor
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from groq import Groq

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hardcoded API Credentials
# ---------------------------------------------------------------------------
GROQ_API_KEY = "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"

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Legal Intake Pipeline",
    version="1.0.0",
    description="Automated legal-intake extraction, conflict checking, and retainer-agreement generation.",
)

# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class ConsultationPayload(BaseModel):
    """Incoming webhook payload."""
    transcript: str


class LegalIntakeContext(BaseModel):
    """Structured data extracted from a consultation transcript."""
    client_full_name: str = Field(..., description="Full legal name of the prospective client.")
    opposing_party_name: str = Field(
        default="None",
        description="Full name of the opposing party. Use 'None' if not mentioned.",
    )
    legal_matter_type: str = Field(..., description="Category of legal matter (e.g., Contract Dispute, Employment Law).")
    case_summary: str = Field(..., description="Concise 2-4 sentence summary of the case facts.")
    agreed_fee_structure: str = Field(
        ...,
        description="Fee arrangement discussed (e.g., hourly, flat fee, contingency).",
    )


class PipelineResponse(BaseModel):
    """Final response returned to the caller."""
    extracted_metadata: dict
    conflict_detected: bool
    conflict_warning: Optional[str] = None
    retainer_agreement_markdown: str

# ---------------------------------------------------------------------------
# Groq Clients
# ---------------------------------------------------------------------------

def _get_groq_client() -> Groq:
    """Return a vanilla Groq client (reads GROQ_API_KEY from env, defaulting to integrated key)."""
    api_key = os.environ.get("GROQ_API_KEY") or GROQ_API_KEY
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set.")
    return Groq(api_key=api_key)


def _get_instructor_client():
    """Return an instructor-patched Groq client for structured extraction."""
    return instructor.from_groq(_get_groq_client())

# ---------------------------------------------------------------------------
# Node 2 — Conflict-Check Gate (mock CRM)
# ---------------------------------------------------------------------------

def check_crm_conflict(opposing_party: str) -> bool:
    """
    Simulate a CRM conflict-of-interest check.

    Returns True if the opposing party matches a known conflicting name,
    indicating the firm has a prior relationship with that party.
    """
    CONFLICTING_NAMES = {"michael johnson"}
    return opposing_party.strip().lower() in CONFLICTING_NAMES

# ---------------------------------------------------------------------------
# Node 1 — Extraction
# ---------------------------------------------------------------------------

def extract_intake_context(transcript: str) -> LegalIntakeContext:
    """Use the 8B model via instructor to extract structured intake data."""
    client = _get_instructor_client()

    logger.info("Node 1 ▸ Extracting structured intake context …")

    context: LegalIntakeContext = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        response_model=LegalIntakeContext,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a legal-intake data extraction assistant. "
                    "Carefully read the consultation transcript and extract "
                    "the required fields. If a field is not mentioned, use a "
                    "sensible default as described in the schema."
                ),
            },
            {
                "role": "user",
                "content": f"CONSULTATION TRANSCRIPT:\n\n{transcript}",
            },
        ],
    )

    logger.info("Node 1 ▸ Extraction complete: %s", context.client_full_name)
    return context

# ---------------------------------------------------------------------------
# Node 3 — Agreement Synthesis
# ---------------------------------------------------------------------------

FIRM_SYSTEM_PROMPT = """\
You are the senior drafting attorney at **the Law Firm**, a prestigious
full-service corporate law firm headquartered in New York City.

FIRM PRICING RULES:
• Standard retainer deposit: $5,000
• Hourly rate — Partner: $650/hr | Senior Associate: $450/hr | Associate: $325/hr
• Contingency cases: 33.3% of recovery
• Flat-fee arrangements are quoted on a per-matter basis and require partner approval

INSTRUCTIONS:
Using the extracted case metadata below, draft a clean, professional legal retainer
agreement in **Markdown** format. The agreement must include:

1. Title and date
2. Parties (firm and client)
3. Scope of representation
4. Fee structure & retainer deposit
5. Billing & payment terms
6. Client obligations
7. Termination clause
8. Governing law (New York)
9. Signature blocks

Write in formal legal language. Do NOT include any commentary outside the agreement.
"""


def synthesize_retainer_agreement(
    context: LegalIntakeContext,
    conflict_warning: Optional[str] = None,
) -> str:
    """Use the 70B model to generate a Markdown retainer agreement."""
    client = _get_groq_client()

    metadata_block = (
        f"CLIENT NAME: {context.client_full_name}\n"
        f"OPPOSING PARTY: {context.opposing_party_name}\n"
        f"MATTER TYPE: {context.legal_matter_type}\n"
        f"CASE SUMMARY: {context.case_summary}\n"
        f"FEE STRUCTURE: {context.agreed_fee_structure}\n"
    )

    if conflict_warning:
        metadata_block += f"\n⚠️ CONFLICT WARNING: {conflict_warning}\n"

    logger.info("Node 3 ▸ Synthesizing retainer agreement …")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": FIRM_SYSTEM_PROMPT},
            {"role": "user", "content": metadata_block},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    markdown_text = response.choices[0].message.content
    logger.info("Node 3 ▸ Agreement synthesis complete.")
    return markdown_text

# ---------------------------------------------------------------------------
# Node 4 — PDF Compilation
# ---------------------------------------------------------------------------

def compile_pdf(markdown_text: str) -> bytes:
    """Convert Markdown → HTML → PDF bytes."""
    html_body = markdown2.markdown(
        markdown_text,
        extras=["tables", "fenced-code-blocks", "header-ids"],
    )

    full_html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: 'Georgia', 'Times New Roman', serif;
        margin: 60px 80px;
        font-size: 13px;
        line-height: 1.7;
        color: #1a1a1a;
    }}
    h1 {{ font-size: 22px; text-align: center; margin-bottom: 4px; }}
    h2 {{ font-size: 16px; margin-top: 28px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
    h3 {{ font-size: 14px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
    th, td {{ border: 1px solid #999; padding: 6px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    logger.info("Node 4 ▸ Compiling PDF …")

    try:
        pdf_bytes = pdfkit.from_string(full_html, False, options={"quiet": ""})
    except OSError as exc:
        logger.error("PDF compilation failed — is wkhtmltopdf installed? %s", exc)
        raise RuntimeError(
            "PDF generation failed. Ensure wkhtmltopdf is installed and on your PATH."
        ) from exc

    logger.info("Node 4 ▸ PDF compiled (%d bytes).", len(pdf_bytes))
    return pdf_bytes

# ---------------------------------------------------------------------------
# Webhook Endpoint
# ---------------------------------------------------------------------------

@app.post("/webhook/consultation-ended", response_model=PipelineResponse)
async def consultation_ended(payload: ConsultationPayload):
    """
    Main pipeline endpoint.

    Receives a consultation transcript and returns:
      • Extracted metadata
      • Conflict-check result
      • Generated Markdown retainer agreement
    """
    transcript = payload.transcript.strip()

    # Guard: transcript length
    word_count = len(transcript.split())
    if word_count < 100:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Transcript is too short ({word_count} words). "
                "A minimum of 100 words is required for reliable extraction."
            ),
        )

    try:
        # ── Node 1: Extraction ─────────────────────────────────────────
        context = extract_intake_context(transcript)

        # ── Node 2: Conflict-check gate ────────────────────────────────
        conflict_detected = check_crm_conflict(context.opposing_party_name)
        conflict_warning = None

        if conflict_detected:
            conflict_warning = (
                f"CONFLICT OF INTEREST DETECTED — The opposing party "
                f"'{context.opposing_party_name}' is a current or former client "
                f"of the Law Firm. This matter MUST be reviewed by the "
                f"Ethics & Compliance Committee before any engagement letter is executed."
            )
            logger.warning("Node 2 ▸ %s", conflict_warning)
        else:
            logger.info("Node 2 ▸ No conflict detected for '%s'.", context.opposing_party_name)

        # ── Node 3: Synthesis ──────────────────────────────────────────
        retainer_md = synthesize_retainer_agreement(context, conflict_warning)

        # ── Node 4: PDF (fire-and-forget; PDF bytes not returned via JSON)
        try:
            compile_pdf(retainer_md)
        except RuntimeError:
            logger.warning("PDF compilation skipped (wkhtmltopdf may not be installed).")

        # ── Response ───────────────────────────────────────────────────
        return PipelineResponse(
            extracted_metadata=context.model_dump(),
            conflict_detected=conflict_detected,
            conflict_warning=conflict_warning,
            retainer_agreement_markdown=retainer_md,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Pipeline error")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}") from exc


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Legal Intake Pipeline"}
