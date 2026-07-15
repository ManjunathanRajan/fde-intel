# fde-intel

**Multi-agent research tool for Forward Deployed Engineers.**

Before walking into a client call, an FDE needs to know: does this technology actually fit? What does it cost? What breaks in production? Who are the alternatives?

`fde-intel` answers those questions in under 2 minutes by running 4 specialist AI agents in parallel, each searching the web and synthesizing findings, then producing a structured briefing.

---

## Architecture

```
User Input: "Research Snowflake"
        │
        ▼
┌────────────────────────────────────┐
│         Orchestrator               │
│  (fans out tasks via asyncio)      │
└──┬───────┬───────┬─────────────────┘
   │       │       │          │
   ▼       ▼       ▼          ▼
 Tech    Cost    Risk    Competitor
Agent   Agent   Agent     Agent
   │       │       │          │
   └───────┴───────┴──────────┘
                │
                ▼
        Synthesis Agent
      (executive summary +
     readiness score +
     recommended questions)
                │
                ▼
         FDE Briefing
   (terminal output + markdown)
```

Each specialist agent runs an **agentic tool-use loop**:
1. Claude decides what to search
2. Calls `search_web` tool (Tavily if key set, DuckDuckGo fallback)
3. Reads results, decides if more searches needed
4. Returns structured JSON finding validated by Pydantic

The orchestrator fans out all 4 agents with `asyncio.gather` — total wall time = slowest single agent, not sum of all.

---

## Quickstart

```bash
git clone https://github.com/ManjunathanRajan/fde-intel.git
cd fde-intel

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Minimum: add ANTHROPIC_API_KEY
# Optional: add TAVILY_API_KEY for higher quality search (tavily.com — free tier)
# Without TAVILY_API_KEY the tool falls back to DuckDuckGo automatically
```

**Run research:**

```bash
python main.py research "Snowflake"
python main.py research "Databricks" --output   # saves markdown to reports/output/
python main.py research "Salesforce Data Cloud"
```

---

## Output

Terminal output with Rich formatting. A full sample briefing is in [`sample_outputs/snowflake_briefing.md`](sample_outputs/snowflake_briefing.md).

```
╔══════════════════════════════════════╗
║    FDE Intelligence Briefing         ║
║    Snowflake                         ║
╚══════════════════════════════════════╝

┌─ Executive Summary ───────────────────────────────────────────┐
│ Snowflake is a mature cloud data warehouse with strong        │
│ enterprise traction. Pricing is consumption-based and can     │
│ scale unpredictably without query governance...               │
└───────────────────────────────────────────────────────────────┘

┌─ FDE Readiness Score ─────────────────────────────────────────┐
│ Grade: B  Score: 82/100                                       │
│ ████████░░                                                    │
│ Mature platform with clear pricing and manageable risks.      │
│                                                               │
│ Blockers:                                                     │
│   ✗ Existing Redshift contracts must expire first            │
│ Accelerators:                                                 │
│   ✓ Pre-built connectors for major ETL tools                 │
└───────────────────────────────────────────────────────────────┘

Integration Complexity: MEDIUM

┌─ Recommended Client Questions ────────────────────────────────┐
│ 1. What is your current data warehouse? When does contract    │
│    expire?                                                    │
│ 2. Do you have active ML workloads or is this pure analytics? │
└───────────────────────────────────────────────────────────────┘
```

---

## What makes this different

Most multi-agent research tools answer general questions. This one is purpose-built for a specific workflow: an FDE preparing for a client call.

- **FDE Readiness Score (0–100)** — grades deployment readiness across tech, cost, risk, and competitive position. No other tool does this.
- **Reasoned complexity** — Claude reasons about integration complexity from all 4 findings, not a hardcoded formula.
- **Client question generator** — produces questions specifically designed to uncover deployment blockers during a sales/discovery call.
- **Production-grade error handling** — structured exceptions separate internal debug info from user-facing messages.
- **Deployment-ready secrets** — supports Kubernetes mounted secrets alongside local env vars.
- **Zero-framework implementation** — raw Claude API + asyncio. Every line is readable. No LangChain, no LangGraph.
- **Works without Tavily** — DuckDuckGo fallback so you can run it with only an Anthropic API key.

| Layer | Choice | Why |
|---|---|---|
| LLM | Claude API (raw) | No framework overhead, full control over tool loops |
| Parallelism | `asyncio.gather` | 4 agents run simultaneously |
| Tool use | Anthropic tool_use API | Structured, reliable — no text parsing |
| Web search | Tavily (+ DuckDuckGo fallback) | Tavily for depth, DDG when no key |
| Output schema | Pydantic v2 | Validated findings, no silent failures |
| Secrets | Env var + file-based mount | Works locally and in Kubernetes |
| CLI | Typer + Rich | Clean terminal output |

---

## Project structure

```
fde-intel/
├── fde_intel/
│   ├── agents.py        # 4 specialist agents with tool-use loops
│   ├── orchestrator.py  # fan-out + synthesis
│   ├── models.py        # Pydantic schemas
│   ├── exceptions.py    # structured errors — internal info never leaks to user
│   ├── secrets.py       # env var + Kubernetes mounted secret loader
│   ├── config.py        # config, validation, param coercion
│   ├── reporter.py      # terminal + markdown output
│   └── tools/
│       └── search.py    # Tavily + DuckDuckGo fallback
├── tests/
│   ├── test_models.py   # models, agentic loop, orchestrator, search fallback
│   └── test_exceptions.py  # exceptions, param coercion
├── sample_outputs/
│   └── snowflake_briefing.md  # real output example
├── reports/output/      # saved briefings (gitignored)
├── main.py              # CLI entry point
└── requirements.txt
```

---

## Tests

```bash
pytest
```

24 tests covering: models, agentic tool-use loop, orchestrator fan-out, search fallback, structured exceptions, param coercion.

---

## Why this project

FDEs spend 2-3 hours per client doing this research manually. This tool compresses that to under 2 minutes and produces a consistent, structured output every time — reducing prep variability across a team.
