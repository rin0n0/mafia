# src/connection_manager.py
from fastapi import WebSocket
import asyncio
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, (WebSocket, asyncio.Queue)]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, client_id: str):
        if self.is_client_connected(room_id, client_id):
            old_websocket, old_queue = self.active_connections[room_id][client_id]
            await old_websocket.close(code=1008, reason="New connection established.")
            print(f"Client {client_id} reconnected, closing old socket.")

        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        
        queue = asyncio.Queue()
        self.active_connections[room_id][client_id] = (websocket, queue)
        print(f"Client {client_id} connected to room {room_id}")
        return queue

    def disconnect(self, room_id: str, client_id: str):
        if room_id in self.active_connections and client_id in self.active_connections[room_id]:
            del self.active_connections[room_id][client_id]
            print(f"Client {client_id} disconnected from room {room_id}")

    async def broadcast(self, room_id: str, message: str):
        if room_id in self.active_connections:
            for client_id, (connection, queue) in self.active_connections[room_id].items():
                await queue.put(message)

    def is_client_connected(self, room_id: str, client_id: str) -> bool:
        return room_id in self.active_connections and client_id in self.active_connections[room_id]
    
    async def send_personal_message(self, room_id: str, client_id: str, message: str):
        if self.is_client_connected(room_id, client_id):
            connection, queue = self.active_connections[room_id][client_id]
            await queue.put(message)
