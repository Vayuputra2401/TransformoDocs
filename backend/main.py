from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import router as ai_router

app = FastAPI(
    title="TransformoDocs API",
    description="Agentic Backend for Document Processing and RAG",
    version="2.0.0"
)

# Setup CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "TransformoDocs API is running"}
