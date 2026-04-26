import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    MODEL_NAME = os.environ["MODEL_NAME"]
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
    CACHE_DIR = os.getenv("CACHE_DIR", "cache")
    PDF_CACHE_DIR = os.path.join(CACHE_DIR, "pdfs")
    SKILL_TREE_CACHE_DIR = os.path.join(CACHE_DIR, "skill_trees")
    ALLOWED_ORIGINS = ["http://localhost:5173"]
    DEFAULT_PASSING_GRADE = "B-"
