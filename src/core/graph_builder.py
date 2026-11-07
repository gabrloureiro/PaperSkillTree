from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from src.models.state import PaperState, BranchState, CartographerNode
from src.agents.pipeline_agents import PipelineAgents

class GraphBuilder:
    def __init__(self, agents: PipelineAgents):
        self.agents = agents

    def _build_branch_graph(self):
        """
        Builds the isolated subgraph for expert analysis and validation.
        This avoids race conditions on the shared state.
        """
        builder = StateGraph(BranchState)
        
        builder.add_node("expert", self.agents.expert)
        builder.add_node("validator", self.agents.validator)
        builder.add_node("resolution", self.agents.resolution)
        
        builder.add_edge(START, "expert")
        builder.add_edge("expert", "validator")
        
        # We don't provide a mapping, the router will return the node names or END directly
        builder.add_conditional_edges(
            "validator",
            self._route_after_validator
        )
        builder.add_edge("resolution", "validator")
        
        return builder.compile()

    def build(self):
        """
        Builds the main orchestrator graph.
        """
        builder = StateGraph(PaperState)
        
        # Add primary nodes
        builder.add_node("recruiter", self.agents.recruiter)
        
        # Council Nodes
        builder.add_node("council_member", self.agents.council_member)
        builder.add_node("pedagogical_expert", self.agents.pedagogical_expert)
        builder.add_node("council_handoff", self.agents.council_handoff)

        builder.add_node("cartographer", self.agents.cartographer)
        
        # Add the branch subgraph as a node
        branch_graph = self._build_branch_graph()
        builder.add_node("branch_worker", branch_graph)
        
        builder.add_node("synthesizer", self.agents.synthesizer)
        builder.add_node("structural_auditor", self.agents.structural_auditor)

        # Define Edges
        builder.add_edge(START, "recruiter")
        builder.add_conditional_edges(
            "recruiter",
            self._route_to_next_brainstormer
        )
        builder.add_conditional_edges(
            "council_member",
            self._route_after_council_member
        )
        builder.add_conditional_edges(
            "pedagogical_expert",
            self._route_after_pedagogical_expert
        )
        builder.add_edge("council_handoff", "cartographer")
        builder.add_conditional_edges(
            "cartographer",
            self._distribute_nodes
        )
        
        builder.add_edge("branch_worker", "synthesizer")
        builder.add_edge("synthesizer", "structural_auditor")
        
        builder.add_conditional_edges(
            "structural_auditor",
            self._route_after_auditor
        )
        
        return builder.compile()

    def _distribute_nodes(self, state: PaperState) -> List[Send]:
        """
        Fans out to multiple Branch subgraphs in parallel.
        """
        nodes = state.get("unprocessed_nodes") or []
        if not nodes:
            return [END]
            
        sends = []
        chunks = state.get("raw_text") or []
        
        for node in nodes:
            node_copy = node.copy()
            target_header = (node_copy.get("source_section_header") or "").strip().lower()
            
            relevant_texts = []
            for c in chunks:
                chunk_header = (c.get("section_header") or "").strip().lower()
                if target_header and (target_header in chunk_header or chunk_header in target_header):
                    relevant_texts.append(c.get("raw_text", ""))
            
            current_raw_text = "\n\n".join(relevant_texts).strip()
            
            # Robust Fallback
            if (not current_raw_text or len(current_raw_text) < 50) and chunks:
                fallback_chunks = chunks[:2] 
                current_raw_text = f"[General Context Provided]\n\n" + "\n\n".join([c.get("raw_text", "") for c in fallback_chunks])
                if not node_copy.get("source_section_header"):
                    node_copy["source_section_header"] = "General Context"

            # Initial state for the branch subgraph
            branch_initial_state = {
                "current_node_under_review": node_copy,
                "current_raw_text_under_review": current_raw_text,
                "revision_count": 0,
                "skill_tree_nodes": [],
                "raw_text": chunks,
                "available_nodes": nodes, # Pass full list for prerequisite selection
                "validation_status": False,
                "draft_analysis": None,
                "critique_feedback": None,
                "node_expert_instructions": state.get("council_instructions", {}).get("expert", "")
            }
            sends.append(Send("branch_worker", branch_initial_state))
            
        return sends

    async def _route_after_validator(self, state: BranchState) -> str:
        """
        Routing logic within the branch subgraph.
        """
        if state.get("validation_status") or state.get("revision_count", 0) >= 3:
            return END
        else:
            return "resolution"

    async def _route_after_auditor(self, state: PaperState) -> str:
        """
        Routing logic for the structural auditor.
        """
        # If we've transitioned to final_dag_review phase, it means the auditor passed or maxed out
        if state.get("council_phase") == "final_dag_review":
            return self._route_to_next_final_auditor(state)
        else:
            return "synthesizer"

    def _route_to_next_brainstormer(self, state: PaperState) -> str:
        specialists = state.get("specialists", [])
        index = state.get("current_specialist_index", 0)
        
        if index < len(specialists):
            return "council_member"
        else:
            return "pedagogical_expert"

    def _route_after_council_member(self, state: PaperState) -> str:
        phase = state.get("council_phase")
        if phase == "brainstorm":
            return self._route_to_next_brainstormer(state)
        elif phase == "plan_audit":
            return self._route_after_plan_audit(state)
        else: # final_dag_review
            return self._route_after_final_audit(state)

    def _route_after_plan_audit(self, state: PaperState) -> str:
        specialists = state.get("specialists", [])
        index = state.get("current_specialist_index", 0)
        
        if index < len(specialists):
            return "council_member"
        else:
            critiques = state.get("council_critiques", [])
            iteration = state.get("council_iteration_count", 0)
            
            if not critiques or iteration >= 3:
                return "council_handoff"
            else:
                return "pedagogical_expert"

    def _route_to_next_final_auditor(self, state: PaperState) -> str:
        specialists = state.get("specialists", [])
        index = state.get("final_council_index", 0)
        
        if index < len(specialists):
            return "council_member"
        else:
            return "pedagogical_expert"

    def _route_after_final_audit(self, state: PaperState) -> str:
        return self._route_to_next_final_auditor(state)

    def _route_after_pedagogical_expert(self, state: PaperState) -> str:
        if state.get("council_phase") == "rubric_generation":
            # pedagogical_expert sets this phase itself when it finishes the
            # final_dag_review pass, so the phase alone cannot tell us whether the
            # rubric pass has run yet. Only terminate once it has produced output.
            if state.get("node_evaluator_rubrics"):
                return END
            return "pedagogical_expert"
        else: # design or revision
            return "council_member"
