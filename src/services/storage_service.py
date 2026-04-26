import os
import json
import hashlib
from typing import Dict, Any, List, Optional

class StorageService:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.pdf_dir = os.path.join(cache_dir, "pdfs")
        self.tree_dir = os.path.join(cache_dir, "skill_trees")
        self._init_dirs()

    def _init_dirs(self):
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.tree_dir, exist_ok=True)

    def get_file_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def save_pdf(self, file_hash: str, content: bytes) -> str:
        path = os.path.join(self.pdf_dir, f"{file_hash}.pdf")
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(content)
        return path

    def get_pdf_path(self, file_hash: str) -> Optional[str]:
        path = os.path.join(self.pdf_dir, f"{file_hash}.pdf")
        return path if os.path.exists(path) else None

    def save_skill_tree(self, tree_id: str, data: Dict[str, Any]):
        path = os.path.join(self.tree_dir, f"{tree_id}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load_skill_tree(self, tree_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.tree_dir, f"{tree_id}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return None

    def delete_skill_tree(self, tree_id: str):
        # Delete JSON
        json_path = os.path.join(self.tree_dir, f"{tree_id}.json")
        if os.path.exists(json_path):
            os.remove(json_path)
        
        # Delete PDF
        pdf_path = os.path.join(self.pdf_dir, f"{tree_id}.pdf")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    def update_skill_tree_metadata(self, tree_id: str, metadata: Dict[str, Any]):
        data = self.load_skill_tree(tree_id)
        if data:
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"].update(metadata)
            self.save_skill_tree(tree_id, data)

    def list_skill_trees(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.tree_dir):
            return []
        
        trees = []
        for filename in os.listdir(self.tree_dir):
            if filename.endswith(".json"):
                tree_id = filename.replace(".json", "")
                data = self.load_skill_tree(tree_id)
                title = tree_id[:12] + "..."
                if data and "metadata" in data and "title" in data["metadata"]:
                    title = data["metadata"]["title"]
                elif data and "raw_text" in data and len(data["raw_text"]) > 0:
                    # Fallback to first chunk if no title in metadata
                    title = data["raw_text"][0].get("raw_text", tree_id)[:50]
                
                trees.append({"id": tree_id, "title": title})
        
        return sorted(trees, key=lambda x: x["title"])
