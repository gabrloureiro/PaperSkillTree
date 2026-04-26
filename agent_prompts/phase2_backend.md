# Phase 2: Backend Orchestration & API

**Agent Role:** You are the Backend Engineer Agent. Your task is to build a lightweight FastAPI server that bridges the React frontend with the monolithic LangGraph pipeline.

> [!IMPORTANT]
> **Implementation Plan Required:** Before writing any code, you MUST create an `implementation_plan.md` artifact detailing your approach and request user approval.

## Requirements

1. **New Script:** Create a new Python file named `server.py`.
2. **API Framework:** Use FastAPI to create the server. Configure CORS to allow requests from the local Vite frontend.
3. **Endpoints:**
   - `POST /upload`: Accepts a PDF file upload from the frontend.
     - Save the PDF to `cache/pdfs/`.
     - Check if a corresponding skill tree already exists in `cache/skill_trees/` (e.g., hash the PDF or use the filename).
     - If it exists, return the cached DAG to prevent redundant generation.
     - If it does not exist, call `parse_pdf()` from `ingestion.py`, initialize the `PaperState`, and invoke the compiled LangGraph (`build_paper_skill_tree_graph()` from `main.py`) locally within the endpoint.
     - Once the graph finishes, save the `final_dag` to `cache/skill_trees/` and return it.
   - `GET /skill-trees`: Returns a list of all successfully generated skill trees currently available in `cache/skill_trees/`.
4. **Execution Constraints:** 
   - The LangGraph must run locally within the `server.py` process. Do NOT create microservices or external HTTP calls for the LangGraph agents.
5. **Dependencies:** Update `requirements.txt` to include `fastapi`, `uvicorn`, and `python-multipart`.

## Context
This server is the entry point for the frontend to upload papers and retrieve the generated DAGs. It handles state initialization and orchestration of the existing `PaperSkillTree` LangGraph.
