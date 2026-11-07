import json
import os
import datetime
from typing import List, Dict, Any
from src.services.ingestion_service import PDFIngester
from src.core.graph_builder import GraphBuilder
from src.models.state import PaperChunkInput

class GraphService:
    def __init__(self, ingester: PDFIngester, graph_builder: GraphBuilder):
        self.ingester = ingester
        self.graph_builder = graph_builder
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            self._graph = self.graph_builder.build()
        return self._graph

    async def _get_title(self, chunks: List[Dict[str, Any]]) -> str:
        title = "Untitled Paper"
        for chunk in chunks[:3]:
            if chunk.get("section_header") == "Title" or chunk.get("section_header") == "Article":
                title = chunk.get("raw_text", "").split('\n')[0][:100]
                break
        if title == "Untitled Paper" and chunks:
            title = chunks[0].get("raw_text", "").split('\n')[0][:100]
        return title

    async def process_paper(self, pdf_path: str, complexity: str = "simple") -> Dict[str, Any]:
        chunks = self.ingester.parse_pdf(pdf_path)
        initial_state = {
            "raw_text": chunks,
            "skill_tree_nodes": [],
            "unprocessed_nodes": [],
            "skeleton_dag": [],
            "final_dag": None,
            "audit_feedback": None,
            "audit_revision_count": 0,
            "complexity": complexity,
            "specialists": [],
            "council_instructions": {},
            "node_evaluator_rubrics": {},
            "current_specialist_index": 0,
            "current_council_role": "",
            "council_chat_history": [],
            "council_critiques": [],
            "council_iteration_count": 0,
            "consensus_met": False,
            "proposed_plan": None
        }

        final_state = await self.graph.ainvoke(initial_state, config={"recursion_limit": 100})
        
        skill_tree_nodes = final_state.get("skill_tree_nodes", [])
        final_dag = final_state.get("final_dag", {})
        
        title = await self._get_title(chunks)

        return {
            "directed_acyclic_graph": final_dag.get("directed_acyclic_graph", []),
            "skill_tree_nodes": skill_tree_nodes,
            "raw_text": final_state.get("raw_text", []),
            "unprocessed_nodes": final_state.get("unprocessed_nodes", []),
            "metadata": {
                "title": title,
                "complexity": complexity,
                "node_evaluator_rubrics": final_state.get("node_evaluator_rubrics", {})
            }
        }

    async def process_paper_stream(self, pdf_path: str, complexity: str = "simple"):
        """
        Streams graph execution events for real-time visualization.
        """
        chunks = self.ingester.parse_pdf(pdf_path)
        initial_state = {
            "raw_text": chunks,
            "skill_tree_nodes": [],
            "unprocessed_nodes": [],
            "skeleton_dag": [],
            "final_dag": None,
            "audit_feedback": None,
            "audit_revision_count": 0,
            "complexity": complexity,
            "specialists": [],
            "council_instructions": {},
            "node_evaluator_rubrics": {},
            "current_specialist_index": 0,
            "current_council_role": "",
            "council_chat_history": [],
            "council_critiques": [],
            "council_iteration_count": 0,
            "consensus_met": False,
            "proposed_plan": None,
            "final_council_index": 0,
            "final_council_review_history": [],
            "council_phase": "brainstorm"
        }



        # Prepare logging
        if not os.path.exists("logs"):
            os.makedirs("logs")
        pdf_base = os.path.basename(pdf_path).split('.')[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/{pdf_base}_{timestamp}.log"
        
        def write_log(content: str):
            with open(log_filename, "a") as f:
                f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {content}\n")

        write_log(f"Starting session for: {pdf_path} (Complexity: {complexity})")

        last_state = initial_state
        async for event in self.graph.astream_events(initial_state, version="v2", config={"recursion_limit": 100}):
            kind = event["event"]
            node_name = event.get("metadata", {}).get("langgraph_node")
            
            # --- START EVENT HANDLING ---
            if kind == "on_chain_start":
                if node_name:
                    # Robust extraction from dict or list
                    raw_input = event.get("data", {}).get("input")
                    input_data = {}
                    if isinstance(raw_input, dict):
                        input_data = raw_input
                    elif isinstance(raw_input, list) and raw_input:
                        for item in reversed(raw_input):
                            if isinstance(item, dict):
                                input_data = item
                                break
                    
                    if node_name == "branch_worker":
                        # Skip the container node, we only care about the agents inside it
                        continue

                    agent_name = node_name
                    if node_name == "council_member":
                        raw_role = input_data.get("current_council_role")
                        if raw_role and isinstance(raw_role, str) and raw_role.strip():
                            agent_name = raw_role
                        else:
                            agent_name = "Council Member"
                    elif node_name == "expert":
                        node_data = input_data.get('current_node_under_review') or {}
                        concept_name = node_data.get('concept_name') if isinstance(node_data, dict) else None
                        agent_name = f"Expert ({concept_name or '...'})"
                    
                    write_log(f"Agent Start: {agent_name}")
                    yield {"type": "agent_start", "agent": agent_name}
                elif event.get("name") == "LangGraph":
                    yield {"type": "status", "content": "Initializing pipeline..."}
            
            # --- END EVENT HANDLING ---
            elif kind == "on_chain_end":
                raw_output = event.get("data", {}).get("output")
                output = raw_output if isinstance(raw_output, dict) else {}
                
                # Update last_state incrementally with SMART MERGING
                if isinstance(output, dict):
                    for state_key in ["skill_tree_nodes", "unprocessed_nodes", "raw_text", "node_evaluator_rubrics", "skeleton_dag"]:
                        if state_key in output and output[state_key]:
                            if isinstance(output[state_key], list):
                                # Merge lists by ID if possible, or cumulatively
                                if state_key == "skill_tree_nodes":
                                    current_nodes = {n.get("node_id"): n for n in last_state.get("skill_tree_nodes", []) if n.get("node_id")}
                                    for new_node in output[state_key]:
                                        node_id = new_node.get("node_id")
                                        if node_id:
                                            current_nodes[node_id] = new_node
                                    last_state["skill_tree_nodes"] = list(current_nodes.values())
                                    write_log(f"DEBUG: last_state['skill_tree_nodes'] size now {len(last_state['skill_tree_nodes'])}")
                                else:
                                    # For other lists like unprocessed_nodes, we usually want the latest full version
                                    last_state[state_key] = output[state_key]
                            else:
                                last_state[state_key] = output[state_key]
                    
                    # Special handling for final_dag edges
                    if "final_dag" in output and output["final_dag"]:
                        new_edges = output["final_dag"].get("directed_acyclic_graph", [])
                        if len(new_edges) >= len(last_state.get("final_dag", {}).get("directed_acyclic_graph", [])):
                            last_state["final_dag"] = output["final_dag"]
                            write_log(f"DEBUG: last_state['final_dag'] updated with {len(new_edges)} edges")

                # Handle Top-Level Completion
                if event.get("name") == "LangGraph":
                    # Update last_state, but ONLY if output has substantive data
                    if isinstance(output, dict) and (output.get("skill_tree_nodes") or output.get("final_dag")):
                        last_state = output
                    yield {"type": "status", "content": "Processing complete."}
                    continue

                # Extract input data for context
                raw_input = event.get("data", {}).get("input")
                input_data = {}
                if isinstance(raw_input, dict):
                    input_data = raw_input
                elif isinstance(raw_input, list) and raw_input:
                    for item in reversed(raw_input):
                        if isinstance(item, dict):
                            input_data = item
                            break
                
                # --- PROCESS EVENTS BEFORE LOGGING SKIP ---
                if isinstance(output, dict):
                    # Cartographer
                    if "unprocessed_nodes" in output:
                        nodes = output["unprocessed_nodes"]
                        edges = output.get("skeleton_dag") or last_state.get("skeleton_dag") or []
                        yield {
                            "type": "skeleton_discovered", 
                            "nodes": nodes,
                            "edges": edges
                        }
                    
                    # Node Finalization (at the end of branch_worker)
                    elif "skill_tree_nodes" in output and node_name == "branch_worker":
                        for node in output["skill_tree_nodes"]:
                            yield {"type": "node_finalized", "node": node}

                    # Synthesizer
                    elif "final_dag" in output and output["final_dag"]:
                        edges = output["final_dag"].get("directed_acyclic_graph", [])
                        nodes = output.get("skill_tree_nodes", [])
                        yield {
                            "type": "graph_synthesized", 
                            "edges": edges,
                            "nodes": nodes if nodes else last_state.get("skill_tree_nodes", [])
                        }

                if not node_name or node_name == "branch_worker":
                    continue

                # Safe extraction of role/concept
                current_role = output.get("current_role_snapshot") or input_data.get("current_council_role")
                
                agent_name = node_name
                if node_name == "council_member":
                    agent_name = current_role or "Council Member"
                elif node_name == "expert":
                    node_data = input_data.get('current_node_under_review') or {}
                    concept_name = node_data.get('concept_name') if isinstance(node_data, dict) else None
                    agent_name = f"Expert ({concept_name or '...'})"
                
                write_log(f"Agent Stop: {agent_name}")
                yield {"type": "agent_stop", "agent": agent_name}
                
                # Extract messages/reasoning if they exist
                if isinstance(output, dict):
                    # Council Member / Pedagogical Expert
                    role_from_output = output.get("current_role_snapshot")
                    
                    if "council_chat_history" in output and output["council_chat_history"]:
                        last_msg = output["council_chat_history"][-1]
                        msg_role = last_msg.get("role") or role_from_output or agent_name
                        write_log(f"{msg_role}: {last_msg.get('message')}")
                        yield {"type": "agent_message", "agent": msg_role, "content": last_msg.get("message")}
                    elif "final_council_review_history" in output and output["final_council_review_history"]:
                        last_msg = output["final_council_review_history"][-1]
                        msg_role = last_msg.get("role") or role_from_output or agent_name
                        write_log(f"{msg_role}: {last_msg.get('message')}")
                        yield {"type": "agent_message", "agent": msg_role, "content": last_msg.get("message")}
                    elif role_from_output and "council_critiques" in output:
                        write_log(f"{role_from_output} (Critique): {output['council_critiques'][-1]}")
                        yield {"type": "agent_message", "agent": role_from_output, "content": f"Critique: {output['council_critiques'][-1]}"}
                    elif "proposed_plan" in output and isinstance(output["proposed_plan"], dict):
                        plan = output["proposed_plan"]
                        strategy = plan.get("progression_strategy")
                        if strategy:
                            write_log(f"Pedagogical Expert Strategy: {strategy}")
                            yield {"type": "agent_message", "agent": "Pedagogical Expert", "content": strategy}
                    
                    # Recruiter
                    elif "field_of_study" in output:
                        recruiter_msg = f"Field of Study: {output['field_of_study']}. Specialists: {', '.join(output.get('specialists', []))}"
                        write_log(f"Recruiter: {recruiter_msg}")
                        yield {"type": "agent_message", "agent": "Recruiter", "content": recruiter_msg}
                    
                    # Expert (inside branch_worker)
                    elif "draft_analysis" in output and node_name == "expert":
                        draft = output["draft_analysis"]
                        yield {"type": "agent_message", "agent": f"Expert ({draft.get('concept_name')})", "content": draft.get("explanation")}
                    
                    # Validator (inside branch_worker)
                    elif "critique_feedback" in output and node_name == "validator":
                        critique = output["critique_feedback"]
                        if not critique.get("is_valid"):
                            yield {"type": "agent_message", "agent": "Validator", "content": f"Issues found: {json.dumps(critique.get('hallucination_flags', []))}"}
                    
                    # Structural Auditor
                    elif "audit_feedback" in output and node_name == "structural_auditor":
                        feedback = output["audit_feedback"]
                        yield {"type": "agent_message", "agent": "Structural Auditor", "content": feedback.get("reasoning", "Audit complete.")}

        # --- FINAL RESULT FROM STATE ---
        skill_tree_nodes = last_state.get("skill_tree_nodes", [])
        final_dag = last_state.get("final_dag") or {}
        
        title = await self._get_title(chunks)
        final_result = {
            "directed_acyclic_graph": final_dag.get("directed_acyclic_graph", []),
            "skill_tree_nodes": skill_tree_nodes,
            "raw_text": last_state.get("raw_text", []),
            "unprocessed_nodes": last_state.get("unprocessed_nodes", []),
            "metadata": {
                "title": title,
                "complexity": complexity,
                "node_evaluator_rubrics": last_state.get("node_evaluator_rubrics", {})
            }
        }
        
        yield {"type": "final_result", "data": final_result}
        yield {"type": "status", "content": "Pipeline finished."}
