from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from src.models.state import PaperState
from src.agents.pipeline_agents import PipelineAgents

class GraphBuilder:
    def __init__(self, agents: PipelineAgents):
        self.agents = agents

    def build(self):
        builder = StateGraph(PaperState)
        
        # Add Nodes from agents
        builder.add_node("cartographer", self.agents.cartographer)
        builder.add_node("select_next_node", self._select_next_node)
        builder.add_node("expert", self.agents.expert)
        builder.add_node("validator", self.agents.validator)
        builder.add_node("resolution", self.agents.resolution)
        builder.add_node("commit_node", self._commit_node)
        builder.add_node("synthesizer", self.agents.synthesizer)
        
        # Add Edges
        builder.add_edge(START, "cartographer")
        builder.add_edge("cartographer", "select_next_node")
        
        builder.add_conditional_edges(
            "select_next_node",
            self._route_after_select,
            {
                "expert": "expert",
                "synthesizer": "synthesizer"
            }
        )
        
        builder.add_edge("expert", "validator")
        
        builder.add_conditional_edges(
            "validator",
            self._route_after_validator,
            {
                "commit_node": "commit_node",
                "resolution": "resolution",
                "select_next_node": "select_next_node"
            }
        )
        
        builder.add_edge("resolution", "validator")
        builder.add_edge("commit_node", "select_next_node")
        builder.add_edge("synthesizer", END)
        
        return builder.compile()

    def _select_next_node(self, state: PaperState) -> Dict[str, Any]:
        unprocessed = state.get("unprocessed_nodes", [])
        if not unprocessed:
            return {
                "current_node_under_review": None,
                "current_raw_text_under_review": ""
            }
        
        next_node = unprocessed[0]
        remaining_nodes = unprocessed[1:]
        
        target_header = next_node.get("source_section_header", "")
        chunks = state.get("raw_text", [])
        
        relevant_texts = []
        for chunk in chunks:
            if isinstance(chunk, dict):
                raw_text = chunk.get("raw_text", "")
                section_header = chunk.get("section_header", "")
                if target_header and section_header == target_header:
                    relevant_texts.append(raw_text)
                    
        if relevant_texts:
            current_raw_text = "\n\n".join(relevant_texts)
        else:
            current_raw_text = chunks[0].get("raw_text", "") if chunks else ""
        
        return {
            "unprocessed_nodes": remaining_nodes,
            "current_node_under_review": next_node,
            "current_raw_text_under_review": current_raw_text,
            "revision_count": 0,
            "draft_analysis": None,
            "critique_feedback": None,
            "validation_status": False
        }

    def _commit_node(self, state: PaperState) -> Dict[str, Any]:
        draft = state.get("draft_analysis")
        return {
            "skill_tree_nodes": [draft] if draft else [],
            "current_node_under_review": None,
            "draft_analysis": None,
            "critique_feedback": None,
            "validation_status": False,
            "revision_count": 0
        }

    def _route_after_select(self, state: PaperState) -> str:
        if state.get("current_node_under_review"):
            return "expert"
        return "synthesizer"

    def _route_after_validator(self, state: PaperState) -> str:
        if state.get("validation_status"):
            return "commit_node"
        else:
            revision_count = state.get("revision_count", 0)
            if revision_count < 3:
                return "resolution"
            else:
                return "select_next_node"
