from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, client_id: str):
        if self.is_client_connected(room_id, client_id):
            old_websocket = self.active_connections[room_id][client_id]
            await old_websocket.close(code=1008, reason="New connection established from another location.")
            print(f"Client {client_id} reconnected, closing old socket.")

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
            connections_to_send: List[WebSocket] = list(self.active_connections[room_id].values())
            for connection in connections_to_send:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Failed to send message: {e}")

    def is_client_connected(self, room_id: str, client_id: str) -> bool:
        return room_id in self.active_connections and client_id in self.active_connections[room_id]
    
    async def send_personal_message(self, room_id: str, client_id: str, message: str):
        if self.is_client_connected(room_id, client_id):
            websocket = self.active_connections[room_id][client_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"Failed to send personal message to {client_id}: {e}")

connection_manager = ConnectionManager()