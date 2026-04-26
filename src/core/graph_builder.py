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
        builder.add_node("cartographer", self.agents.cartographer)
        
        # Add the branch subgraph as a node
        branch_graph = self._build_branch_graph()
        builder.add_node("branch_worker", branch_graph)
        
        # Define Edges
        builder.add_edge(START, "cartographer")
        builder.add_conditional_edges(
            "cartographer",
            self._distribute_nodes
        )
        
        builder.add_edge("branch_worker", END)
        
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
                "critique_feedback": None
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
