from fastapi import HTTPException
import asyncio
import random
import string
from collections import Counter
from typing import Dict, List, Coroutine, Any

from schemas import *
from connection_manager import ConnectionManager

class GameManager:
    def __init__(self):
        self.active_rooms: Dict[str, GameRoom] = {}
        self.MAX_ROOMS_PER_HOST = 3
        self._broadcast_callback: Coroutine[str, None, None] | None = None
        self._connection_manager: ConnectionManager | None = None

    def set_connection_manager(self, manager: ConnectionManager): self._connection_manager = manager
    def set_broadcast_callback(self, callback): self._broadcast_callback = callback

    def _generate_room_id(self) -> str:
        while True:
            room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if room_id not in self.active_rooms:
                return room_id
            
    def _sanitize_for_llm(self, text: str) -> str:
        return f"{{{{{text}}}}}"

    def create_room(self, host_name: str, host_client_id: str) -> GameRoom:
        room_id = self._generate_room_id()

        current_host_rooms = 0
        for room in self.active_rooms.values():
            if room.host_id == host_client_id:
                current_host_rooms += 1
        
        if current_host_rooms >= self.MAX_ROOMS_PER_HOST:
            raise HTTPException(
                status_code=403, 
                detail=f"Вы уже создали максимальное количество комнат ({self.MAX_ROOMS_PER_HOST})."
            )
        
        host_player = Player(
            client_id=host_client_id,
            name=host_name,
        )
        
        new_room = GameRoom(
            room_id=room_id,
            players=[host_player],
            host_id = host_player.client_id,
        )
        
        self.active_rooms[room_id] = new_room
        print(f"Room created: {room_id}. Host: {host_name} ({host_client_id})")
        return new_room

    def get_room(self, room_id: str) -> GameRoom:
        room = self.active_rooms.get(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Комната не найдена")
        return room

    def join_room(self, room_id: str, player_name: str, player_client_id: str) -> GameRoom:
        room = self.get_room(room_id)

        if room.status != 'waiting':
            raise HTTPException(status_code=400, detail="Игра уже началась")
        if any(p.client_id == player_client_id for p in room.players):
            raise HTTPException(status_code=400, detail="Вы уже в этой комнате")
            
        if any(p.name == player_name for p in room.players):
            raise HTTPException(status_code=400, detail=f"Имя '{player_name}' уже занято")
        
        new_player = Player(client_id=player_client_id, name=player_name)
        room.players.append(new_player)
        
        print(f"Player {player_name} ({player_client_id}) joined room {room_id}")
        return room
    
    def start_game(self, room_id: str, client_id: str) -> GameRoom:
        room = self.get_room(room_id)

        if client_id != room.host_id:
            raise HTTPException(status_code=403, detail="Только хост может начать игру")

        if room.status != RoomStatus.WAITING:
            raise HTTPException(status_code=400, detail="Игра уже началась или завершена")

        total_roles = sum(room.roles.model_dump().values())
        if len(room.players) != total_roles:
            raise HTTPException(
                status_code=400, 
                detail=f"Количество игроков ({len(room.players)}) не совпадает с количеством ролей ({total_roles})"
            )
        
        roles_to_distribute = []
        for role, count in room.roles.model_dump().items():
            roles_to_distribute.extend([PlayerRole(role)] * count)
        
        random.shuffle(roles_to_distribute)
        
        shuffled_players = random.sample(room.players, len(room.players))
        
        for player, role in zip(shuffled_players, roles_to_distribute):
            player.role = role
        
        room.status = RoomStatus.IN_PROGRESS
        room.phase = GamePhase.INTRODUCTION_NIGHT
        room.day_number = 0

        task = asyncio.create_task(self._game_loop(room))
        room.game_loop_task = task
        print(f"Game started in room {room_id}. Roles distributed.")
        return room
    
    def set_broadcast_callback(self, callback):
        self._broadcast_callback = callback

    async def _game_loop(self, room: GameRoom):
        try:
            await self._handle_introduction_night(room)
            await self._handle_introduction_day(room)

            print(f"Game loop for room {room.room_id} finished (placeholder).")
        except asyncio.CancelledError:
            print(f"Game loop for room {room.room_id} was cancelled.")
        except Exception as e:
            print(f"Error in game loop for room {room.room_id}: {e}")

    async def _handle_introduction_night(self, room: GameRoom):
        room.phase = GamePhase.INTRODUCTION_NIGHT
        room.phase_event = asyncio.Event()
        await self._broadcast_callback(room.room_id)
        print(f"Room {room.room_id}: Starting INTRODUCTION_NIGHT. Waiting for descriptions for 60s.")
        try: await asyncio.wait_for(room.phase_event.wait(), timeout=60.0)
        except asyncio.TimeoutError: print(f"Room {room.room_id}: Introduction timeout reached.")
        finally: room.phase_event = None

    async def _handle_introduction_day(self, room: GameRoom):
        room.phase = GamePhase.INTRODUCTION_DAY
        room.day_number = 1
        room.phase_event = asyncio.Event()
        await self._broadcast_callback(room.room_id)

        joke_vote_message = WsMessage(type="joke_vote_started", payload={"question": "Кто здесь самый крутой житель?"})
        if self._connection_manager: await self._connection_manager.broadcast(room.room_id, joke_vote_message.model_dump_json())
        print(f"Room {room.room_id}: Starting INTRODUCTION_DAY. Joke vote started.")
        try: await asyncio.wait_for(room.phase_event.wait(), timeout=90.0)
        except asyncio.TimeoutError: print(f"Room {room.room_id}: Joke vote timeout reached.")
        finally:
            vote_counts = Counter(room.day_votes.values())
            winner_id = vote_counts.most_common(1)[0][0] if vote_counts else None
            winner_player = next((p for p in room.players if p.client_id == winner_id), None)
            winner_name = winner_player.name if winner_player else "Никто"
            result_text = f"В шуточном голосовании победил(а) {self._sanitize_for_llm(winner_name)}!"
            
            room.last_events.append({"type": "joke_vote_result", "text": result_text})
            results_message = WsMessage(type="vote_results", payload={"text": result_text})
            if self._connection_manager: await self._connection_manager.broadcast(room.room_id, results_message.model_dump_json())
            
            room.day_votes.clear()
            room.phase_event = None
            room.phase = GamePhase.NIGHT
            await self._broadcast_callback(room.room_id)

    async def process_action(self, room_id: str, client_id: str, action: PlayerActionRequest):
        room = self.get_room(room_id)
        player = next((p for p in room.players if p.client_id == client_id), None)
        if not player or not player.is_alive: raise HTTPException(status_code=403, detail="Действие недоступно")
        
        if room.phase == GamePhase.INTRODUCTION_NIGHT and action.action_type == ActionType.INTRODUCE:
            self._handle_introduce_action(room, player, action.payload)
        elif room.phase == GamePhase.INTRODUCTION_DAY and action.action_type == ActionType.VOTE:
            self._handle_vote_action(room, player, action.payload)
        else: 
            raise HTTPException(status_code=400, detail="Неверное действие для текущей фазы")
        
        await self._broadcast_callback(room_id)

    def _handle_introduce_action(self, room: GameRoom, player: Player, payload: dict):
        description = payload.get("description")
        player.description = self._sanitize_for_llm(description) if description else ""
        print(f"Player {player.name} submitted description.")
        self._check_phase_completion(room)

    def _handle_vote_action(self, room: GameRoom, player: Player, payload: dict):
        if player.client_id in room.day_votes: raise HTTPException(status_code=400, detail="Вы уже голосовали")
        target_name = payload.get("target_name")
        target_player = next((p for p in room.players if p.name == target_name and p.is_alive), None)
        if not target_player: raise HTTPException(status_code=404, detail=f"Игрок с именем '{target_name}' не найден")

        room.day_votes[player.client_id] = target_player.client_id
        print(f"Player {player.name} voted for {target_player.name}")
        self._check_phase_completion(room)

    def _check_phase_completion(self, room: GameRoom):
        if room.phase_event and room.phase_event.is_set(): return

        alive_players = [p for p in room.players if p.is_alive]
        
        if room.phase == GamePhase.INTRODUCTION_NIGHT:
            if all(p.description is not None for p in alive_players):
                if room.phase_event: room.phase_event.set()
        elif room.phase == GamePhase.INTRODUCTION_DAY:
            if len(room.day_votes) == len(alive_players):
                if room.phase_event: room.phase_event.set()

    def schedule_player_removal(self, room_id: str, client_id: str, delay: int = 10):
        asyncio.create_task(self._remove_player_after_delay(room_id, client_id, delay))

    async def _remove_player_after_delay(self, room_id: str, client_id: str, delay: int):
        await asyncio.sleep(delay)
        if not self._connection_manager or self._connection_manager.is_client_connected(room_id, client_id):
            return
        
        try:
            room = self.get_room(room_id)
            room.players = [p for p in room.players if p.client_id != client_id]
            
            if not room.players:
                self._delete_room(room_id)
                return

            if room.host_id == client_id:
                room.host_id = room.players[0].client_id
            
            self._check_phase_completion(room) 
            await self._broadcast_callback(room_id)
        except (HTTPException, KeyError): pass

    def _delete_room(self, room_id: str):
        if room_id in self.active_rooms:
            room = self.active_rooms[room_id]
            if room.game_loop_task and not room.game_loop_task.done():
                room.game_loop_task.cancel()
            del self.active_rooms[room_id]
            print(f"Room {room_id} and its tasks have been deleted.")

    def set_roles_settings(self, room_id: str, client_id: str, new_roles: Roles) -> GameRoom:
        room = self.get_room(room_id)
        if client_id != room.host_id:
            raise HTTPException(status_code=403, detail="Только хост может менять настройки")
        
        if room.status != RoomStatus.WAITING: 
            raise HTTPException(status_code=400, detail="Нельзя менять настройки после начала игры")

        total_roles = sum(new_roles.model_dump().values())
        if len(room.players) != total_roles:
            raise HTTPException(status_code=400, detail=f"Количество ролей ({total_roles}) не совпадает с количеством игроков ({len(room.players)})")
        
        if len(room.players) / 3 < new_roles.mafia:
            raise HTTPException(status_code=400, detail="Мафии не может быть больше трети игроков")

        room.roles = new_roles
        print(f"Room {room_id} roles updated: {room.roles}")
        return room

    def set_environ(self, room_id: str, client_id: str, environ: str) -> GameRoom:
        room = self.get_room(room_id)
        if client_id != room.host_id:
            raise HTTPException(status_code=403, detail="Только хост может менять настройки")
        if room.status != RoomStatus.WAITING: 
            raise HTTPException(status_code=400, detail="Нельзя менять настройки после начала игры")
        room.environ = environ
        print(f"Room {room_id} environ updated: {room.environ}")
        return room



def create_public_room_view(room: GameRoom) -> GameRoomPublic:
    public_players = [
        PlayerPublic(
            name=p.name,
            is_alive=p.is_alive,
            is_host=(p.client_id == room.host_id),
            has_acted=(
                (room.phase == GamePhase.INTRODUCTION_NIGHT and p.description is not None) or
                (room.phase == GamePhase.INTRODUCTION_DAY and p.client_id in room.day_votes)

            )
        ) for p in room.players
    ]
    return GameRoomPublic(
        room_id=room.room_id,
        players=public_players,
        status=room.status,
        roles=room.roles,
        environ=room.environ,
        phase=room.phase,             
        day_number=room.day_number
    )

def create_personalized_room_view(room: GameRoom, for_client_id: str) -> GameRoomPersonalizedResponse:
    public_view = create_public_room_view(room)
    is_host = (room.host_id == for_client_id)
    
    current_player_role = None
    for player in room.players:
        if player.client_id == for_client_id:
            current_player_role = player.role
            break

    return GameRoomPersonalizedResponse(
        room_details=public_view,
        is_current_user_host=is_host,
        my_role=current_player_role
    )



game_manager = GameManager()