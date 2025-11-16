from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import asyncio
import time

class RoomStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class GamePhase(str, Enum):
    INTRODUCTION_NIGHT = "introduction_night"
    INTRODUCTION_DAY = "introduction_day"
    JOKE_VOTING = "joke_voting"
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

class ActionType(str, Enum):
    INTRODUCE = "introduce"
    READY_FOR_VOTE = "ready_for_vote" 
    VOTE = "vote" 
    MAFIA_KILL = "mafia_kill"
    DOCTOR_HEAL = "doctor_heal"
    COMMISSAR_CHECK = "commissar_check"
    WHORE_BLOCK = "whore_block"

class Player(BaseModel):
    client_id: str 
    name: str
    is_alive: bool = True
    role: Optional[PlayerRole] = None
    description: Optional[str] = None

class Roles (BaseModel):
    mafia: int = 0
    citizen: int = 0
    doctor: int = 0
    comissar: int = 0
    whore: int = 0

class Winner(str, Enum):
    mafia = "mafia"
    citizens = "citizens"

class NightActions(BaseModel):
    mafia_kill_votes: Dict[str, str] = Field(default_factory=dict) 
    doctor_heal_votes: Dict[str, str] = Field(default_factory=dict)
    commissar_check_votes: Dict[str, str] = Field(default_factory=dict)
    whore_block_votes: Dict[str, str] = Field(default_factory=dict)

class GameRoom(BaseModel):
    room_id: str
    players: List[Player] = []
    status: RoomStatus = RoomStatus.WAITING
    host_id: str
    roles: Roles = Field(default_factory=Roles)
    environ: Optional[str] = None
    phase: Optional[GamePhase] = None
    day_number: int = 0
    pre_generated_narration: Optional[Dict] = Field(default=None, exclude=True)
    pre_generation_task: Optional[asyncio.Task] = Field(default=None, exclude=True)
    phase_start_time: Optional[float] = Field(default=None, exclude=True)
    phase_duration: Optional[float] = Field(default=None, exclude=True)

    ready_votes: Dict[str, bool] = Field(default_factory=dict)
    joke_votes: Dict[str, str] = Field(default_factory=dict)
    lynch_votes: Dict[str, str] = Field(default_factory=dict)
    active_narration: Optional[Dict] = None
    night_actions: NightActions = Field(default_factory=NightActions)
    last_events: List[Dict[str, Any]] = Field(default_factory=list)
    winner: Optional[Winner] = None

    phase_event: Optional[asyncio.Event] = Field(default=None, exclude=True)
    game_loop_task: Optional[asyncio.Task] = Field(default=None, exclude=True)
    lock: asyncio.Lock = Field(default_factory=asyncio.Lock, exclude=True) 

    class Config:
        arbitrary_types_allowed = True

class PlayerPublic(BaseModel):
    name: str
    is_alive: bool = True
    is_host: bool = False 
    has_acted: bool = False
    role: Optional[PlayerRole] = None

class GameRoomPublic(BaseModel):
    room_id: str
    players: List[PlayerPublic] = []
    status: RoomStatus
    phase: Optional[GamePhase]
    roles: Roles
    environ: Optional[str]
    day_number: int
    last_events: List[Dict[str, Any]] = Field(default_factory=list)
    winner: Optional[Winner] = None
    phase_time_left: Optional[float] = None
    phase_duration: Optional[float] = None
    active_narration: Optional[Dict] = None

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

class PlayerActionRequest(BaseModel):
    action_type: ActionType
    payload: Dict[str, Any]

class WsMessage(BaseModel):
    type: str
    payload: Dict[str, Any]

class GameRoomPersonalizedResponse(BaseModel):
    room_details: GameRoomPublic
    is_current_user_host: bool
    my_role: Optional[PlayerRole] = None
    winner: Optional[Winner] = None
    teammates: List[str] = Field(default_factory=list)
    team_votes: Dict[str, str] = Field(default_factory=dict)

class AINarration(BaseModel):
    title: str = Field(description="Креативный, атмосферный заголовок события.")
    summary: str = Field(description="Сухой, фактический итог события в одном предложении.")
    narration: str = Field(description="Полное, креативное и атмосферное описание события.")

class AIContext(BaseModel):
    setting: str
    player_descriptions: Dict[str, str]
    history: List[str]