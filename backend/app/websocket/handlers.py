from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.websocket.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/{vehicle_id}")
async def vehicle_websocket(websocket:WebSocket, vehicle_id: str):
    await manager.connect(vehicle_id,websocket)
    try:
        while True:
            message = await websocket.receive_json()
            await manager.broadcast({
                "vehicle_id": vehicle_id,
                "message": message
            })

    except:
        manager.disconnect(vehicle_id)