from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class RoomStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class GamePhase(str, Enum):
    INTRODUCTION_NIGHT = "introduction_night"
    INTRODUCTION_DAY = "introduction_day"
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"
    GAME_OVER = "game_over"

class PlayerRole(str, Enum):
    MAFIA = "mafia"
    CITIZEN = "citizen"
    DOCTOR = "doctor"
    COMMISSAR = "comissar"
    WHORE = "whore"

class Player(BaseModel):
    client_id: str 
    name: str
    is_alive: bool = True
    role: Optional[PlayerRole] = None

class Roles (BaseModel):
    mafia: int = 0
    citizen: int = 0
    doctor: int = 0
    comissar: int = 0
    whore: int = 0

class Winner(str, Enum):
    MAFIA = "mafia"
    CITIZENS = "citizens"

class NightActions(BaseModel):
    mafia_kill_votes: Dict[str, str] = Field(default_factory=dict) 
    doctor_heal_target: Optional[str] = None
    commissar_check_target: Optional[str] = None
    whore_block_target: Optional[str] = None

class GameRoom(BaseModel):
    room_id: str
    players: List[Player] = []
    status: RoomStatus = RoomStatus.WAITING
    host_id: str  
    roles: Roles = Field(default_factory=Roles)
    environ: Optional[str] = None
    phase: Optional[GamePhase] = None    
    day_number: int = 0
    day_votes: Dict[str, str] = Field(default_factory=dict)
    night_actions: NightActions = Field(default_factory=NightActions)
    last_events: List[Dict[str, Any]] = Field(default_factory=list)
    winner: Optional[Winner] = None

class PlayerPublic(BaseModel):
    name: str
    is_alive: bool = True
    is_host: bool = False 

class GameRoomPublic(BaseModel):
    room_id: str
    players: List[PlayerPublic] = []
    status: RoomStatus
    phase: Optional[GamePhase]
    roles: Roles
    environ: Optional[str]
    day_number: int

class CreateRoomRequest(BaseModel):
    host_name: str
    host_client_id: str

class JoinRoomRequest(BaseModel):
    player_name: str
    player_client_id: str

class SetRolesRequest(BaseModel):
    roles: Roles

class SetEnvironRequest(BaseModel):
    environ: str | None


class GameRoomPersonalizedResponse(BaseModel):
    room_details: GameRoomPublic
    is_current_user_host: bool
    my_role: Optional[PlayerRole] = None
    
