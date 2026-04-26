import os

class Config:
    MODEL_NAME = "gemini-3.1-pro"
    TEMPERATURE = 0.0
    CACHE_DIR = "cache"
    PDF_CACHE_DIR = os.path.join(CACHE_DIR, "pdfs")
    SKILL_TREE_CACHE_DIR = os.path.join(CACHE_DIR, "skill_trees")
    ALLOWED_ORIGINS = ["http://localhost:5173"]
