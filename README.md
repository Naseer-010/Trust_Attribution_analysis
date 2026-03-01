# Human-AI Trust Experimentation Engine

> **GSoC 2026** · Humanlike AI Systems and Trust Attribution  
> A modular experimentation engine for studying trust calibration in AI-assisted decision systems.

---

## Architecture

```
Trust_attribution/
├── backend/                # FastAPI + LangChain backend
│   ├── main.py             # REST API (7 routes)
│   ├── ai_provider.py      # 3 AI modes: Hardcoded / OpenAI / HuggingFace
│   ├── conditions.py       # 2x2x2 factorial condition management (8 conditions)
│   ├── logger.py           # Thread-safe CSV logging
│   ├── prompt_templates.py # LangChain prompt templates with cue injection
│   ├── cues_config.json    # Cue dimensions, conditions, scenarios, error injection
│   └── .env                # API keys and model configuration
├── frontend/               # Next.js React app
│   └── src/app/
│       ├── page.js         # Start Experiment (random condition assignment)
│       ├── task/page.js    # Decision Task (Accept/Override + latency tracking)
│       └── admin/export/   # Data dashboard + CSV download
├── analysis/
│   ├── analyze_results.py  # Trust calibration analysis script
│   └── trust_analysis.ipynb # Jupyter notebook with visualizations
├── data/
│   ├── results.csv         # Accumulated experiment data (auto-generated)
│   └── sample_results.csv  # Sample output with 32 records
└── README.md
```

---

## Condition Logic

**3 Cue Dimensions** in a 2x2x2 factorial design = **8 experimental conditions**:

| Dimension | Level A | Level B |
|-----------|---------|---------|
| **Agent Identity** | `System-X` (neutral AI label) | `Sarah` (humanlike name) |
| **Tone** | `Technical` (formal, data-driven) | `Empathetic` (warm, conversational) |
| **Confidence** | `Probabilistic` (calibrated ranges) | `Authoritative` (definitive claims) |

Participants are randomly assigned to one of the 8 conditions. The AI's name, communication tone, and confidence framing are dynamically injected into both the prompt template and the UI.

**Error Injection**: 30% of scenarios (IDs 3, 5, 10) are deliberately answered incorrectly by the AI. This tests whether users can detect and override wrong AI recommendations — a key measure of trust calibration.

---

## Logging Implementation

**Event Schema** (CSV columns):

| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | UUID-based participant identifier |
| `condition_id` | int (1-8) | Assigned experimental condition |
| `agent_name` | string | "System-X" or "Sarah" |
| `tone_style` | string | "Technical" or "Empathetic" |
| `confidence_framing` | string | "Probabilistic" or "Authoritative" |
| `ai_recommendation` | string | What the AI recommended: "Accept" or "Reject" |
| `scenario_id` | int (1-10) | Which business decision scenario was presented |
| `correct_answer` | string | The objectively correct answer for the scenario |
| `confidence_score` | float | AI's stated confidence level (0-100) |
| `decision` | string | User's decision: "Accept" or "Override" |
| `latency_ms` | float | Milliseconds from AI render to user click |
| `timestamp` | ISO 8601 | UTC timestamp of the decision |

**Latency Measurement**: Uses `performance.now()` in the browser for sub-millisecond resolution. Timer starts when the AI response is rendered, stops on button click.

**Thread Safety**: CSV writes are protected by a threading lock for concurrent request handling.

---

## AI Provider Modes

The AI provider in `ai_provider.py` supports three modes — switch by changing one line:

| Mode | Description | Setup Required |
|------|-------------|----------------|
| **Hardcoded** | Static responses with controlled accuracy | None (default) |
| **Proprietary** | OpenAI GPT via LangChain | Set `OPENAI_API_KEY` in `.env` |
| **Open Source** | HuggingFace model via LangChain | Set `HUGGINGFACE_API_KEY` in `.env` |

All three modes use the same prompt template and cue injection system from `cues_config.json`.

---

## How to Run Locally

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The API runs at **http://localhost:8000**. Verify: `curl http://localhost:8000/`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at **http://localhost:3000**.

### 3. Run the Experiment

1. Open **http://localhost:3000** in your browser
2. Click **"Start Experiment"** — you'll be assigned a random condition
3. Review the AI recommendation and click **Accept** or **Override**
4. Visit **http://localhost:3000/admin/export** to view/download data

### 4. Run the Analysis

**Command-line script**:
```bash
cd analysis
pip install pandas scipy numpy
python analyze_results.py --csv ../data/results.csv
```

**Jupyter notebook** (recommended for visualization):
```bash
cd analysis
pip install jupyter pandas scipy numpy matplotlib seaborn
jupyter notebook trust_analysis.ipynb
```

Or use the sample data:
```bash
python analyze_results.py --csv ../data/sample_results.csv
```

---

## Trust Calibration Metrics

The analysis computes research-grade behavioral trust metrics:

| Metric | Description |
|--------|-------------|
| **Trust Agreement Rate** | How often the user's decision matched the AI recommendation |
| **Appropriate Reliance** | Accepted when AI was correct (good trust) |
| **Over-reliance** | Accepted when AI was wrong (blind trust / automation bias) |
| **Under-reliance** | Overrode when AI was correct (missed opportunity) |
| **Trust Discrimination Ratio** | Appropriate reliance / over-reliance (>1 = calibrated) |
| **User Accuracy** | How often the user's final decision was objectively correct |
| **Latency Analysis** | Response time differences between Accept/Override with t-tests |
| **Cue Effects** | Chi-square tests for each cue dimension's influence on trust |

---

## Sample Output

See `data/sample_results.csv` for example experiment data (32 records). Running the analysis produces:

```
========================================================================
  HUMAN-AI TRUST EXPERIMENT: ANALYSIS REPORT
========================================================================

  OVERALL TRUST METRICS
  Total Responses:            32
  Reliance Rate:              71.9%
  Override Rate:              28.1%

  Trust Agreement Rate:        56.2%
  Appropriate Reliance:        78.6%  (accepted when AI was correct)
  Over-reliance:               25.0%  (accepted when AI was WRONG)

  Trust Discrimination Ratio:  3.14
    Verdict: Well-calibrated

  KEY FINDINGS
  1. Users show GOOD trust calibration (discrimination ratio: 3.14)
  2. Override decisions take 2x longer than Accepts (p=0.0008)
  3. Highest trust agreement in Condition 3 (75.0%)
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/api/start` | Assign random condition to new participant |
| `GET` | `/api/condition/{id}` | Get cue config for a condition (1-8) |
| `GET` | `/api/conditions` | List all 8 conditions |
| `POST` | `/api/recommendation` | Get AI recommendation for a task |
| `POST` | `/api/log` | Log a decision event to CSV |
| `GET` | `/admin/export` | Download results.csv |
| `GET` | `/admin/data` | Get all data as JSON |

---

## Research Context

This project is built for the **"Humanlike AI Systems and Trust Attribution"** project under ISSR / University of Alabama, focusing on:

- Distinguishing perceived capability from actual capability
- Measuring when humanlike cues alter trust calibration
- Enabling evidence-based interface design for AI-assisted decision systems

**Mentors**: Andrya Allen, Dr. Xinyue Ye, Dr. Kelsey Chappetta, Dr. Andrea Underhill

---

## License

Open-source research prototype.
