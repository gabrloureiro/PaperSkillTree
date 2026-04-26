# Phase 1: Preprocessing & Ingestion Engine

**Agent Role:** You are the Data Engineer Agent. Your task is to build robust document parsing and caching logic for the `PaperSkillTree` project.

> [!IMPORTANT]
> **Implementation Plan Required:** Before writing any code, you MUST create an `implementation_plan.md` artifact detailing your approach and request user approval.

## Requirements

1. **New Module:** Create a new Python file named `ingestion.py`.
2. **Persistent Caching:** 
   - Implement a caching mechanism. Uploaded PDFs should be saved to a `cache/pdfs/` directory.
   - Generated skill trees (from later phases) will be saved to `cache/skill_trees/`. 
   - Make sure your script creates these directories if they don't exist.
   - The cache should NOT be cleared automatically.
3. **Library Usage:** Use `PyMuPDF` (`fitz`) and/or `unstructured` to process incoming PDF files.
4. **Extraction & Chunking:**
   - Extract the text from the PDF.
   - Strictly chunk the document by logical section headers (e.g., Abstract, Introduction, Conclusion). 
5. **Sanitization:** 
   - Strip out unreadable/unnecessary elements to preserve context windows and token counts. Specifically, remove or ignore images, figures, complex tables, and the bibliography/references section.
6. **Output Format:**
   - The primary function (e.g., `parse_pdf(filepath: str)`) must return a list of dictionaries matching the `PaperChunkInput` TypedDict defined in `state.py`.
   - Each dictionary must contain:
     - `raw_text`: The sanitized string content of the section.
     - `section_header`: The title of the section.
7. **Dependencies:** Update `requirements.txt` to include `pymupdf` and/or `unstructured`.

## Context
The output of this module will be injected directly into the `raw_text` field of the `PaperState` in the LangGraph orchestration layer. The extraction must be clean and highly deterministic.
