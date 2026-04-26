from typing import List, Dict, Any
import json
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

    async def process_paper(self, pdf_path: str) -> Dict[str, Any]:
        chunks = self.ingester.parse_pdf(pdf_path)
        initial_state = {
            "raw_text": chunks,
            "skill_tree_nodes": [],
            "unprocessed_nodes": [],
            "skeleton_dag": [],
            "final_dag": None,
            "audit_feedback": None,
            "audit_revision_count": 0
        }
        final_state = await self.graph.ainvoke(initial_state)
        
        skill_tree_nodes = final_state.get("skill_tree_nodes", [])
        final_dag = final_state.get("final_dag", {})
        
        title = await self._get_title(chunks)

        return {
            "directed_acyclic_graph": final_dag.get("directed_acyclic_graph", []),
            "skill_tree_nodes": skill_tree_nodes,
            "raw_text": final_state.get("raw_text", []),
            "unprocessed_nodes": final_state.get("unprocessed_nodes", []),
            "metadata": {
                "title": title
            }
        }

    async def process_paper_stream(self, pdf_path: str):
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
            "audit_revision_count": 0
        }

        last_state = initial_state
        async for event in self.graph.astream_events(initial_state, version="v2"):
            kind = event["event"]
            if kind == "on_chain_start":
                node_name = event.get("metadata", {}).get("langgraph_node")
                if node_name:
                    yield {"type": "node_start", "node": node_name}
                elif event["name"] == "LangGraph":
                    yield {"type": "status", "content": "Initializing pipeline..."}
            
            elif kind == "on_chain_end":
                node_name = event.get("metadata", {}).get("langgraph_node")
                if node_name:
                    output = event.get("data", {}).get("output")
                    yield {
                        "type": "node_end", 
                        "node": node_name, 
                        "output": output
                    }
                elif event["name"] == "LangGraph":
                    last_state = event.get("data", {}).get("output")
                    yield {"type": "status", "content": "Concept extraction finished."}

        # --- FINAL RESULT FROM STATE ---
        skill_tree_nodes = last_state.get("skill_tree_nodes", [])
        final_dag = last_state.get("final_dag", {})
        
        title = await self._get_title(chunks)
        final_result = {
            "directed_acyclic_graph": final_dag.get("directed_acyclic_graph", []),
            "skill_tree_nodes": skill_tree_nodes,
            "raw_text": last_state.get("raw_text", []),
            "unprocessed_nodes": last_state.get("unprocessed_nodes", []),
            "metadata": {
                "title": title
            }
        }
        
        yield {"type": "final_result", "data": final_result}
        yield {"type": "status", "content": "Pipeline finished."}
