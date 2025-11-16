import logging
from typing import Dict

from schemas import *
from connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

class GameNotifier:
    def __init__(self, connection_manager: ConnectionManager):
        self._connection_manager = connection_manager
    def is_client_connected(self, room_id: str, client_id: str) -> bool:
        return self._connection_manager.is_client_connected(room_id, client_id)
    async def close_and_remove_room_connections(self, room_id: str):
        await self._connection_manager.close_and_remove_room_connections(room_id)
    async def notify_room_update(self, room: GameRoom):
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
        message = WsMessage(type="personal_event", payload={"text": text})
        await self._connection_manager.send_personal_message(room_id, client_id, message.model_dump_json())

    async def send_team_activity_update(self, room_id: str, client_id: str, payload: Dict):
        message = WsMessage(type="team_activity_update", payload=payload)
        await self._connection_manager.send_personal_message(room_id, client_id, message.model_dump_json())

    async def send_emote_notification(self, room_id: str, client_id: str, payload: Dict):
        message = WsMessage(type="receive_emote", payload=payload)
        await self._connection_manager.send_personal_message(room_id, client_id, message.model_dump_json())

    def _create_public_room_view(self, room: GameRoom) -> GameRoomPublic:
        public_players = []
        for p in room.players:
            acted = False
            if room.phase != GamePhase.NIGHT:
                if room.phase == GamePhase.INTRODUCTION_NIGHT: acted = p.description is not None
                elif room.phase in [GamePhase.INTRODUCTION_DAY, GamePhase.DAY]: acted = p.client_id in room.ready_votes
                elif room.phase == GamePhase.JOKE_VOTING: acted = p.client_id in room.joke_votes
                elif room.phase == GamePhase.VOTING: acted = p.client_id in room.lynch_votes

            public_players.append(PlayerPublic(
                name=p.name, is_alive=p.is_alive, is_host=(p.client_id == room.host_id), 
                has_acted=acted, role=p.role if room.status == RoomStatus.FINISHED else None
            ))

        phase_time_left: Optional[float] = None
        if room.phase_start_time and room.phase_duration:
            elapsed = time.time() - room.phase_start_time
            remaining = room.phase_duration - elapsed
            phase_time_left = max(0, remaining)
            
        return GameRoomPublic(
            room_id=room.room_id, 
            players=public_players, 
            status=room.status,
            roles=room.roles, 
            environ=room.environ, 
            phase=room.phase, 
            day_number=room.day_number,
            last_events=room.last_events, 
            winner=room.winner, 
            phase_time_left=phase_time_left, 
            phase_duration=room.phase_duration,
            active_narration=room.active_narration
        )

    def _create_personalized_room_view(self, room: GameRoom, for_client_id: str) -> GameRoomPersonalizedResponse:
        public_view = self._create_public_room_view(room)
        current_player = next((p for p in room.players if p.client_id == for_client_id), None)
        
        if current_player:
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
            else: 
                player_in_public_view = next((pv for pv in public_view.players if pv.name == current_player.name), None)
                if player_in_public_view:
                    real_has_acted = player_in_public_view.has_acted
            my_public_player_view = next((p for p in public_view.players if p.name == current_player.name), None)
            if my_public_player_view:
                my_public_player_view.has_acted = real_has_acted

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
