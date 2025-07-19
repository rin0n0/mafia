from fastapi import HTTPException
from typing import Dict
import random
import string

from schemas import GameRoom, Player, GameRoomPersonalizedResponse, GameRoomPublic, PlayerPublic, Roles

class GameManager:
    def __init__(self):
        self.active_rooms: Dict[str, GameRoom] = {}

    def _generate_room_id(self) -> str:
        while True:
            room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if room_id not in self.active_rooms:
                return room_id

    def create_room(self, host_name: str, host_client_id: str) -> GameRoom:
        room_id = self._generate_room_id()
        
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
    def set_roles_settings(self, room_id: str, client_id: str, new_roles: Roles ) -> GameRoom:
        room = self.get_room(room_id)
        if (client_id==room.host_id): 
            room.roles = new_roles
            print("roles assigned ", room.roles)
        else print("hack prevented")

    def set_environ(self, room_id: str, client_id: str, environ: str) -> GameRoom:
        room = self.get_room(room_id)
        if (client_id==room.host_id): 
            room.environ = environ
            print("environ assigned: ", room.environ)
        else print("hack prevented")


def create_personalized_room_view(room: GameRoom, for_client_id: str) -> GameRoomPersonalizedResponse:

    public_players = []
    for p in room.players:
        player_is_host = (p.client_id == room.host_id)
        public_players.append(
            PlayerPublic(
                name=p.name, 
                is_alive=p.is_alive, 
                is_host=player_is_host 
            )
        )
    
    public_room_details = GameRoomPublic(
        room_id=room.room_id,
        players=public_players,
        status=room.status
    )
    
    is_current_user_host = (room.host_id == for_client_id)
    
    return GameRoomPersonalizedResponse(
        room_details=public_room_details,
        is_current_user_host=is_current_user_host
    )

game_manager = GameManager()