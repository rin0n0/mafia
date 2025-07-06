from pydantic import BaseModel, Field
from typing import List, Optional


class Player(BaseModel):
    client_id: str 
    name: str
    is_host: bool = False
    is_alive: bool = True
    role: Optional[str] = None

class GameRoom(BaseModel):
    room_id: str
    players: List[Player] = []
    status: str = 'waiting'

class CreateRoomRequest(BaseModel):
    host_name: str
    host_client_id: str

class JoinRoomRequest(BaseModel):
    player_name: str
    player_client_id: str