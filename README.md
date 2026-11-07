# PaperSkillTree

Turns an academic paper into a **skill tree** — a directed acyclic graph of the concepts it
depends on, ordered so you can learn them from the ground up — then lets you work through
that tree by explaining each concept back to an examiner.

The pipeline is a compiled [LangGraph](https://langchain-ai.github.io/langgraph/) state
machine, not a conversational agent swarm. The orchestrator is deterministic code; LLMs are
confined to individual nodes, every one of which must return JSON matching a Pydantic schema.
Explanations are checked against the paper's own text by an adversarial validator, so what
lands in the tree is grounded in the source rather than in the model's priors.

## How it works

```
                  ┌─ Recruiter ─────────── picks 3-5 specialist roles for the paper's field
                  │
 Teaching Council ├─ Specialists ───────── each names the technical non-negotiables
                  ├─ Pedagogical Expert ── drafts a learning plan from their input
                  └─ Plan audit ────────── specialists accept or critique (≤3 rounds)
                  │
                  ▼
             Cartographer ──────────────── concepts + a skeleton DAG
                  │
                  ▼
    ┌──────── per concept, in parallel ────────┐
    │  Expert ──────── drafts an explanation   │
    │  Validator ───── flags ungrounded claims │   ≤3 revisions
    │  Resolution ──── rewrites to the source  │
    └──────────────────────────────────────────┘
                  │
                  ▼
            Synthesizer ─────────────────── merges into one clean DAG
                  │                                      ▲
                  ▼                                      │ ≤3 rounds
         Structural Auditor ──────────────── cycles, islands, bottlenecks
                  │
                  ▼
     Final council review ──► rubric generation ──► done
```

The **branch subgraph** (Expert → Validator → Resolution) runs isolated per concept so
parallel branches can't race on shared state; results merge back through an id-keyed reducer.
The **Structural Auditor** computes reachability itself — adjacency list, roots, BFS — and
hands the model a concrete list of disconnected nodes rather than asking it to eyeball the
graph. **Rubric generation** produces per-concept grading criteria for every grade from A+ to
F, which the examiner then marks against.

## Requirements

- Python 3.10+
- Node.js 18+
- A Google Gemini API key

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd frontend && npm install && cd ..
```

Create a `.env` in the project root (see `.env.example`):

```ini
GOOGLE_API_KEY=your-key-here
MODEL_NAME=gemini-2.5-flash    # required, no default
TEMPERATURE=0.0                # optional
CACHE_DIR=cache                # optional
```

`MODEL_NAME` is read with `os.environ[...]`, so the app raises `KeyError` on startup if it is
missing. The others have defaults.

## Running

```bash
fastapi dev server.py          # backend
cd frontend && npm run dev     # frontend
```

The backend's CORS policy only allows `http://localhost:5173` (`Config.ALLOWED_ORIGINS`), and
the frontend hardcodes `http://localhost:8000` as its API base — change both if you move
either port.

Upload a PDF and pick a complexity:

- **simple** — 5–15 concepts, a linear high-level path
- **complex** — 20–30 concepts, exhaustive, broken into granular sub-concepts

## Caching

A tree's id is the **SHA-256 of the PDF's bytes**. Uploads are cached under `CACHE_DIR`:

```
cache/pdfs/<sha256>.pdf
cache/skill_trees/<sha256>.json
```

Re-uploading a byte-identical PDF replays the stored tree instead of rerunning the pipeline.
To force a real run, delete that tree (`DELETE /skill-trees/{id}`) or clear `cache/`.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/upload?complexity=simple` | Process a PDF, return the finished tree |
| `POST` | `/upload-stream?complexity=simple` | Same, streamed as SSE while it runs |
| `GET` | `/skill-trees` | List stored trees (`id`, `title`) |
| `GET` | `/skill-trees/{id}` | Fetch one tree |
| `PATCH` | `/skill-trees/{id}` | Update `title` / `passing_grade` |
| `DELETE` | `/skill-trees/{id}` | Delete tree and cached PDF |
| `POST` | `/skill-trees/{id}/reset` | Clear progress and passing grade |
| `POST` | `/chat/examiner` | Explain a concept; get graded against its rubric |
| `POST` | `/chat/tutor` | Ask for help understanding a concept |

`/upload-stream` emits SSE frames whose `type` is one of `status`, `agent_start`,
`agent_stop`, `agent_message`, `skeleton_discovered`, `node_finalized`, `graph_synthesized`,
`final_result`, `complete`, or `error`. The frontend's ProcessingLog renders this feed so the
skeleton graph appears immediately and nodes fill in as each branch finalizes.

Default passing grade is `B-` (`Config.DEFAULT_PASSING_GRADE`).

## Layout

```
server.py                  FastAPI app and routes
main.py                    compiles the graph standalone (sanity check)
src/
  core/config.py           env-backed settings
  core/graph_builder.py    LangGraph topology and routers
  agents/pipeline_agents.py   pipeline agent node functions
  agents/chat_agents.py    examiner and tutor
  models/state.py          PaperState / BranchState and their reducers
  models/schemas.py        Pydantic response schemas
  services/               ingestion, llm, graph, chat, storage
frontend/src/              React + ReactFlow UI
specs/sdd.md               design doc and data contracts
tests/                     pytest suite
```

Ingestion uses **PyMuPDF** to pull text blocks (dropping page numbers and everything from
`References` onward) and **unstructured** to segment what's left by section header. Agents are
handed only the chunk matching their concept's `source_section_header`.

## Tests

```bash
pytest tests/
```

`tests/conftest.py` builds a synthetic PDF fixture, so the unit tests need no sample paper.
`tests/integration/test_graph.py` only asserts the graph compiles — it does not call the API.

## Notes

- State is keyed by `node_id` throughout. A node that loses its id is dropped by the merge
  reducer, so the Cartographer assigns a fallback id whenever the model omits one.
- `PaperState` fields each declare a reducer. Counters using `operator.add` must return the
  *increment*, not a running total — returning the total makes the value compound.
- Routers in `graph_builder.py` are pure reads. LangGraph evaluates conditional edges *after*
  a node runs against the already-updated state, so mutating `state` inside a router has no
  effect; agents return their own routing state instead.
- `agent_prompts/` and `scratch/` are development notes and throwaway scripts, not part of the
  running system.
