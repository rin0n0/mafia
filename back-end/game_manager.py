from fastapi import HTTPException
from typing import Dict
import random
import string

from schemas import GameRoom, Player

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
            is_host=True
        )
        
        new_room = GameRoom(
            room_id=room_id,
            players=[host_player]
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

game_manager = GameManager()