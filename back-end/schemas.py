from pydantic import BaseModel
from typing import List, Optional

class Player(BaseModel):
    client_id: str 
    name: str
    is_alive: bool = True
    role: Optional[str] = None

class GameRoom(BaseModel):
    room_id: str
    players: List[Player] = []
    status: str = 'waiting'
    host_id: str  

class PlayerPublic(BaseModel):
    name: str
    is_alive: bool = True

class GameRoomPublic(BaseModel):
    room_id: str
    players: List[PlayerPublic] = []
    status: str = 'waiting'

class CreateRoomRequest(BaseModel):
    host_name: str
    host_client_id: str

class JoinRoomRequest(BaseModel):
    player_name: str
    player_client_id: str


class GameRoomPersonalizedResponse(BaseModel):
    room_details: GameRoomPublic
    is_current_user_host: bool