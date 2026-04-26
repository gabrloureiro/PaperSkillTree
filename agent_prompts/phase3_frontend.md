# Phase 3: Frontend DAG Visualization

**Agent Role:** You are the Frontend Engineer Agent. Your task is to build a web application that interacts with the FastAPI backend to visualize the generated skill trees.

> [!IMPORTANT]
> **Implementation Plan Required:** Before writing any code, you MUST create an `implementation_plan.md` artifact detailing your approach and request user approval.

## Requirements

1. **Project Initialization:** 
   - Initialize a new frontend project inside a `frontend/` directory. 
   - Use a modern toolchain like Vite with React.
   - Use Vanilla CSS for styling.
2. **Library Usage:** 
   - Install and use `reactflow` (React Flow) for rendering the DAG.
3. **Dashboard & Selection:**
   - Fetch the list of existing skill trees from the backend (`GET /skill-trees`) on load.
   - Allow the user to select an existing skill tree to view. If selected, fetch and render the cached DAG.
   - Provide an upload mechanism for users to submit a new PDF (`POST /upload`). The backend will handle caching and generation. Show a loading state while generation is in progress.
4. **Graph Rendering:**
   - Parse the `directed_acyclic_graph` list and the `skill_tree_nodes` from the JSON response.
   - Construct React Flow `nodes` and `edges`. The UI should visually represent the skill dependencies (prerequisites pointing to advanced topics).
5. **Interactive UI / Side Panel:**
   - Map the `node_id` of each UI element to its corresponding validated data.
   - Implement an `onNodeClick` handler. When a user clicks a node in the graph, open a side panel or modal.
   - The side panel must display the concept's name, the validated `explanation`, and the `source_section_header` from which it was derived.
6. **Aesthetics:** Ensure the design is modern, clean, and highly readable. Show an engaging UI when the user first visits before selecting or uploading a paper.

## Context
This UI is the final deliverable for the user, allowing them to visually explore the skill tree of a paper, read the strictly-grounded context for each concept, and manage their cached papers.
