"""
Legal Intake & Retainer Generation System
=========================================
Single-file Streamlit application with embedded pipeline logic.
Deploys directly to Streamlit Cloud — no separate backend required.
"""

from __future__ import annotations

import os
import json
import logging
import requests
from datetime import datetime
from typing import Optional

import streamlit as st
import instructor
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
RECALL_API_KEY = "65c330da36dda1d28c3e344b6ed8a70d627fa2ca"

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Legal Intake Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — Premium Dark Glassmorphism Theme
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ─────────────────────────────────────────────────── */
    .stApp {
        background: linear-gradient(160deg, #0a0e1a 0%, #101829 40%, #0d1520 100%);
        font-family: 'Inter', sans-serif;
    }

    /* ── Header ─────────────────────────────────────────────────── */
    .dashboard-header {
        text-align: center;
        padding: 2.5rem 0 1.5rem 0;
    }
    .dashboard-header h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .dashboard-header p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.4rem;
        font-weight: 400;
    }
    .dashboard-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #334155, transparent);
        margin: 0 0 2rem 0;
    }

    /* ── Cards ──────────────────────────────────────────────────── */
    .glass-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        padding: 1.8rem 2rem;
        margin-bottom: 1.2rem;
        transition: border-color 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.35);
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .card-title .icon {
        font-size: 1.2rem;
    }

    /* ── Status Badges ─────────────────────────────────────────── */
    .badge-ok {
        display: inline-block;
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 0.35rem 1rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-conflict {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 0.35rem 1rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* ── Conflict Alert ────────────────────────────────────────── */
    .conflict-alert {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-left: 4px solid #ef4444;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
        color: #fca5a5;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .conflict-alert strong {
        color: #f87171;
        font-size: 1rem;
    }

    /* ── Success Card ──────────────────────────────────────────── */
    .success-card {
        background: rgba(34, 197, 94, 0.08);
        border: 1px solid rgba(34, 197, 94, 0.25);
        border-left: 4px solid #22c55e;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.8rem 0;
        color: #86efac;
        font-size: 0.9rem;
    }

    /* ── Streamlit overrides ───────────────────────────────────── */
    .stTextArea textarea {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(99, 102, 241, 0.25) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', monospace !important;
        font-size: 0.9rem !important;
        padding: 1rem !important;
    }
    .stTextArea textarea:focus {
        border-color: rgba(99, 102, 241, 0.6) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 0.3px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.35) !important;
    }

    div[data-testid="stJson"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 12px !important;
    }

    .stMarkdown {
        color: #cbd5e1;
    }

    /* ── Agreement Styling ─────────────────────────────────────── */
    .agreement-container {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 14px;
        padding: 2rem 2.2rem;
        color: #e2e8f0;
        line-height: 1.8;
    }

    /* ── Pipeline Steps ────────────────────────────────────────── */
    .step-indicator {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.6rem 0;
        color: #94a3b8;
        font-size: 0.88rem;
    }
    .step-indicator.active {
        color: #a78bfa;
        font-weight: 600;
    }
    .step-indicator.done {
        color: #4ade80;
    }

    /* ── Footer ────────────────────────────────────────────────── */
    .dashboard-footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: #475569;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Pydantic Schema for Extraction
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Pipeline Functions
# ---------------------------------------------------------------------------

def get_groq_client(api_key: str) -> Groq:
    """Return a vanilla Groq client."""
    return Groq(api_key=api_key)


def get_instructor_client(api_key: str):
    """Return an instructor-patched Groq client."""
    return instructor.from_groq(get_groq_client(api_key))


def check_crm_conflict(opposing_party: str) -> bool:
    """
    Mock CRM conflict-of-interest check.
    Returns True if opposing party is 'Michael Johnson'.
    """
    CONFLICTING_NAMES = {"michael johnson"}
    return opposing_party.strip().lower() in CONFLICTING_NAMES


def extract_intake_context(api_key: str, transcript: str) -> LegalIntakeContext:
    """Node 1: Use the 8B model via instructor to extract structured intake data."""
    client = get_instructor_client(api_key)

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
    return context


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
    api_key: str,
    context: LegalIntakeContext,
    conflict_warning: Optional[str] = None,
) -> str:
    """Node 3: Use the 70B model to generate a Markdown retainer agreement."""
    client = get_groq_client(api_key)

    metadata_block = (
        f"CLIENT NAME: {context.client_full_name}\n"
        f"OPPOSING PARTY: {context.opposing_party_name}\n"
        f"MATTER TYPE: {context.legal_matter_type}\n"
        f"CASE SUMMARY: {context.case_summary}\n"
        f"FEE STRUCTURE: {context.agreed_fee_structure}\n"
    )

    if conflict_warning:
        metadata_block += f"\n⚠️ CONFLICT WARNING: {conflict_warning}\n"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": FIRM_SYSTEM_PROMPT},
            {"role": "user", "content": metadata_block},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Meetings Database Functions (Persistence)
# ---------------------------------------------------------------------------
MEETINGS_DB_PATH = "meetings_db.json"

def load_meetings_db() -> dict:
    """Load the locally persisted meetings database."""
    if not os.path.exists(MEETINGS_DB_PATH):
        return {}
    try:
        with open(MEETINGS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading meetings database: {e}")
        return {}

def save_meetings_db(db: dict):
    """Save the meetings database to a local JSON file."""
    try:
        with open(MEETINGS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving meetings database: {e}")

# ---------------------------------------------------------------------------
# Recall.ai Integration Functions
# ---------------------------------------------------------------------------
def format_recall_transcript(transcript_data) -> str:
    """Format Recall.ai utterance-level JSON transcript into standard format."""
    if not isinstance(transcript_data, list):
        return str(transcript_data)
    
    lines = []
    for idx, utterance in enumerate(transcript_data):
        if not isinstance(utterance, dict):
            continue
        speaker = utterance.get("speaker")
        if not speaker:
            participant = utterance.get("participant")
            if isinstance(participant, dict):
                speaker = participant.get("name")
        if not speaker:
            speaker = f"Speaker {idx+1}"
            
        words = utterance.get("words", [])
        if isinstance(words, list):
            text = " ".join([w.get("text", "") for w in words if isinstance(w, dict) and "text" in w]).strip()
        else:
            text = str(words)
            
        if text:
            lines.append(f"{speaker}: {text}")
    return "\n\n".join(lines)


def create_recall_bot(meeting_url: str, region: str = "us-east-1") -> str:
    """Create a Recall.ai bot to join the meeting URL."""
    recall_api_host = "api.recall.ai" if region == "us-east-1" else f"{region}.recall.ai"
    url = f"https://{recall_api_host}/api/v1/bot"
    
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "meeting_url": meeting_url,
        "bot_name": "Legal Notetaker",
        "recording_config": {
            "transcript": {
                "provider": {
                    "recallai_streaming": {}
                }
            }
        }
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    if response.status_code in (200, 201):
        return response.json()["id"]
    else:
        raise RuntimeError(f"Recall.ai error ({response.status_code}): {response.text}")


def check_recall_bot_status(bot_id: str, region: str = "us-east-1") -> dict:
    """Retrieve current status of a Recall.ai bot."""
    recall_api_host = "api.recall.ai" if region == "us-east-1" else f"{region}.recall.ai"
    url = f"https://{recall_api_host}/api/v1/bot/{bot_id}/"
    
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        bot_data = response.json()
        status_value = bot_data.get("status")
        # Handle list vs string
        if isinstance(status_value, list) and len(status_value) > 0:
            status_str = status_value[-1]
        else:
            status_str = str(status_value)
        return {
            "status": status_str,
            "raw": bot_data
        }
    else:
        raise RuntimeError(f"Recall.ai status error ({response.status_code}): {response.text}")


def get_recall_bot_transcript(bot_id: str, region: str = "us-east-1") -> str:
    """Fetch transcript from Recall.ai and format it."""
    recall_api_host = "api.recall.ai" if region == "us-east-1" else f"{region}.recall.ai"
    url = f"https://{recall_api_host}/api/v1/bot/{bot_id}/transcript/"
    
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code == 200:
        return format_recall_transcript(response.json())
    else:
        raise RuntimeError(f"Recall.ai transcript error ({response.status_code}): {response.text}")


def refresh_bot_status(bot_id: str, db: dict, region: str) -> bool:
    """Check status of a bot, download transcript and auto-run pipeline if done."""
    try:
        res = check_recall_bot_status(bot_id, region)
        status_str = res["status"]
        db[bot_id]["status"] = status_str
        
        # If terminal status and transcript is not yet fetched
        if status_str in ("done", "call_ended", "recording_done", "analysis_done") and not db[bot_id].get("transcript"):
            # Fetch transcript
            transcript = get_recall_bot_transcript(bot_id, region)
            db[bot_id]["transcript"] = transcript
            
            # Auto-run legal pipeline
            word_count = len(transcript.split())
            if word_count >= 100:
                # Node 1: Extraction
                context = extract_intake_context(GROQ_API_KEY, transcript)
                db[bot_id]["extracted_metadata"] = context.model_dump()
                
                # Node 2: Conflict Check
                conflict_detected = check_crm_conflict(context.opposing_party_name)
                db[bot_id]["conflict_detected"] = conflict_detected
                
                conflict_warning = None
                if conflict_detected:
                    conflict_warning = (
                        f"CONFLICT OF INTEREST DETECTED — The opposing party "
                        f"'{context.opposing_party_name}' is a current or former client "
                        f"of the Law Firm. This matter MUST be reviewed by the "
                        f"Ethics & Compliance Committee before any engagement letter is executed."
                    )
                db[bot_id]["conflict_warning"] = conflict_warning
                
                # Node 3: Synthesis
                retainer_md = synthesize_retainer_agreement(GROQ_API_KEY, context, conflict_warning)
                db[bot_id]["retainer_agreement_markdown"] = retainer_md
            else:
                db[bot_id]["error"] = f"Transcript is too short ({word_count} words). Minimum 100 words is required."
        elif status_str == "fatal":
            db[bot_id]["error"] = "Recall.ai bot failed with a fatal error."
            
        save_meetings_db(db)
        return True
    except Exception as e:
        logger.error(f"Error refreshing bot status for {bot_id}: {e}")
        db[bot_id]["error"] = str(e)
        save_meetings_db(db)
        return False


# ---------------------------------------------------------------------------
# Sample Transcript
# ---------------------------------------------------------------------------

SAMPLE_TRANSCRIPT = """Attorney Sarah Mitchell: Good morning, please come in and have a seat. I'm Sarah Mitchell, senior partner here at the Law Firm. Thank you for coming in today.

Client David Reynolds: Thank you, Ms. Mitchell. I appreciate you seeing me on such short notice. I've been dealing with a situation that's been keeping me up at night.

Attorney: Of course, that's what we're here for. Why don't you start by telling me a little about yourself and what brings you in today?

Client: Sure. My name is David Reynolds. I'm 42, and I've been running a mid-size logistics company called Reynolds Supply Chain Solutions for the past twelve years. We handle warehousing and last-mile delivery for e-commerce brands, mostly on the East Coast. Things were going well until about six months ago when we entered into a partnership agreement with a company run by Michael Johnson.

Attorney: Tell me more about this partnership and what went wrong.

Client: Michael Johnson runs a tech startup called SwiftRoute Technologies. The idea was that his company would provide AI-driven route optimization software exclusively for our fleet, and in return, we'd give them a fifteen percent equity stake in a new joint venture we were forming. We signed a partnership agreement and I personally invested around three hundred and fifty thousand dollars to integrate their software into our systems.

Attorney: I see. And when did things start to break down?

Client: Almost immediately after we finished integration, about three months in. I discovered that Michael had been licensing the exact same proprietary software to two of our direct competitors. This was explicitly prohibited under our exclusivity clause in Section 4.2 of the partnership agreement. When I confronted him about it, he denied it at first, then claimed that the exclusivity clause only applied to our geographic region, which is nonsense because the contract clearly states nationwide exclusivity.

Attorney: That does sound like a clear breach of contract. Do you have documentation of these competing licenses?

Client: Yes, I have email correspondence where his own sales team accidentally copied my operations manager on a proposal to one of our competitors. I also have the original signed partnership agreement, financial records of my investment, and internal communications showing the damages we've suffered. Our client retention rate dropped by twenty percent since their competitors got the same software advantage.

Attorney: That's strong evidence. Based on what you're describing, this appears to be a straightforward breach of contract case with potential claims for fraud and misrepresentation. Have you attempted any resolution directly with Mr. Johnson?

Client: I sent a formal demand letter through my previous attorney about two months ago, but Michael's lawyers responded saying they disagree with our interpretation of the exclusivity clause and they have no intention of settling. That's when I decided I needed a firm with more litigation firepower, which is why I'm here.

Attorney: You've come to the right place. Our law firm has extensive experience in commercial litigation and partnership disputes. Let me outline what I'd recommend. First, we'd file a breach of contract action in New York State Supreme Court, seeking compensatory damages for your direct losses, which based on what you've described could be in the range of five hundred thousand to seven hundred and fifty thousand dollars when you factor in lost revenue and the diminished value of your investment. We may also pursue punitive damages given the alleged fraudulent misrepresentation.

Client: That sounds like exactly what I need. What would the fee arrangement look like?

Attorney: Given the strength of your case and the clear documentation you have, I'd recommend we proceed on a hybrid fee structure. We'd charge a reduced hourly rate of three hundred and twenty-five dollars per hour for an associate and four hundred and fifty for my time as the lead partner, with a standard retainer deposit upfront. If we proceed to trial and win, we'd also take a small success fee of ten percent of any recovery above the base damages. Does that sound reasonable to you?

Client: Yes, that works for me. I just want to make sure this gets resolved properly and that Michael Johnson is held accountable for what he's done to my business.

Attorney: Absolutely. We'll prepare the retainer agreement and have it ready for your signature by end of day. We'll also begin our initial case assessment and start preparing the complaint. Is there anything else you'd like to discuss today?

Client: No, I think that covers everything. Thank you, Ms. Mitchell. I feel much better about this already.

Attorney: You're welcome, David. We'll take good care of this for you. My assistant will walk you out and schedule our next meeting. Welcome to the Law Firm."""

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="dashboard-header">
        <h1>⚖️ Legal Intake Dashboard</h1>
        <p>AI-Powered Consultation Processing &bull; Conflict Detection &bull; Retainer Generation</p>
    </div>
    <div class="dashboard-divider"></div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — API Key Info & Configuration
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Sidebar — Clean Navigation & Branding
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0; text-align: center;">
            <div style="font-size: 2.2rem; margin-bottom: 0.4rem;">⚖️</div>
            <h3 style="color: #e2e8f0; margin: 0; font-size: 1.3rem; font-weight: 700; letter-spacing: -0.3px;">Legal Intake</h3>
            <p style="color: #64748b; font-size: 0.8rem; margin: 0.2rem 0 0 0;">Intake & Retainer Engine</p>
        </div>
        <div style="height: 1px; background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.25), transparent); margin: 0.5rem 0 1.5rem 0;"></div>
        """,
        unsafe_allow_html=True
    )
    
    menu_selection = st.radio(
        "Navigation",
        options=["⚖️ Dashboard", "📖 User Instructions", "⚙️ System Settings"],
        label_visibility="collapsed"
    )

# ---------------------------------------------------------------------------
# Navigation Views
# ---------------------------------------------------------------------------
def render_instructions():
    st.markdown(
        '<div class="card-title"><span class="icon">📖</span> Software Instructions & User Guide</div>',
        unsafe_allow_html=True,
    )
    tab_ov, tab_man, tab_bot, tab_rules = st.tabs([
        "🔍 System Overview",
        "📝 Manual Intake",
        "📹 Google Meet Bot",
        "⚖️ Pricing & Conflict Rules"
    ])
    
    with tab_ov:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color:#60a5fa; margin-top:0;">Dual-Model Legal Intake Architecture</h4>
            <p>The Legal Intake System is an automated workflow that processes legal consultations using state-of-the-art LLMs via Groq:</p>
            <ul>
                <li><strong>Node 1 (Extraction)</strong>: <code>llama-3.1-8b-instant</code> parses the raw transcript to extract structured data (Client, Opposing Party, Matter, Case Summary, Fee Structure) using Pydantic enforcement.</li>
                <li><strong>Node 2 (Conflict check)</strong>: Screens the opposing party against a mock CRM blocklist to identify conflicts.</li>
                <li><strong>Node 3 (Synthesis)</strong>: <code>llama-3.3-70b-versatile</code> drafts a professional retainer agreement based on firm rules and NY law.</li>
                <li><strong>Node 4 (PDF Compilation)</strong>: Compiles the generated agreement into printable PDF bytes (Node 4 will gracefully skip if wkhtmltopdf is not installed).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with tab_man:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color:#60a5fa; margin-top:0;">📝 Manual Intake Instructions</h4>
            <ol>
                <li>Navigate to the <strong>Dashboard</strong>.</li>
                <li>Ensure the mode switch is set to <strong>📝 Paste Consultation Transcript</strong>.</li>
                <li>Copy your consultation meeting transcript and paste it into the text area.
                    <ul>
                        <li><em>Note: A minimum of 100 words is required for reliable extraction.</em></li>
                    </ul>
                </li>
                <li>Click the <strong>⚡ Run Intake Pipeline</strong> button.</li>
                <li>The system will process the transcript. Results (Extracted Metadata, Conflict Warning, and the Generated Retainer) will render in the right panel.</li>
                <li>You can download the generated retainer agreement as a Markdown file.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    with tab_bot:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color:#60a5fa; margin-top:0;">📹 Google Meet Bot Instructions (Recall.ai)</h4>
            <ol>
                <li>Navigate to the <strong>Dashboard</strong>.</li>
                <li>Set the mode switch to <strong>📹 Deploy Google Meet Bot</strong>.</li>
                <li>Enter the full Google Meet meeting link (e.g. <code>https://meet.google.com/abc-defg-hij</code>).</li>
                <li>Click the <strong>🤖 Dispatch Notetaker Bot</strong> button.</li>
                <li>The bot will attempt to join the call. <strong>Important:</strong> A human participant must be present in the Google Meet call to click "Admit" for the <em>Legal Notetaker</em> participant.</li>
                <li>The bot will record and transcribe the call in real time.</li>
                <li>Once the meeting ends, the bot processes the audio, fetches the transcript, and automatically runs the conflict-retainer generation pipeline.</li>
                <li>Use the <strong>🔄 Refresh</strong> button next to the bot in the history list to fetch updates on the status.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    with tab_rules:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color:#f87171; margin-top:0;">⚠️ Conflict Check Rule</h4>
            <p>The mock CRM currently flags the opposing party name <strong>"Michael Johnson"</strong> (case-insensitive) as a conflict of interest, simulating a prior representation block.</p>
            <h4 style="color:#60a5fa; margin-top:1.5rem;">⚖️ Standard Retainer Clauses</h4>
            <ul>
                <li><strong>Retainer Deposit</strong>: $5,000 upfront.</li>
                <li><strong>Partner Hourly Rate</strong>: $650 / hr.</li>
                <li><strong>Senior Associate Rate</strong>: $450 / hr.</li>
                <li><strong>Associate Rate</strong>: $325 / hr.</li>
                <li><strong>Contingency Fee</strong>: 33.3% of recovery.</li>
                <li><strong>Governing Law</strong>: State of New York.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def render_settings():
    st.markdown(
        '<div class="card-title"><span class="icon">⚙️</span> System Settings</div>',
        unsafe_allow_html=True,
    )
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.session_state.recall_region = st.selectbox(
        "Recall.ai Region",
        options=["us-east-1", "us-west-2", "eu-central-1", "ap-northeast-1"],
        index=["us-east-1", "us-west-2", "eu-central-1", "ap-northeast-1"].index(st.session_state.recall_region),
        help="Select the region where your Recall.ai account was created."
    )
    st.markdown(
        f"""
        <p style="font-size:0.85rem; color:#94a3b8; margin-top:0.5rem; margin-bottom:0;">
            Current API host: <code>{"api.recall.ai" if st.session_state.recall_region == "us-east-1" else f"{st.session_state.recall_region}.recall.ai"}</code>
        </p>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:700; color:#e2e8f0; margin-bottom:0.8rem;">📊 Pipeline Model Specifications</div>', unsafe_allow_html=True)
    st.markdown("""
    - **Extraction Engine**: `llama-3.1-8b-instant` (Instructor compliant)
    - **Synthesis Engine**: `llama-3.3-70b-versatile` (Formal prose)
    - **Integrated API Credentials**:
      - Groq Key: `Integrated` (gsk_...SscKsDGo)
      - Recall.ai Key: `Integrated` (65c3...fa2ca)
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "active_view" not in st.session_state:
    st.session_state.active_view = "manual"
if "manual_results" not in st.session_state:
    st.session_state.manual_results = None
if "recall_region" not in st.session_state:
    st.session_state.recall_region = "us-east-1"

# Route Navigation Views
if menu_selection == "📖 User Instructions":
    render_instructions()
    st.stop()
elif menu_selection == "⚙️ System Settings":
    render_settings()
    st.stop()

recall_region = st.session_state.recall_region

# ---------------------------------------------------------------------------
# Layout — Two Columns
# ---------------------------------------------------------------------------
col_left, col_spacer, col_right = st.columns([5, 0.3, 6])

# ── LEFT COLUMN — Input ────────────────────────────────────────────────────
with col_left:
    input_mode = st.radio(
        "Choose Input Mode",
        options=["📝 Paste Consultation Transcript", "📹 Deploy Google Meet Bot"],
        label_visibility="collapsed",
        horizontal=True
    )

    if input_mode == "📝 Paste Consultation Transcript":
        st.markdown(
            '<div class="card-title"><span class="icon">📝</span> Consultation Transcript</div>',
            unsafe_allow_html=True,
        )

        transcript = st.text_area(
            label="Paste transcript",
            value=SAMPLE_TRANSCRIPT,
            height=460,
            label_visibility="collapsed",
            placeholder="Paste the full consultation transcript here …",
        )

        st.markdown("")
        run_clicked = st.button("⚡  Run Intake Pipeline", use_container_width=True)

        # ── Metrics Row ────────────────────────────────────────────────
        m1, m2, m3 = st.columns(3)
        word_count = len(transcript.split()) if transcript else 0
        m1.metric("Words", f"{word_count:,}")
        m2.metric("Min Required", "100")
        m3.metric("Status", "Ready" if word_count >= 100 else "Too Short")

        if run_clicked:
            if not transcript or not transcript.strip():
                st.error("⚠️ Please paste a consultation transcript before running the pipeline.")
            elif word_count < 100:
                st.error(f"⚠️ **Transcript too short** ({word_count} words). A minimum of 100 words is required.")
            else:
                try:
                    # Node 1: Extraction
                    with st.status("🧠 Running intake pipeline …", expanded=True) as status:
                        st.write("**Node 1** — Extracting structured data (Llama 3.1 8B) …")
                        context = extract_intake_context(GROQ_API_KEY, transcript)
                        st.write("✅ Extraction complete")

                        # Node 2: Conflict Check
                        st.write("**Node 2** — Running conflict-of-interest check …")
                        conflict_detected = check_crm_conflict(context.opposing_party_name)
                        conflict_warning = None

                        if conflict_detected:
                            conflict_warning = (
                                f"CONFLICT OF INTEREST DETECTED — The opposing party "
                                f"'{context.opposing_party_name}' is a current or former client "
                                f"of the Law Firm. This matter MUST be reviewed by the "
                                f"Ethics & Compliance Committee before any engagement letter is executed."
                            )
                            st.write("🚨 Conflict detected!")
                        else:
                            st.write("✅ No conflicts found")

                        # Node 3: Synthesis
                        st.write("**Node 3** — Synthesizing retainer agreement (Llama 3.3 70B) …")
                        retainer_md = synthesize_retainer_agreement(GROQ_API_KEY, context, conflict_warning)
                        st.write("✅ Agreement generated")

                        status.update(label="✅ Pipeline complete!", state="complete", expanded=False)

                    st.session_state.manual_results = {
                        "context": context.model_dump(),
                        "conflict_detected": conflict_detected,
                        "conflict_warning": conflict_warning,
                        "retainer_md": retainer_md
                    }
                    st.session_state.active_view = "manual"
                    st.rerun()

                except Exception as exc:
                    st.error(f"❌ **Pipeline Error:** {exc}")
                    logger.exception("Pipeline error")

    elif input_mode == "📹 Deploy Google Meet Bot":
        st.markdown(
            '<div class="card-title"><span class="icon">🤖</span> Google Meet Notetaker Bot</div>',
            unsafe_allow_html=True,
        )
        
        st.markdown("""
        Deploy a smart AI bot to join your live Google Meet call. The bot will automatically:
        1. **Join the meeting** as a participant ("Legal Notetaker").
        2. **Transcribe** the dialogue in real-time.
        3. **Analyze** conflict and generate the retainer once the meeting ends.
        """)

        meet_url = st.text_input(
            "Google Meet URL",
            placeholder="https://meet.google.com/abc-defg-hij",
            help="Enter the full Google Meet link."
        )

        st.markdown("")
        dispatch_clicked = st.button("🤖  Dispatch Notetaker Bot", use_container_width=True)

        if dispatch_clicked:
            if not meet_url or "meet.google.com" not in meet_url:
                st.error("⚠️ Please enter a valid Google Meet URL (containing meet.google.com).")
            else:
                try:
                    with st.spinner("Dispatching bot via Recall.ai..."):
                        bot_id = create_recall_bot(meet_url, recall_region)
                        
                    db = load_meetings_db()
                    db[bot_id] = {
                        "meeting_url": meet_url,
                        "status": "joining_call",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "transcript": None,
                        "extracted_metadata": None,
                        "conflict_detected": False,
                        "conflict_warning": None,
                        "retainer_agreement_markdown": None,
                    }
                    save_meetings_db(db)
                    
                    st.success(f"✅ Bot successfully dispatched! ID: `{bot_id[:8]}`")
                    st.session_state.active_view = f"bot_{bot_id}"
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ **Failed to dispatch bot:** {exc}")

        # ── Dispatched Bots History ────────────────────────────────────
        db = load_meetings_db()
        if db:
            st.markdown("---")
            st.markdown("### 📋 Dispatched Bots History")
            for bot_id, bot_data in sorted(db.items(), key=lambda x: x[1].get("created_at", ""), reverse=True):
                status_val = bot_data["status"]
                status_color = "#22c55e" if status_val in ("done", "call_ended", "recording_done", "analysis_done") else ("#ef4444" if status_val == "fatal" else "#6366f1")
                
                # Card container
                st.markdown(
                    f"""
                    <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(99, 102, 241, 0.1); border-radius: 8px; padding: 0.8rem; margin-bottom: 0.8rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                            <strong>Bot {bot_id[:8]}</strong>
                            <span style="color: {status_color}; font-weight: 600; font-size: 0.85rem; padding: 0.15rem 0.5rem; background: rgba(15, 23, 42, 0.6); border-radius: 4px;">{status_val.upper()}</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.6rem;">
                            URL: <a href="{bot_data['meeting_url']}" target="_blank" style="color: #a78bfa;">{bot_data['meeting_url']}</a><br>
                            Created: {bot_data['created_at']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Action Buttons
                col_v, col_r, col_d = st.columns(3)
                with col_v:
                    if st.button("👁️ View", key=f"view_{bot_id}"):
                        st.session_state.active_view = f"bot_{bot_id}"
                        st.rerun()
                with col_r:
                    is_terminal = status_val in ("done", "call_ended", "recording_done", "analysis_done", "fatal")
                    if st.button("🔄 Refresh", key=f"ref_{bot_id}", disabled=is_terminal):
                        with st.spinner("Checking..."):
                            refresh_bot_status(bot_id, db, recall_region)
                        st.rerun()
                with col_d:
                    if st.button("🗑️ Delete", key=f"del_{bot_id}"):
                        del db[bot_id]
                        save_meetings_db(db)
                        if st.session_state.active_view == f"bot_{bot_id}":
                            st.session_state.active_view = "manual"
                        st.rerun()

# ── RIGHT COLUMN — Outputs ─────────────────────────────────────────────────
def render_placeholder():
    st.markdown(
        """
        <div class="glass-card" style="text-align: center; padding: 4rem 2rem;">
            <div style="font-size: 3.5rem; margin-bottom: 1rem;">⚖️</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.6rem;">
                Ready to Process
            </div>
            <div style="color: #94a3b8; font-size: 0.95rem; max-width: 400px; margin: 0 auto; line-height: 1.7;">
                Paste a consultation transcript or deploy a Google Meet bot on the left to extract client data, check conflicts, and generate a retainer agreement.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Feature Cards ──────────────────────────────────────────
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(
            """
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 1.8rem;">🧠</div>
                <div style="font-weight: 600; color: #e2e8f0; margin: 0.5rem 0 0.3rem;">Extraction</div>
                <div style="color: #94a3b8; font-size: 0.82rem;">Llama 3.1 8B extracts structured data from raw transcripts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f2:
        st.markdown(
            """
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 1.8rem;">🔒</div>
                <div style="font-weight: 600; color: #e2e8f0; margin: 0.5rem 0 0.3rem;">Conflict Check</div>
                <div style="color: #94a3b8; font-size: 0.82rem;">Automated CRM screening for conflicts of interest</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f3:
        st.markdown(
            """
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 1.8rem;">📄</div>
                <div style="font-weight: 600; color: #e2e8f0; margin: 0.5rem 0 0.3rem;">Synthesis</div>
                <div style="color: #94a3b8; font-size: 0.82rem;">Llama 3.3 70B drafts professional retainer agreements</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_pipeline_results(context_dict, conflict_detected, conflict_warning, retainer_md):
    # Extracted Metadata
    st.markdown(
        '<div class="card-title"><span class="icon">🔍</span> Extracted Intake Metadata</div>',
        unsafe_allow_html=True,
    )
    st.json(context_dict, expanded=True)

    # Conflict Status
    st.markdown("")
    if conflict_detected:
        st.markdown(
            '<span class="badge-conflict">🚨 CONFLICT DETECTED</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="conflict-alert">
                <strong>⚠️ Conflict of Interest Alert</strong><br><br>
                {conflict_warning}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="badge-ok">✅ No Conflicts Detected</span>',
            unsafe_allow_html=True,
        )

    # Retainer Agreement
    st.markdown("")
    st.markdown(
        '<div class="card-title"><span class="icon">📄</span> Generated Retainer Agreement</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="agreement-container">', unsafe_allow_html=True
    )
    st.markdown(retainer_md)
    st.markdown("</div>", unsafe_allow_html=True)

    # Download button
    st.markdown("")
    st.download_button(
        label="📥 Download Retainer Agreement as Markdown",
        data=retainer_md,
        file_name="retainer_agreement.md",
        mime="text/markdown",
        use_container_width=True,
    )


def render_bot_view(bot_id, bot_data):
    st.markdown(f"### 📹 Google Meet Bot: `{bot_id[:8]}`")
    st.markdown(f"**Meeting URL:** [{bot_data['meeting_url']}]({bot_data['meeting_url']})")
    st.markdown(f"**Dispatched at:** {bot_data['created_at']}")
    
    status = bot_data['status']
    
    # Render status badge
    if status in ("done", "call_ended", "recording_done", "analysis_done"):
        st.markdown('<span class="badge-ok">✅ MEETING COMPLETED</span>', unsafe_allow_html=True)
    elif status == "fatal":
        st.markdown('<span class="badge-conflict">🚨 BOT ERROR (FATAL)</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge-ok" style="background: rgba(99, 102, 241, 0.15); color: #a78bfa; border-color: rgba(99, 102, 241, 0.3);">⏳ BOT STATUS: {status.upper()}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if bot_data.get("error"):
        st.error(f"❌ **Error:** {bot_data['error']}")
        
    if bot_data.get("transcript"):
        with st.expander("📖 View Raw Transcript", expanded=False):
            st.text_area("Transcript Text", value=bot_data["transcript"], height=250, disabled=True)
            
    if bot_data.get("extracted_metadata"):
        render_pipeline_results(
            bot_data["extracted_metadata"],
            bot_data.get("conflict_detected", False),
            bot_data.get("conflict_warning"),
            bot_data.get("retainer_agreement_markdown", "")
        )
    else:
        if status not in ("done", "call_ended", "recording_done", "analysis_done", "fatal"):
            st.info("🕒 The bot is still active in the meeting or processing audio. Once the call ends, the transcript will be analyzed, conflict checked, and the retainer agreement will generate automatically.")
            st.markdown("""
            **How to check for updates:**
            - Click the **🔄 Refresh** button on the left sidebar/list to poll for updates.
            """)
        else:
            st.warning("⚠️ Meeting ended but no data was processed. This might happen if the transcript was too short or empty.")


with col_right:
    if st.session_state.active_view == "manual":
        if st.session_state.manual_results:
            render_pipeline_results(
                st.session_state.manual_results["context"],
                st.session_state.manual_results["conflict_detected"],
                st.session_state.manual_results["conflict_warning"],
                st.session_state.manual_results["retainer_md"]
            )
        else:
            render_placeholder()
    elif st.session_state.active_view.startswith("bot_"):
        bot_id = st.session_state.active_view.split("_", 1)[1]
        db = load_meetings_db()
        if bot_id in db:
            render_bot_view(bot_id, db[bot_id])
        else:
            st.error("Selected meeting record not found.")
            st.session_state.active_view = "manual"
            st.rerun()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="dashboard-footer">
        Legal Intake Automation System &bull; Powered by Groq
    </div>
    """,
    unsafe_allow_html=True,
)
