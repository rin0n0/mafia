from fastapi import FastAPI, WebSocket, Header, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json
import asyncio

from connection_manager import ConnectionManager
from game_notifier import GameNotifier
from game_manager import GameManager
from schemas import *

connection_manager = ConnectionManager()
game_notifier = GameNotifier(connection_manager)
game_manager = GameManager(game_notifier)

async def websocket_receiver(websocket: WebSocket, room_id: str, client_id: str):
    async for data in websocket.iter_text():
        try:
            message_data = json.loads(data)
            await game_manager.process_websocket_message(room_id, client_id, message_data)
        except (json.JSONDecodeError, KeyError):
            print(f"Received invalid WebSocket message from {client_id}")

async def websocket_sender(websocket: WebSocket, queue: asyncio.Queue):
    while True:
        message = await queue.get()
        await websocket.send_text(message)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Mafia Game Backend")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/rooms", response_model=GameRoomPersonalizedResponse, tags=["Lobby"])
@limiter.limit("5/minute")
def create_room_endpoint(request_body: CreateRoomRequest, request: Request):
    room = game_manager.create_room(request_body.host_name, request_body.host_client_id)
    return game_notifier._create_personalized_room_view(room, for_client_id=request_body.host_client_id)

@app.post("/api/rooms/{room_id}/join", response_model=GameRoomPersonalizedResponse, tags=["Lobby"])
@limiter.limit("60/minute")
async def join_room_endpoint(room_id: str, request_body: JoinRoomRequest, request: Request):
    try:
        internal_room = game_manager.join_room(room_id, request_body.player_name, request_body.player_client_id)
        await game_notifier.notify_room_update(internal_room)
        return game_notifier._create_personalized_room_view(internal_room, for_client_id=request_body.player_client_id)
    except HTTPException as e:
        raise e

@app.get("/api/rooms/{room_id}", response_model=GameRoomPersonalizedResponse, tags=["Lobby"])
def get_room_details_endpoint(room_id: str, client_id: str = Header(..., alias="X-Client-ID")):
    internal_room = game_manager.get_room(room_id)
    is_member = any(p.client_id == client_id for p in internal_room.players)
    if not is_member:
        raise HTTPException(
            status_code=403, 
            detail="Вы не являетесь участником этой комнаты"
        )
    return game_notifier._create_personalized_room_view(internal_room, for_client_id=client_id)

@app.put("/api/rooms/{room_id}/roles", status_code=status.HTTP_200_OK, tags=["Room Settings"])
async def set_roles_settings_endpoint(room_id: str, request_body: SetRolesRequest, client_id: str = Header(..., alias="X-Client-ID")):
    try:
        internal_room = game_manager.set_roles_settings(room_id, client_id, request_body.roles)
        await game_notifier.notify_room_update(internal_room)
        return {"status": "success", "message": "Roles updated"}
    except HTTPException as e:
        raise e
     
@app.put("/api/rooms/{room_id}/environ", status_code=status.HTTP_200_OK, tags=["Room Settings"])
async def set_environ_endpoint(room_id: str, request_body: SetEnvironRequest, client_id: str = Header(..., alias="X-Client-ID")):
    try:
        internal_room = game_manager.set_environ(room_id, client_id, request_body.environ)
        await game_notifier.notify_room_update(internal_room)
        return {"status": "success", "message": "Environment updated"}
    except HTTPException as e:
        raise e
    
@app.post("/api/rooms/{room_id}/start", response_model=GameRoomPersonalizedResponse, tags=["Game"])
async def start_game_endpoint(room_id: str, client_id: str = Header(..., alias="X-Client-ID")):
    try:
        internal_room = await game_manager.start_game(room_id, client_id)
        await game_notifier.notify_room_update(internal_room)
        return game_notifier._create_personalized_room_view(internal_room, for_client_id=client_id)
        
    except HTTPException as e:
        raise e
    
@app.post("/api/rooms/{room_id}/act", status_code=status.HTTP_200_OK, tags=["Game"])
async def player_action_endpoint(room_id: str, action: PlayerActionRequest, client_id: str = Header(..., alias="X-Client-ID")):
    try:
        await game_manager.process_action(room_id, client_id, action)
        return {"status": "success", "message": "Action received"}
    except HTTPException as e:
        raise e

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
        
    queue = await connection_manager.connect(websocket, room_id, client_id)
    
    receiver_task = asyncio.create_task(websocket_receiver(websocket, room_id, client_id))
    sender_task = asyncio.create_task(websocket_sender(websocket, queue))

    try:
        done, pending = await asyncio.wait(
            [receiver_task, sender_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
    except Exception as e:
        print(f"Error in WebSocket handler for {client_id}: {e}")
    finally:
        print(f"Cleaning up connection for {client_id} in room {room_id}")
        connection_manager.disconnect(room_id, client_id)
        game_manager.schedule_player_removal(room_id, client_id)