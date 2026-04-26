# Spec-Driven Development (SDD) Context: Research Paper Skill Tree Pipeline

## 1. Project Overview
The objective is to build a highly deterministic, multi-agent pipeline that parses academic research papers and outputs a validated "skill tree" (Directed Acyclic Graph) of concepts. The system relies on an adversarial architecture to ruthlessly filter out LLM hallucinations. All data flow must strictly adhere to predefined JSON Schemas.

## 2. Architectural Constraints
* **Framework:** LangGraph (Python). Loose conversational agents (e.g., CrewAI, AutoGen) are strictly prohibited.
* **Determinism:** The orchestrator must not be an LLM; it must be a compiled LangGraph state machine. Agents are restricted to specific nodes within this graph.
* **Shared State (`PaperState`):** A strictly typed dictionary containing:
  * `raw_text`: Chunked paper sections.
  * `skill_tree_nodes`: Growing list of processed concepts.
  * `current_node_under_review`: The specific concept currently being analyzed.
  * `draft_analysis`: The Expert Agent's initial breakdown.
  * `critique_feedback`: The Validator Agent's output.
  * `validation_status`: Boolean gatekeeper (`True` if bulletproof).
* **Context Window Management:** Use PyMuPDF or unstructured.io to chunk the PDF by section headers. Agents must only receive the isolated text chunk relevant to their specific task.
* **LLM Configuration:** Use the Gemini API. All agents must operate with `temperature=0.0` or `0.1` and utilize the `response_schema` parameter to guarantee structured JSON output.

## 3. Pipeline Flow & Execution Graph
1.  **Ingestion:** Parse the PDF and chunk by section headers into `PaperState`.
2.  **Extraction:** The Cartographer Agent maps the raw text into a list of baseline concept nodes.
3.  **Processing Loop (Per Node):**
    * **Expert Agent:** Drafts an explanation and identifies prerequisite nodes.
    * **Validator Agent (Adversarial):** Compares the Expert's draft strictly against the raw source text. Flags any claim not explicitly supported.
    * **Resolution Edge:** If `is_valid == False`, route to the Resolution Agent to strip unverified claims, then loop back to the Validator (max 3 retries).
    * **Commit Edge:** If `is_valid == True`, append the validated node to the final tree.
4.  **Synthesis:** The Synthesizer Agent assembles the validated nodes into a final DAG structure.

## 4. Agent Roles and System Prompts
All agents must use the following system prompt template, substituting the variables accordingly:
> "You are the [{Agent_Role}]. Your sole function is to analyze the input and output a raw JSON object strictly adhering to this schema: [{JSON_Schema}]. Do not include markdown formatting, conversational filler, or hallucinated claims; any deviation causes immediate pipeline failure."

* **Cartographer:** Extracts terms and structure (no explanations) from the abstract, intro, and conclusion.
* **Expert:** Deep-dives into specific chunks to draft explanations and establish prerequisites (edges).
* **Validator:** The hostile peer reviewer. *Specific instruction:* "You are a hostile reviewer. Your only goal is to find claims in the Draft that are not explicitly stated in the Source Text. You do not care about readability; you care only about factual grounding."
* **Resolution:** The editor. Rewrites drafts to strictly remove flags raised by the Validator.
* **Synthesizer:** Formats the final validated data into the required UI-ready DAG structure.

## 5. Internal Data Contracts (Schema Specifications)
The JSON schemas defined in `schemas.json` (and implemented as Pydantic models in the codebase) are the strict, internal data contracts for the Gemini API `response_schema`. 
Ensure no LangGraph node attempts to make HTTP requests to external agents; all LLM invocations must happen locally within the node functions. Any deviation triggers a hard pipeline failure.

## 6. Preprocessing Pipeline
* **Ingestion:** Use `PyMuPDF` to parse PDF binaries and `unstructured.io` to segment the document strictly by logical section headers.
* **Sanitization:** Strip unreadable elements (images, complex tables, bibliography) before injecting text into the `PaperState` to prevent context pollution and token waste.

## 7. Frontend Integration
* **Rendering:** Feed the Synthesizer Agent's DAG JSON output directly into `React Flow` or `D3.js` to construct the visual skill tree.
* **State Mapping:** Map the `node_id` of each UI element to the validated explanations so users can click nodes to read the grounded context.