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

    def list_skill_trees(self) -> List[str]:
        if not os.path.exists(self.tree_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(self.tree_dir) if f.endswith(".json")]
