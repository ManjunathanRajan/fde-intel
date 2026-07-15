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
     recommended questions)
                │
                ▼
         FDE Briefing
   (terminal output + markdown)
```

Each specialist agent runs an **agentic tool-use loop**:
1. Claude decides what to search
2. Calls `search_web` tool (Tavily)
3. Reads results, decides if more searches needed
4. Returns structured JSON finding

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
# Add your ANTHROPIC_API_KEY and TAVILY_API_KEY to .env
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
- **Zero-framework implementation** — raw Claude API + asyncio. Every line is readable. No LangChain, no LangGraph.
- **Works without Tavily** — DuckDuckGo fallback so you can run it with only an Anthropic API key.

| Layer | Choice | Why |
|---|---|---|
| LLM | Claude API (raw) | No framework overhead, full control over tool loops |
| Parallelism | `asyncio.gather` | 4 agents run simultaneously |
| Tool use | Anthropic tool_use API | Structured, reliable — no text parsing |
| Web search | Tavily API | Clean API, `advanced` depth mode |
| Output schema | Pydantic v2 | Validated findings, no silent failures |
| CLI | Typer + Rich | Clean terminal output |

No LangChain. No LangGraph. Every line is readable and debuggable.

---

## Project structure

```
fde-intel/
├── fde_intel/
│   ├── agents.py        # 4 specialist agents with tool-use loops
│   ├── orchestrator.py  # fan-out + synthesis
│   ├── models.py        # Pydantic schemas
│   ├── reporter.py      # terminal + markdown output
│   ├── config.py        # env config
│   └── tools/
│       └── search.py    # Tavily web search
├── tests/
│   └── test_models.py
├── reports/output/      # saved briefings (gitignored)
├── main.py              # CLI entry point
└── requirements.txt
```

---

## Tests

```bash
pytest
```

---

## Why this project

FDEs spend 2-3 hours per client doing this research manually. This tool compresses that to under 2 minutes and produces a consistent, structured output every time — reducing prep variability across a team.

Built as part of a portfolio for transitioning from SRE to Forward Deployed Engineering.

---

## License

MIT
