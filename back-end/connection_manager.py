from fastapi  import WebSocket
from typing import Dict


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, client_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][client_id] = websocket
        print(f"Client {client_id} connected to room {room_id}")

    def disconnect(self, room_id: str, client_id: str):
        if room_id in self.active_connections and client_id in self.active_connections[room_id]:
            del self.active_connections[room_id][client_id]
            print(f"Client {client_id} disconnected from room {room_id}")

    async def broadcast(self, room_id: str, message: str):
        if room_id in self.active_connections:
            for client_id, connection in list(self.active_connections[room_id].items()):
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Failed to send message to {client_id}: {e}")

    def is_client_connected(self, room_id: str, client_id: str) -> bool:
        return room_id in self.active_connections and client_id in self.active_connections[room_id]
    
    async def send_personal_message(self, room_id: str, client_id: str, message: str):
        if room_id in self.active_connections and client_id in self.active_connections[room_id]:
            websocket = self.active_connections[room_id][client_id]
            await websocket.send_text(message)

connection_manager = ConnectionManager()