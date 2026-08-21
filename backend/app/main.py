from fastapi import FastAPI
from backend.app.schemas.semantic_message import SemanticMessage
from backend.app.websocket.handlers import router as websocket_router

app = FastAPI(
    title="Ditributed AI System Backend",
    version="0.1.0"
)

app.include_router(websocket_router)

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