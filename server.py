import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict

from src.core.config import Config
from src.services.storage_service import StorageService
from src.services.llm_service import LLMService
from src.services.ingestion_service import PDFIngester
from src.services.graph_service import GraphService
from src.services.chat_service import ChatService
from src.agents.chat_agents import ExaminerAgent, TutorAgent
from src.agents.pipeline_agents import PipelineAgents
from src.core.graph_builder import GraphBuilder

class ChatRequest(BaseModel):
    node_id: str
    tree_id: str
    message: str
    chat_history: List[Dict[str, str]]

app = FastAPI(title="PaperSkillTree API", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Service Container ---
storage_service = StorageService(Config.CACHE_DIR)
llm_service = LLMService(Config.MODEL_NAME, Config.TEMPERATURE)
ingester = PDFIngester()
pipeline_agents = PipelineAgents(llm_service)
graph_builder = GraphBuilder(pipeline_agents)
graph_service = GraphService(ingester, graph_builder)
examiner_agent = ExaminerAgent(llm_service)
tutor_agent = TutorAgent(llm_service)
chat_service = ChatService(storage_service, examiner_agent, tutor_agent)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    file_hash = storage_service.get_file_hash(content)
    
    # Check cache
    cached_tree = storage_service.load_skill_tree(file_hash)
    if cached_tree:
        return JSONResponse(content={"status": "cached", "tree_data": cached_tree})
    
    # Save PDF
    pdf_path = storage_service.save_pdf(file_hash, content)
            
    try:
        # Process paper using GraphService
        tree_data = await graph_service.process_paper(pdf_path)
        
        # Save results
        storage_service.save_skill_tree(file_hash, tree_data)
            
        return JSONResponse(content={"status": "success", "tree_data": tree_data})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-stream")
async def upload_pdf_stream(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    file_hash = storage_service.get_file_hash(content)
    pdf_path = storage_service.save_pdf(file_hash, content)
            
    async def event_generator():
        try:
            async for event in graph_service.process_paper_stream(pdf_path):
                if event.get("type") == "final_result":
                    storage_service.save_skill_tree(file_hash, event["data"])
                yield f"data: {json.dumps(event)}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'tree_id': file_hash})}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/skill-trees")
async def list_skill_trees():
    try:
        trees = storage_service.list_skill_trees()
        return {"skill_trees": trees}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/skill-trees/{tree_id}")
async def get_skill_tree(tree_id: str):
    try:
        cached_tree = storage_service.load_skill_tree(tree_id)
        if not cached_tree:
            raise HTTPException(status_code=404, detail="Skill tree not found")
        return JSONResponse(content={"status": "success", "tree_data": cached_tree})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/skill-trees/{tree_id}")
async def delete_skill_tree(tree_id: str):
    try:
        storage_service.delete_skill_tree(tree_id)
        return {"status": "success", "message": f"Skill tree {tree_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RenameRequest(BaseModel):
    title: str

@app.patch("/skill-trees/{tree_id}")
async def rename_skill_tree(tree_id: str, req: RenameRequest):
    try:
        storage_service.update_skill_tree_metadata(tree_id, {"title": req.title})
        return {"status": "success", "message": f"Skill tree {tree_id} renamed to {req.title}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/examiner")
async def chat_examiner(req: ChatRequest):
    try:
        result = await chat_service.chat_examiner(req.tree_id, req.node_id, req.message, req.chat_history)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/tutor")
async def chat_tutor(req: ChatRequest):
    try:
        result = await chat_service.chat_tutor(req.tree_id, req.node_id, req.message, req.chat_history)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
