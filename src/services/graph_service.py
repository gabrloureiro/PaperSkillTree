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

    def process_paper(self, pdf_path: str) -> Dict[str, Any]:
        # 1. Parse PDF
        chunks = self.ingester.parse_pdf(pdf_path)
        
        # 2. Initialize State
        initial_state = {
            "raw_text": chunks,
            "skill_tree_nodes": [],
            "current_node_under_review": None,
            "current_raw_text_under_review": "",
            "draft_analysis": None,
            "critique_feedback": None,
            "validation_status": False,
            "unprocessed_nodes": [],
            "revision_count": 0,
            "final_dag": None
        }
        
        # 3. Run Graph
        final_state = self.graph.invoke(initial_state)
        
        # 4. Extract Results
        final_dag = final_state.get("final_dag") or {}
        return {
            "directed_acyclic_graph": final_dag.get("directed_acyclic_graph", []),
            "skill_tree_nodes": final_state.get("skill_tree_nodes", []),
            "raw_text": final_state.get("raw_text", []),
            "unprocessed_nodes": final_state.get("unprocessed_nodes", [])
        }
