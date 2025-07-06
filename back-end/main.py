from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from game_manager import game_manager
from connection_manager import connection_manager
from schemas import CreateRoomRequest, JoinRoomRequest, GameRoom

app = FastAPI(title="Mafia Game Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/rooms", response_model=GameRoom, tags=["Lobby"])
def create_room_endpoint(request: CreateRoomRequest):
    room = game_manager.create_room(request.host_name, request.host_client_id)
    return room

@app.post("/api/rooms/{room_id}/join", response_model=GameRoom, tags=["Lobby"])
async def join_room_endpoint(room_id: str, request: JoinRoomRequest):
    try:
        room = game_manager.join_room(room_id, request.player_name, request.player_client_id)

        await connection_manager.broadcast(room_id, room.model_dump_json())
        return room
    except HTTPException as e:
        raise e

@app.get("/api/rooms/{room_id}", response_model=GameRoom, tags=["Lobby"])
def get_room_details_endpoint(room_id: str):
    return game_manager.get_room(room_id)


@app.websocket("/ws/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, client_id: str):
    try:
        room = game_manager.get_room(room_id)
        if not any(p.client_id == client_id for p in room.players):
            await websocket.close(code=4001, reason="Player not in room")
            return
    except HTTPException:
        await websocket.close(code=4004, reason="Room not found")
        return
        
    await connection_manager.connect(websocket, room_id)
    
    try:

        while True:
            data = await websocket.receive_text()

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, room_id)
        room.players = [p for p in room.players if p.client_id != client_id]
        await connection_manager.broadcast(room_id, room.model_dump_json())