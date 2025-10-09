import logging
from typing import Dict

from schemas import *
from connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

class GameNotifier:
    def __init__(self, connection_manager: ConnectionManager):
        self._connection_manager = connection_manager

    async def notify_room_update(self, room: GameRoom):
        """
        Главный метод рассылки. Отправляет КАЖДОМУ игроку его
        персональное состояние комнаты.
        """
        if not self._connection_manager:
            logger.warning(f"Room {room.room_id}: ConnectionManager is not set.")
            return

        for player in room.players:
            if self._connection_manager.is_client_connected(room.room_id, player.client_id):
                personalized_view = self._create_personalized_room_view(room, for_client_id=player.client_id)
                message = WsMessage(
                    type="personal_state_update",
                    payload=personalized_view.model_dump()
                )
                await self._connection_manager.send_personal_message(
                    room.room_id, player.client_id, message.model_dump_json()
                )

    async def send_personal_event(self, room_id: str, client_id: str, text: str):
        """Отправляет одноразовое ТЕКСТОВОЕ событие (для Комиссара)."""
        message = WsMessage(type="personal_event", payload={"text": text})
        await self._connection_manager.send_personal_message(room_id, client_id, message.model_dump_json())

    async def send_team_activity_update(self, room_id: str, client_id: str, payload: Dict):
        """Отправляет обновление о действии союзника."""
        message = WsMessage(type="team_activity_update", payload=payload)
        await self._connection_manager.send_personal_message(room_id, client_id, message.model_dump_json())

    async def send_emote_notification(self, room_id: str, client_id: str, payload: Dict):
        """Отправляет уведомление о полученном эмодзи."""
        message = WsMessage(type="receive_emote", payload=payload)
        await self._connection_manager.send_personal_message(room_id, client_id, message.model_dump_json())

    def _create_public_room_view(self, room: GameRoom) -> GameRoomPublic:
        public_players = []
        for p in room.players:
            acted = False
            # Ночью публичный has_acted всегда false
            if room.phase != GamePhase.NIGHT:
                if room.phase == GamePhase.INTRODUCTION_NIGHT: acted = p.description is not None
                elif room.phase in [GamePhase.INTRODUCTION_DAY, GamePhase.DAY]: acted = p.client_id in room.ready_votes
                elif room.phase == GamePhase.JOKE_VOTING: acted = p.client_id in room.joke_votes
                elif room.phase == GamePhase.VOTING: acted = p.client_id in room.lynch_votes
            
            public_players.append(PlayerPublic(
                name=p.name, is_alive=p.is_alive, is_host=(p.client_id == room.host_id), 
                has_acted=acted, role=p.role if room.status == RoomStatus.FINISHED else None
            ))
            
        return GameRoomPublic(
            room_id=room.room_id, players=public_players, status=room.status,
            roles=room.roles, environ=room.environ, phase=room.phase, day_number=room.day_number,
            last_events=room.last_events, winner=room.winner
        )

    def _create_personalized_room_view(self, room: GameRoom, for_client_id: str) -> GameRoomPersonalizedResponse:
        public_view = self._create_public_room_view(room)
        current_player = next((p for p in room.players if p.client_id == for_client_id), None)
        
        if current_player:
            # Вычисляем РЕАЛЬНЫЙ has_acted для этого игрока
            real_has_acted = False
            phase = room.phase
            if phase == GamePhase.NIGHT:
                votes_map = {
                    PlayerRole.MAFIA: room.night_actions.mafia_kill_votes,
                    PlayerRole.DOCTOR: room.night_actions.doctor_heal_votes,
                    PlayerRole.COMMISSAR: room.night_actions.commissar_check_votes,
                    PlayerRole.WHORE: room.night_actions.whore_block_votes,
                }
                if current_player.role in votes_map:
                    vote_dict = votes_map[current_player.role]
                    if vote_dict:
                        real_has_acted = current_player.client_id in vote_dict
            else: # Для всех остальных фаз берем из public_view
                player_in_public_view = next((pv for pv in public_view.players if pv.name == current_player.name), None)
                if player_in_public_view:
                    real_has_acted = player_in_public_view.has_acted

            # Обновляем has_acted в "публичной" части персонализированного ответа
            my_public_player_view = next((p for p in public_view.players if p.name == current_player.name), None)
            if my_public_player_view:
                my_public_player_view.has_acted = real_has_acted

        # ... (остальная логика для teammates, team_votes и т.д. без изменений)
        is_host = (room.host_id == for_client_id)
        my_role = current_player.role if current_player else None
        
        teammates_list = []
        if my_role and my_role != PlayerRole.CITIZEN:
            for p in room.players:
                if p.role == my_role and p.is_alive and p.client_id != for_client_id:
                    teammates_list.append(p.name)

        team_votes_map = {}
        if room.phase == GamePhase.NIGHT and my_role and my_role != PlayerRole.CITIZEN:
            votes_attr_map = {
                PlayerRole.MAFIA: room.night_actions.mafia_kill_votes,
                PlayerRole.DOCTOR: room.night_actions.doctor_heal_votes,
                PlayerRole.COMMISSAR: room.night_actions.commissar_check_votes,
                PlayerRole.WHORE: room.night_actions.whore_block_votes,
            }
            current_team_votes = votes_attr_map.get(my_role)
            if current_team_votes:
                id_to_name_map = {p.client_id: p.name for p in room.players}
                for voter_id, target_id in current_team_votes.items():
                    voter_name = id_to_name_map.get(voter_id)
                    target_name = id_to_name_map.get(target_id)
                    if voter_name and target_name: team_votes_map[voter_name] = target_name

        return GameRoomPersonalizedResponse(
            room_details=public_view, is_current_user_host=is_host, my_role=my_role,
            winner=room.winner, teammates=teammates_list, team_votes=team_votes_map
        )
