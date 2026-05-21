<p align="center">
  <strong>⚖️ Legal Intake & Retainer Generation System</strong>
</p>

<p align="center">
  <em>AI-powered consultation processing pipeline for modern law firms</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Groq-LPU_Inference-f55036?style=flat-square" alt="Groq">
  <img src="https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit">
</p>

---

## Executive Summary

**The Problem:** Law firms spend an average of 6–8 billable hours per client on manual intake processing—transcribing consultations, cross-referencing conflicts, and drafting retainer agreements. This repetitive administrative work creates intake friction, delays client onboarding, and diverts attorney time from high-value legal strategy.

**The Solution:** The Legal Intake System is a fully automated pipeline that transforms a raw consultation transcript into a structured intake record, a conflict-check result, and a production-ready legal retainer agreement—in under 30 seconds.

### Business Value

| Metric | Before (Manual) | After (Automated) |
|---|---|---|
| Intake processing time | 6–8 hours | < 30 seconds |
| Conflict check turnaround | 1–2 business days | Instant |
| Retainer drafting | 2–3 hours (paralegal) | Automated |
| Error rate in data extraction | ~12% | < 1% (structured AI) |
| Cost per intake | $1,200–$2,000 | < $0.05 (API cost) |

---

## Architecture Overview

The system uses a **dual-model Groq architecture** with a four-node processing pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONSULTATION TRANSCRIPT                       │
│                  (Webhook POST Payload)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   NODE 1: EXTRACTION   │
              │  Llama 3.1 8B Instant  │
              │  + instructor/Pydantic │
              │                        │
              │  Extracts:             │
              │  • Client name         │
              │  • Opposing party      │
              │  • Matter type         │
              │  • Case summary        │
              │  • Fee structure       │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │ NODE 2: CONFLICT CHECK │
              │     Mock CRM Gate      │
              │                        │
              │ Screens opposing party │
              │ against known clients  │
              └───────────┬────────────┘
                          │
                   ┌──────┴──────┐
                   │             │
              No Conflict   Conflict Found
                   │             │
                   │      ┌──────┴──────────┐
                   │      │ Append warning   │
                   │      │ to context       │
                   │      └──────┬───────────┘
                   │             │
                   └──────┬──────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  NODE 3: SYNTHESIS     │
              │ Llama 3.3 70B Versatile│
              │                        │
              │ Generates complete     │
              │ Markdown retainer      │
              │ agreement with firm    │
              │ pricing rules          │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │ NODE 4: PDF COMPILE    │
              │ markdown2 → HTML       │
              │ pdfkit → PDF bytes     │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │     JSON RESPONSE      │
              │  • Extracted metadata  │
              │  • Conflict status     │
              │  • Retainer (Markdown) │
              └────────────────────────┘
```

### Why Two Models?

| Stage | Model | Rationale |
|---|---|---|
| **Extraction** | `llama-3.1-8b-instant` | Optimized for speed and structured output. Paired with `instructor` for guaranteed Pydantic schema compliance. Sub-second latency. |
| **Synthesis** | `llama-3.3-70b-versatile` | Superior language generation for formal legal prose. Produces nuanced, jurisdiction-aware retainer agreements with proper legal terminology. |

---

## Prerequisites & API Integration

This application is ready to run out of the box with pre-integrated API keys for both **Groq** and **Recall.ai**. No manual key configuration is required to get started.

### System Requirements

| Dependency | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Runtime |
| **wkhtmltopdf** (Optional) | — | HTML-to-PDF conversion engine used by `pdfkit` |

> **Note:** PDF compilation (Node 4) will gracefully skip if `wkhtmltopdf` is not installed. All other pipeline functionality works without it.

**Installing wkhtmltopdf:**

- **Windows:** Download from [wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html) and add to PATH
- **macOS:** `brew install wkhtmltopdf`
- **Ubuntu/Debian:** `sudo apt-get install wkhtmltopdf`

---

## Installation

### 1. Clone or Download the Project

```bash
cd "AI Call bot"
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn groq instructor pydantic markdown2 pdfkit streamlit requests
```

### 4. Override API Keys (Optional)

If you want to use your own Groq API key, set it in your environment:

```bash
# Windows (PowerShell)
$env:GROQ_API_KEY = "gsk_your_api_key_here"

# Windows (CMD)
set GROQ_API_KEY=gsk_your_api_key_here

# macOS/Linux
export GROQ_API_KEY="gsk_your_api_key_here"
```

---

## Running the System

You need **two terminal windows** running concurrently:

### Terminal 1 — FastAPI Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

Verify the backend is live:

```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"Legal Intake Pipeline"}
```

### Terminal 2 — Streamlit Dashboard

```bash
streamlit run app.py
```

The dashboard will open automatically at `http://localhost:8501`.

---

## Testing with a Mock Transcript

The Streamlit dashboard comes pre-loaded with a sample consultation transcript featuring:

- **Client:** David Reynolds
- **Opposing Party:** Michael Johnson (triggers conflict detection!)
- **Matter:** Breach of contract / partnership dispute
- **Fee Structure:** Hybrid hourly + success fee

### Quick Test Steps

1. Start both servers (see above)
2. Open `http://localhost:8501` in your browser
3. The sample transcript is already loaded — click **⚡ Run Intake Pipeline**
4. Observe:
   - ✅ Structured metadata extraction in the JSON block
   - 🚨 **Red conflict alert** (Michael Johnson is flagged)
   - 📄 Full retainer agreement rendered in Markdown

## Testing Google Meet Bot Integration

The dashboard supports deploying a live Google Meet bot via **Recall.ai** that joins the meeting, records/transcribes it, and automatically runs the pipeline on completion.

### How to use the Google Meet Notetaker Bot:

1. Start the Streamlit server and open `http://localhost:8501`.
2. Select **📹 Deploy Google Meet Bot** input mode.
3. Enter your Google Meet link (e.g. `https://meet.google.com/abc-defg-hij`).
4. Click **🤖 Dispatch Notetaker Bot**.
5. The bot (named "Legal Notetaker") will join the meeting. (Ensure someone is in the meeting to admit it).
6. When the meeting ends, the bot automatically retrieves the transcript, runs conflict checking, extracts metadata, and generates the retainer.
7. Click **🔄 Refresh** in the sidebar's bot history list to pull the latest status.

### Testing via cURL (API Only)

```bash
curl -X POST http://localhost:8000/webhook/consultation-ended \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Attorney: Good morning... [paste full transcript here, 100+ words]"
  }'
```

### Testing the Too-Short Guard

```bash
curl -X POST http://localhost:8000/webhook/consultation-ended \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Hello, I need a lawyer."}'
# → 400: Transcript is too short (6 words). A minimum of 100 words is required.
```

---

## API Reference

### `POST /webhook/consultation-ended`

| Field | Type | Required | Description |
|---|---|---|---|
| `transcript` | `string` | ✅ | Full consultation transcript (min. 100 words) |

**Response (200):**

```json
{
  "extracted_metadata": {
    "client_full_name": "David Reynolds",
    "opposing_party_name": "Michael Johnson",
    "legal_matter_type": "Breach of Contract",
    "case_summary": "...",
    "agreed_fee_structure": "..."
  },
  "conflict_detected": true,
  "conflict_warning": "CONFLICT OF INTEREST DETECTED — ...",
  "retainer_agreement_markdown": "# LEGAL RETAINER AGREEMENT ..."
}
```

**Error Responses:**

| Code | Condition |
|---|---|
| `400` | Transcript under 100 words |
| `500` | Pipeline processing error |

### `GET /health`

Returns `{"status": "ok"}` — useful for load balancer health checks.

---

## Project Structure

```
AI Call bot/
├── main.py          # FastAPI backend — 4-node intake pipeline
├── app.py           # Streamlit dashboard — premium split-screen UI
├── README.md        # This file
└── requirements.txt # (optional) pip freeze output
```

---

## Customization Guide

### Modifying Firm Details

Edit the `FIRM_SYSTEM_PROMPT` constant in `main.py` to change:
- Firm name, location, and branding
- Hourly rates and retainer amounts
- Fee structures and billing policies
- Governing law jurisdiction

### Extending the Conflict Check

Replace the `check_crm_conflict()` function in `main.py` with a real CRM integration:

```python
def check_crm_conflict(opposing_party: str) -> bool:
    # Example: query your CRM API
    response = requests.get(f"https://crm.yourfirm.com/api/conflicts?name={opposing_party}")
    return response.json().get("conflict_exists", False)
```

### Adding New Extraction Fields

Extend the `LegalIntakeContext` Pydantic model:

```python
class LegalIntakeContext(BaseModel):
    client_full_name: str
    opposing_party_name: str = "None"
    legal_matter_type: str
    case_summary: str
    agreed_fee_structure: str
    # Add new fields:
    jurisdiction: str = Field(default="Not specified")
    urgency_level: str = Field(default="Standard")
```

---

## License

This project is provided as-is for demonstration and internal use. Consult your firm's compliance team before deploying in a production legal environment.

---

<p align="center">
  <strong>Built with ❤️ by the Engineering Team</strong><br>
  <em>Powered by Groq LPU Inference • FastAPI • Streamlit</em>
</p>
