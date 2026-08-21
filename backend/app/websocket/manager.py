from fastapi import WebSocket

class ConnectionManager:

    def __init__(self):
        self.active_connections: dict[str,WebSocket] = {}

    async def connect(self, vehicle_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[vehicle_id] = websocket

    def disconnect(self, vehicle_id: str):
        self.active_connections.pop(vehicle_id,None)

    async def send_to_vehicle(self, vehicle_id:str, message:dict):
        websocket = self.active_connections.get(vehicle_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message:dict):
        for websocket in self.active_connections.values():
            await websocket.send_json(message)