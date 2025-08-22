from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json

from game_manager import *
from connection_manager import connection_manager
from schemas import *

async def broadcast_room_update(room_id: str):
    try:
        room = game_manager.get_room(room_id)
        public_view = create_public_room_view(room)
        public_message = WsMessage(
            type="public_state_update",
            payload=public_view.model_dump()
        )
        await connection_manager.broadcast(room_id, public_message.model_dump_json())
    except HTTPException:
        print(f"Cannot broadcast update for non-existent room {room_id}")
    
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

game_manager.set_connection_manager(connection_manager) 
game_manager.set_broadcast_callback(broadcast_room_update)

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
    return create_personalized_room_view(room, for_client_id=request_body.host_client_id)

@app.post("/api/rooms/{room_id}/join", response_model=GameRoomPersonalizedResponse, tags=["Lobby"])
@limiter.limit("60/minute")
async def join_room_endpoint(room_id: str, request_body: JoinRoomRequest, request: Request):
    try:
        internal_room = game_manager.join_room(room_id, request_body.player_name, request_body.player_client_id)
        public_view = create_public_room_view(internal_room)
        public_message = WsMessage(
            type="public_state_update",
            payload=public_view.model_dump()
        )
        await connection_manager.broadcast(room_id, public_message.model_dump_json())
        return create_personalized_room_view(internal_room, for_client_id=request_body.player_client_id)
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
    return create_personalized_room_view(internal_room, for_client_id=client_id)

@app.put("/api/rooms/{room_id}/roles", status_code=status.HTTP_200_OK, tags=["Room Settings"])
async def set_roles_settings_endpoint(room_id: str, request_body: SetRolesRequest, client_id: str = Header(..., alias="X-Client-ID")):
    try:
        internal_room = game_manager.set_roles_settings(room_id, client_id, request_body.roles)
        public_view = create_public_room_view(internal_room)
        public_message = WsMessage(
            type="public_state_update",
            payload=public_view.model_dump()
        )
        await connection_manager.broadcast(room_id, public_message.model_dump_json())
        return {"status": "success", "message": "Roles updated"}
    except HTTPException as e:
        raise e
     
@app.put("/api/rooms/{room_id}/environ", status_code=status.HTTP_200_OK, tags=["Room Settings"])
async def set_environ_endpoint(room_id: str, request_body: SetEnvironRequest, client_id: str = Header(..., alias="X-Client-ID")):
    try:
        internal_room = game_manager.set_environ(room_id, client_id, request_body.environ)
        public_view = create_public_room_view(internal_room)
        public_message = WsMessage(
            type="public_state_update",
            payload=public_view.model_dump()
        )
        await connection_manager.broadcast(room_id, public_message.model_dump_json())
        return {"status": "success", "message": "Environment updated"}
    except HTTPException as e:
        raise e
    
    
@app.post("/api/rooms/{room_id}/start", tags=["Game"])
async def start_game_endpoint(room_id: str, client_id: str = Header(..., alias="X-Client-ID")):
    try:
        internal_room = game_manager.start_game(room_id, client_id)

        for player in internal_room.players:
            personalized_view = create_personalized_room_view(internal_room, for_client_id=player.client_id)

            personal_message = WsMessage(
                type="personal_state_update",
                payload=personalized_view.model_dump()
            )
            await connection_manager.send_personal_message(
                room_id, player.client_id, personal_message.model_dump_json()
            )
        
        return {"status": "success", "message": "Game started"}

    except HTTPException as e:
        raise e
    
@app.post("/api/rooms/{room_id}/act", status_code=status.HTTP_200_OK, tags=["Game"])
async def player_action_endpoint(room_id: str, action: PlayerActionRequest, client_id: str = Header(..., alias="X-Client-ID")):
    try:
        await game_manager.process_action(room_id, client_id, action)
        return {"status": "success", "message": "Action received"}
    except HTTPException as e: raise e


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
    finally:
        print(f"Cleaning up connection for {client_id} in room {room_id}")
        connection_manager.disconnect(room_id, client_id)
        game_manager.schedule_player_removal(room_id, client_id)