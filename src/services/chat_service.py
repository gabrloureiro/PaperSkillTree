from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from src.services.storage_service import StorageService
from src.agents.chat_agents import ExaminerAgent, TutorAgent

class ChatService:
    def __init__(self, storage_service: StorageService, examiner: ExaminerAgent, tutor: TutorAgent):
        self.storage_service = storage_service
        self.examiner = examiner
        self.tutor = tutor

    def get_node_context(self, tree_id: str, node_id: str):
        tree_data = self.storage_service.load_skill_tree(tree_id)
        if not tree_data:
            raise HTTPException(status_code=404, detail="Skill tree not found")
            
        nodes = tree_data.get("skill_tree_nodes", [])
        unprocessed = tree_data.get("unprocessed_nodes", [])
        raw_texts = tree_data.get("raw_text", [])
        
        node = next((n for n in nodes if n["node_id"] == node_id), None)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found in skill tree")
            
        unprocessed_node = next((n for n in unprocessed if n["node_id"] == node_id), None)
        raw_text_chunk = ""
        if unprocessed_node:
            section_header = unprocessed_node.get("source_section_header")
            matching_chunk = next((c for c in raw_texts if c.get("section_header") == section_header), None)
            if matching_chunk:
                raw_text_chunk = matching_chunk.get("raw_text", "")
                
        return node, raw_text_chunk

    def chat_examiner(self, tree_id: str, node_id: str, message: str, chat_history: List[Dict[str, str]]):
        node, raw_text = self.get_node_context(tree_id, node_id)
        return self.examiner.interact(
            concept_name=node.get("concept_name", node_id),
            explanation=node.get("explanation", ""),
            raw_text=raw_text,
            message=message,
            chat_history=chat_history
        )

    def chat_tutor(self, tree_id: str, node_id: str, message: str, chat_history: List[Dict[str, str]]):
        node, raw_text = self.get_node_context(tree_id, node_id)
        return self.tutor.interact(
            concept_name=node.get("concept_name", node_id),
            explanation=node.get("explanation", ""),
            raw_text=raw_text,
            message=message,
            chat_history=chat_history
        )
