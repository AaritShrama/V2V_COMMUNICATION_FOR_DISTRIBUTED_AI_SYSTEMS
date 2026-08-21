from fastapi import FastAPI
from backend.app.schemas.semantic_message import SemanticMessage

app = FastAPI(
    title="Ditributed AI System Backend",
    version="0.1.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "av-backend" 
    }

@app.post("/events")
async def recieve_event(message : SemanticMessage):
    return {
        "status": "recieved",
        "message": message
    }