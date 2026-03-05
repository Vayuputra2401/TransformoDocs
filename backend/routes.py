import os
import time
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

# Internal packages
from src.data_engineering import DataEngineer
from src.rag_pipeline import RAGPipeline
from src.agents import AgenticWorkflow
from src.mlops import MLOpsTracker

router = APIRouter()

# Global instances of our AI logic
# Note: In production we'd want dependency injection, but global state suffices for MVP caching
de_service = DataEngineer()
rag_service = RAGPipeline()
mlops_tracker = MLOpsTracker()
agent_service = AgenticWorkflow(rag_service)

# Temporary directory for file processing
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# Datastore (InMemory dictionary for MVP simulating DB)
documents_db = {}


class ChatRequest(BaseModel):
    query: str
    document_id: str


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Handles document upload, structuring, and indexing."""
    start_time = time.time()
    
    # Generate unique ID for the document
    doc_id = str(uuid.uuid4())
    temp_file_path = os.path.join(TEMP_DIR, f"{doc_id}_{file.filename}")

    try:
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Extract and Structure (PyTesseract/Pandas inside)
        structured_data = de_service.process_file(temp_file_path)
        
        # 2. Ingest to VectorDB
        success = rag_service.ingest_data(structured_data)
        
        # Save state
        documents_db[doc_id] = structured_data
        
        # MLOps Telemetry
        duration = time.time() - start_time
        mlops_tracker.log_agent_execution(
            query="Ingestion via API",
            processing_time_sec=duration,
            source_doc_length=structured_data["metadata"]["character_count"],
            success=success
        )

        return {
            "document_id": doc_id,
            "filename": file.filename,
            "message": "Document successfully processed and indexed.",
            "metrics": {
                "character_count": structured_data["metadata"]["character_count"],
                "word_count": structured_data["metadata"]["word_count"],
                "processing_time_sec": round(duration, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.get("/document/{document_id}")
async def get_document(document_id: str):
    """Returns the structured JSON data for the UI."""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found.")
    return documents_db[document_id]


@router.post("/chat")
async def chat_with_document(request: ChatRequest):
    """Executes the CrewAI Multi-Agent workflow."""
    if request.document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found.")

    start_time = time.time()
    try:
        response = agent_service.execute_analytical_query(request.query)
        
        # MLOps
        mlops_tracker.log_agent_execution(
            query=request.query,
            processing_time_sec=time.time() - start_time,
            source_doc_length=documents_db[request.document_id]["metadata"]["character_count"],
            success=True
        )

        return {
            "query": request.query,
            "answer": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")
