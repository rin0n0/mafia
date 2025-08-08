from fastapi import HTTPException
import asyncio
from typing import Dict
import random
import string

from schemas import GameRoom, Player, GameRoomPersonalizedResponse, GameRoomPublic, PlayerPublic, Roles

class GameManager:
    def __init__(self):
        self.active_rooms: Dict[str, GameRoom] = {}
        self.MAX_ROOMS_PER_HOST = 3

    def _generate_room_id(self) -> str:
        while True:
            room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if room_id not in self.active_rooms:
                return room_id

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
    
    def set_broadcast_callback(self, callback):
        self._broadcast_callback = callback
    
    def schedule_player_removal(self, room_id: str, client_id: str, delay: int = 5):
        asyncio.create_task(self._remove_player_after_delay(room_id, client_id, delay))

    async def _remove_player_after_delay(self, room_id: str, client_id: str, delay: int):
        print(f"Player {client_id} disconnected. Removal for room {room_id} scheduled in {delay}s.")
        await asyncio.sleep(delay)

        from connection_manager import connection_manager

        try:
            room = self.get_room(room_id)
            
            if connection_manager.is_client_connected(room_id, client_id):
                print(f"Player {client_id} reconnected to {room_id}. Removal cancelled.")
                return

            print(f"Timeout expired. Removing player {client_id} from room {room_id}.")
            room.players = [p for p in room.players if p.client_id != client_id]
            
            if not room.players:
                del self.active_rooms[room_id]
                print(f"Room {room_id} is empty and has been deleted.")
            else:
                if room.host_id == client_id:
                    new_host = room.players[0]
                    room.host_id = new_host.client_id
                    print(f"Host left. New host for room {room_id} is {new_host.name}.")
                if hasattr(self, '_broadcast_callback'):
                    await self._broadcast_callback(room_id)
        except (HTTPException, KeyError):
            print(f"Room {room_id} no longer exists. No action needed for player {client_id}.")
            pass


    def set_roles_settings(self, room_id: str, client_id: str, new_roles: Roles) -> GameRoom:
        room = self.get_room(room_id)
        if client_id != room.host_id:
            raise HTTPException(status_code=403, detail="Только хост может менять настройки")
        
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
        room.environ = environ
        print(f"Room {room_id} environ updated: {room.environ}")
        return room



def create_public_room_view(room: GameRoom) -> GameRoomPublic:
    public_players = [
        PlayerPublic(
            name=p.name,
            is_alive=p.is_alive,
            is_host=(p.client_id == room.host_id)
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