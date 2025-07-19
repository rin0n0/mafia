from pydantic import BaseModel, Field
from typing import List, Optional

class Player(BaseModel):
    client_id: str 
    name: str
    is_alive: bool = True
    role: Optional[str] = None

class Roles (BaseModel):
    mafia: int = 0
    citizen: int = 0
    doctor: int = 0
    comissar: int = 0
    whore: int = 0

class GameRoom(BaseModel):
    room_id: str
    players: List[Player] = []
    status: str = 'waiting'
    host_id: str  
    roles: Roles = Field(default_factory=Roles)
    environ: str = None

class PlayerPublic(BaseModel):
    name: str
    is_alive: bool = True
    is_host: bool = False 

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

class SetRolesRequest(BaseModel):
    client_id: str
    roles: Roles

class SetEnvironRequest(BaseModel):
    client_id: str
    environ: str | None


class GameRoomPersonalizedResponse(BaseModel):
    room_details: GameRoomPublic
    is_current_user_host: bool
