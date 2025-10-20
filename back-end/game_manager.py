import asyncio
import logging
import random
import string
from collections import Counter
from typing import Dict, List, Optional
import time

from fastapi import HTTPException

from schemas import *
from game_notifier import GameNotifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INTRO_NIGHT_DURATION = 60.0
DAY_DISCUSSION_DURATION = 180.0
JOKE_VOTING_DURATION = 90.0
NIGHT_DURATION = 120.0
VOTING_DURATION = 90.0
RESULTS_DISPLAY_PAUSE = 8.0
EVENT_HISTORY_LIMIT = 15

ACTIVE_NIGHT_ROLES = {PlayerRole.MAFIA, PlayerRole.DOCTOR, PlayerRole.COMMISSAR, PlayerRole.WHORE}

PHASE_TRANSITIONS: Dict[GamePhase, GamePhase] = {
    GamePhase.INTRODUCTION_NIGHT: GamePhase.INTRODUCTION_DAY,
    GamePhase.INTRODUCTION_DAY: GamePhase.JOKE_VOTING,
    GamePhase.JOKE_VOTING: GamePhase.NIGHT,
    GamePhase.NIGHT: GamePhase.DAY,
    GamePhase.DAY: GamePhase.VOTING,
    GamePhase.VOTING: GamePhase.NIGHT,
}

PHASE_DURATIONS: Dict[GamePhase, float] = {
    GamePhase.INTRODUCTION_NIGHT: INTRO_NIGHT_DURATION,
    GamePhase.INTRODUCTION_DAY: DAY_DISCUSSION_DURATION,
    GamePhase.JOKE_VOTING: JOKE_VOTING_DURATION,
    GamePhase.NIGHT: NIGHT_DURATION,
    GamePhase.DAY: DAY_DISCUSSION_DURATION,
    GamePhase.VOTING: VOTING_DURATION,
}

class GameManager:
    def __init__(self, notifier: GameNotifier):
        self.active_rooms: Dict[str, GameRoom] = {}
        self.MAX_ROOMS_PER_HOST = 3
        self._notifier = notifier

    def _generate_room_id(self) -> str:
        while True:
            room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if room_id not in self.active_rooms: return room_id

    def _sanitize_for_llm(self, text: str) -> str: return f"{{{{{text}}}}}"
    
    def get_room(self, room_id: str) -> GameRoom:
        room = self.active_rooms.get(room_id)
        if not room: raise HTTPException(status_code=404, detail="Комната не найдена")
        return room

    def create_room(self, host_name: str, host_client_id: str) -> GameRoom:
        room_id = self._generate_room_id()
        current_host_rooms = sum(1 for room in self.active_rooms.values() if room.host_id == host_client_id)
        if current_host_rooms >= self.MAX_ROOMS_PER_HOST:
            raise HTTPException(status_code=403, detail=f"Вы уже создали максимальное количество комнат ({self.MAX_ROOMS_PER_HOST}).")
        host_player = Player(client_id=host_client_id, name=host_name.strip())
        new_room = GameRoom(room_id=room_id, players=[host_player], host_id=host_player.client_id)
        self.active_rooms[room_id] = new_room
        return new_room

    def join_room(self, room_id: str, player_name: str, player_client_id: str) -> GameRoom:
        room = self.get_room(room_id)
        player_name_stripped = player_name.strip()
        if not player_name_stripped: raise HTTPException(status_code=400, detail="Имя не может быть пустым.")
        if room.status != RoomStatus.WAITING: raise HTTPException(status_code=400, detail="Игра уже началась")
        if any(p.client_id == player_client_id for p in room.players): raise HTTPException(status_code=400, detail="Вы уже в этой комнате")
        if any(p.name.lower() == player_name_stripped.lower() for p in room.players): raise HTTPException(status_code=400, detail=f"Имя '{player_name_stripped}' уже занято")
        new_player = Player(client_id=player_client_id, name=player_name_stripped)
        room.players.append(new_player)
        return room

    def start_game(self, room_id: str, client_id: str) -> GameRoom:
        room = self.get_room(room_id)
        if client_id != room.host_id: raise HTTPException(status_code=403, detail="Только хост может начать игру")
        if room.status != RoomStatus.WAITING: raise HTTPException(status_code=400, detail="Игра уже началась или завершена")
        total_roles = sum(room.roles.model_dump().values())
        if len(room.players) != total_roles: raise HTTPException(status_code=400, detail=f"Количество игроков ({len(room.players)}) не совпадает с количеством ролей ({total_roles})")
        
        roles_to_distribute = [PlayerRole(role) for role, count in room.roles.model_dump().items() for _ in range(count)]
        random.shuffle(roles_to_distribute)
        for player, role in zip(random.sample(room.players, len(room.players)), roles_to_distribute):
            player.role = role
        
        room.status = RoomStatus.IN_PROGRESS
        room.phase = GamePhase.INTRODUCTION_NIGHT
        room.day_number = 1
        
        room.game_loop_task = asyncio.create_task(self._game_loop(room))
        logger.info(f"Game started in room {room.room_id}.")
        return room

    async def _game_loop(self, room: GameRoom):
        try:
            while room.winner is None:
                await self._run_phase_logic(room)
                if self._check_and_handle_win_condition(room):
                    break
                await self._advance_to_next_phase(room)
            await self._handle_game_over(room)
        except asyncio.CancelledError:
            logger.info(f"Game loop for room {room.room_id} was cancelled.")
            await self._delete_room(room.room_id)
        except Exception as e:
            logger.error(f"Error in game loop for room {room.room_id}: {e}", exc_info=True)

    async def _run_phase_logic(self, room: GameRoom):
        phase = room.phase
        logger.info(f"Room {room.room_id}: Starting phase {phase} (Day {room.day_number})")
        duration = PHASE_DURATIONS.get(phase)
        if not duration:
            logger.warning(f"No duration set for phase {phase}, game might hang.")
            return

        room.phase_event = asyncio.Event()
        try:
            await asyncio.wait_for(room.phase_event.wait(), timeout=duration)
            logger.info(f"Room {room.room_id}: Phase {phase} completed early.")
        except asyncio.TimeoutError:
            logger.info(f"Room {room.room_id}: Phase {phase} timed out.")
        finally:
            room.phase_event = None
            if phase == GamePhase.JOKE_VOTING: await self._process_joke_vote_results(room)
            elif phase == GamePhase.VOTING: await self._process_lynch_vote_results(room)
            elif phase == GamePhase.NIGHT: await self._process_night_results(room)
            
            if phase in [GamePhase.JOKE_VOTING, GamePhase.VOTING, GamePhase.NIGHT]:
                await self._notifier.notify_room_update(room)
                await asyncio.sleep(RESULTS_DISPLAY_PAUSE)

    async def _advance_to_next_phase(self, room: GameRoom):
        async with room.lock:
            current_phase = room.phase
            if not current_phase or room.winner: return

            next_phase = PHASE_TRANSITIONS.get(current_phase)
            if not next_phase: raise ValueError(f"No transition from phase: {current_phase}")
            
            duration = PHASE_DURATIONS.get(next_phase)
            if duration:
                room.phase_start_time = time.time()
                room.phase_duration = duration
            else:
                room.phase_start_time = None
                room.phase_duration = None
            room.last_events.clear()
            
            if next_phase == GamePhase.DAY: room.day_number += 1
            if next_phase == GamePhase.NIGHT: room.night_actions = NightActions(); room.lynch_votes.clear()
            elif next_phase in [GamePhase.INTRODUCTION_DAY, GamePhase.DAY]: room.ready_votes.clear()
            elif next_phase == GamePhase.JOKE_VOTING:
                room.ready_votes.clear(); room.joke_votes.clear()
            
            room.phase = next_phase
            await self._notifier.notify_room_update(room)

    async def process_action(self, room_id: str, client_id: str, action: PlayerActionRequest):
        room = self.get_room(room_id)
        async with room.lock:
            player = next((p for p in room.players if p.client_id == client_id), None)
            if not player or not player.is_alive: raise HTTPException(status_code=403, detail="Действие недоступно")
        
            action_handlers = {
                (GamePhase.INTRODUCTION_NIGHT, ActionType.INTRODUCE): lambda: setattr(player, 'description', self._sanitize_for_llm(action.payload.get("description", ""))),
                (GamePhase.INTRODUCTION_DAY, ActionType.READY_FOR_VOTE): lambda: room.ready_votes.update({player.client_id: True}),
                (GamePhase.DAY, ActionType.READY_FOR_VOTE): lambda: room.ready_votes.update({player.client_id: True}),
                (GamePhase.JOKE_VOTING, ActionType.VOTE): lambda: self._handle_vote(room, player, action.payload, room.joke_votes),
                (GamePhase.VOTING, ActionType.VOTE): lambda: self._handle_vote(room, player, action.payload, room.lynch_votes),
                (GamePhase.NIGHT, ActionType.MAFIA_KILL): lambda: self._handle_night_action(room, player, action),
                (GamePhase.NIGHT, ActionType.DOCTOR_HEAL): lambda: self._handle_night_action(room, player, action),
                (GamePhase.NIGHT, ActionType.COMMISSAR_CHECK): lambda: self._handle_night_action(room, player, action),
                (GamePhase.NIGHT, ActionType.WHORE_BLOCK): lambda: self._handle_night_action(room, player, action),
            }
            handler = action_handlers.get((room.phase, action.action_type))

            if handler: handler()
            else: raise HTTPException(status_code=400, detail="Неверное действие для текущей фазы")
            
            self._check_phase_completion(room)
            await self._notifier.notify_room_update(room)
            
    def _handle_vote(self, room: GameRoom, player: Player, payload: dict, vote_dict: Dict[str, str]):
        target_name = payload.get("target_name")
        target_player = next((p for p in room.players if p.name == target_name and p.is_alive), None)
        if not target_player: raise HTTPException(status_code=404, detail="Игрок не найден")
        vote_dict[player.client_id] = target_player.client_id

    def _handle_night_action(self, room: GameRoom, player: Player, action: PlayerActionRequest):
        target_name = action.payload.get("target_name")
        target_player = next((p for p in room.players if p.name == target_name and p.is_alive), None)
        if not target_player: raise HTTPException(status_code=404, detail=f"Игрок с именем '{target_name}' не найден")
        if player.role != PlayerRole.DOCTOR and player.client_id == target_player.client_id: raise HTTPException(status_code=400, detail="Вы не можете выбрать себя")
        
        votes_attr_map = {
            (ActionType.MAFIA_KILL, PlayerRole.MAFIA): room.night_actions.mafia_kill_votes,
            (ActionType.DOCTOR_HEAL, PlayerRole.DOCTOR): room.night_actions.doctor_heal_votes,
            (ActionType.COMMISSAR_CHECK, PlayerRole.COMMISSAR): room.night_actions.commissar_check_votes,
            (ActionType.WHORE_BLOCK, PlayerRole.WHORE): room.night_actions.whore_block_votes,
        }
        vote_dict = votes_attr_map.get((action.action_type, player.role))
        if vote_dict is None: raise HTTPException(status_code=403, detail="Неверное действие для вашей роли")
        self._handle_vote(room, player, action.payload, vote_dict)
        
    def _check_phase_completion(self, room: GameRoom):
        if not room.phase_event or room.phase_event.is_set(): return
        alive_players_count = sum(1 for p in room.players if p.is_alive)
        
        completion_conditions = {
            GamePhase.INTRODUCTION_NIGHT: lambda r: all(p.description is not None for p in r.players if p.is_alive),
            GamePhase.INTRODUCTION_DAY: lambda r: len(r.ready_votes) == alive_players_count,
            GamePhase.DAY: lambda r: len(r.ready_votes) == alive_players_count,
            GamePhase.JOKE_VOTING: lambda r: len(r.joke_votes) == alive_players_count,
            GamePhase.VOTING: lambda r: len(r.lynch_votes) == alive_players_count,
            GamePhase.NIGHT: self._check_night_completion,
        }
        check_func = completion_conditions.get(room.phase)
        if check_func and check_func(room):
            room.phase_event.set()

    def _check_night_completion(self, room: GameRoom) -> bool:
        alive_players = [p for p in room.players if p.is_alive]
        active_roles_in_game = {p.role for p in alive_players if p.role in ACTIVE_NIGHT_ROLES}
        if not active_roles_in_game: return True
        votes_map = {
            PlayerRole.MAFIA: room.night_actions.mafia_kill_votes,
            PlayerRole.DOCTOR: room.night_actions.doctor_heal_votes,
            PlayerRole.COMMISSAR: room.night_actions.commissar_check_votes,
            PlayerRole.WHORE: room.night_actions.whore_block_votes,
        }
        for role in active_roles_in_game:
            team_members = [p for p in alive_players if p.role == role]
            team_size = len(team_members)
            if team_size == 0: continue
            votes_for_team = votes_map.get(role)
            if not votes_for_team: return False
            if len(votes_for_team) == team_size: continue
            vote_counts = Counter(votes_for_team.values())
            most_common_vote = vote_counts.most_common(1)
            if most_common_vote and most_common_vote[0][1] > team_size / 2: continue
            return False
        return True

    async def _process_joke_vote_results(self, room: GameRoom):
        vote_counts = Counter(room.joke_votes.values())
        if not vote_counts:
            result_text = "Голосование завершилось, но никто не отдал свой голос."
        else:
            top_two = vote_counts.most_common(2)
            if len(top_two) > 1 and top_two[0][1] == top_two[1][1]:
                result_text = "Голоса разделились. Никто не был признан самым подозрительным."
            else:
                winner_id = top_two[0][0]
                winner_player = next((p for p in room.players if p.client_id == winner_id), None)
                winner_name = winner_player.name if winner_player else "Никто"
                result_text = f"По итогам шуточного голосования, самым подозрительным посчитали игрока {self._sanitize_for_llm(winner_name)}!"
        event_data = {"type": "joke_vote_result", "text": result_text}
        room.last_events.append(event_data) 
        
    async def _process_lynch_vote_results(self, room: GameRoom):
        if not room.lynch_votes: result_text = "Голосование завершилось безрезультатно, никто не был казнен."
        else:
            vote_counts = Counter(room.lynch_votes.values())
            top_two = vote_counts.most_common(2)
            is_tie = len(top_two) > 1 and top_two[0][1] == top_two[1][1]
            if is_tie: result_text = "Голоса разделились. Сегодня никто не будет казнен."
            else:
                lynched_id = top_two[0][0]
                lynched_player = next((p for p in room.players if p.client_id == lynched_id), None)
                if lynched_player:
                    lynched_player.is_alive = False
                    result_text = f"По итогам голосования, игрок {self._sanitize_for_llm(lynched_player.name)} был казнен."
                else: result_text = "Произошла ошибка при голосовании."
        room.last_events.append({"type": "lynch_result", "text": result_text})

    async def _process_night_results(self, room: GameRoom):
        actions = room.night_actions
        whore_target_id = self._get_team_target(actions.whore_block_votes)
        blocked_players = [whore_target_id] if whore_target_id else []
        mafia_target_id = self._get_team_target(actions.mafia_kill_votes, ignored_voters=blocked_players)
        healed_target_id = self._get_team_target(actions.doctor_heal_votes, ignored_voters=blocked_players)
        commissar_target_id = self._get_team_target(actions.commissar_check_votes, ignored_voters=blocked_players)

        if commissar_target_id:
            commissars = [p for p in room.players if p.role == PlayerRole.COMMISSAR and p.is_alive]
            target_player = next((p for p in room.players if p.client_id == commissar_target_id), None)
            if commissars and target_player:
                is_mafia = "Мафия" if target_player.role == PlayerRole.MAFIA else "Не мафия"
                result_text = f"Результат вашей проверки: игрок {self._sanitize_for_llm(target_player.name)} - {is_mafia}."
                for commissar in commissars:
                    await self._notifier.send_personal_event(room.room_id, commissar.client_id, result_text)

        event_data = None
        if mafia_target_id and mafia_target_id != healed_target_id:
            killed_player = next((p for p in room.players if p.client_id == mafia_target_id), None)
            if killed_player:
                killed_player.is_alive = False
                event_data = {"type": "kill", "text": f"Этой ночью был убит игрок {self._sanitize_for_llm(killed_player.name)}.", "killed_player_name": killed_player.name}
        elif mafia_target_id and mafia_target_id == healed_target_id:
            healed_player = next((p for p in room.players if p.client_id == healed_target_id), None)
            healed_name = healed_player.name if healed_player else "цель"
            event_data = {"type": "save", "text": f"Мафия пыталась убить игрока {self._sanitize_for_llm(healed_name)}, но Доктор его спас."}
        else:
            event_data = {"type": "no_kill", "text": "Этой ночью в городе было тихо. Никто не был убит."}
        if event_data:
            room.last_events.append(event_data)

    def _check_and_handle_win_condition(self, room: GameRoom) -> bool:
        if room.winner: return True
        alive_players = [p for p in room.players if p.is_alive]
        mafia_count = sum(1 for p in alive_players if p.role == PlayerRole.MAFIA)
        citizen_team_count = len(alive_players) - mafia_count
        
        if mafia_count == 0:
            room.winner = Winner.citizens.name 
        elif mafia_count >= citizen_team_count:
            room.winner = Winner.mafia.name 
        return room.winner is not None
    
    def _get_team_target(self, votes: Dict[str, str], ignored_voters: List[str] = []) -> Optional[str]:
        valid_votes = {voter: target for voter, target in votes.items() if voter not in ignored_voters}
        if not valid_votes: return None
        vote_counts = Counter(valid_votes.values())
        top_two = vote_counts.most_common(2)
        if len(top_two) > 1 and top_two[0][1] == top_two[1][1]: return None
        return top_two[0][0]

    async def _handle_game_over(self, room: GameRoom):
        room.phase = GamePhase.GAME_OVER
        room.status = RoomStatus.FINISHED
        await self._notifier.notify_room_update(room)
        logger.info(f"Room {room.room_id}: GAME OVER. Winner: {room.winner}")
        asyncio.create_task(self._delete_room_after_delay(room.room_id, 60))
    
    async def _delete_room_after_delay(self, room_id: str, delay: int):
        await asyncio.sleep(delay)
        if room_id in self.active_rooms:
            logger.info(f"Deleting room {room_id} after delay.")
            await self._delete_room(room_id)

    def schedule_player_removal(self, room_id: str, client_id: str, delay: int = 10):
        asyncio.create_task(self._remove_player_after_delay(room_id, client_id, delay))

    async def _remove_player_after_delay(self, room_id: str, client_id: str, delay: int):
        await asyncio.sleep(delay)
        try:
            room = self.get_room(room_id)
            if self._notifier._connection_manager.is_client_connected(room_id, client_id): return

            async with room.lock:
                player_to_remove = next((p for p in room.players if p.client_id == client_id), None)
                if not player_to_remove: return
                if room.status == RoomStatus.IN_PROGRESS and player_to_remove.is_alive:
                    player_to_remove.is_alive = False
                    logger.info(f"Player {player_to_remove.name} disconnected and marked as dead.")
                    if self._check_and_handle_win_condition(room):
                        if room.game_loop_task and not room.game_loop_task.done(): room.game_loop_task.cancel()
                        await self._handle_game_over(room)
                    else:
                        self._check_phase_completion(room)
                elif room.status == RoomStatus.WAITING:
                    room.players = [p for p in room.players if p.client_id != client_id]
                    if not room.players: return await self._delete_room(room.room_id)
                    if room.host_id == client_id: room.host_id = room.players[0].client_id
                    logger.info(f"Player {player_to_remove.name} removed from lobby.")
                
                await self._notifier.notify_room_update(room)
        except (HTTPException, KeyError): pass

    async def _delete_room(self, room_id: str):
        if room_id in self.active_rooms:
            room = self.active_rooms.pop(room_id)
            if room.game_loop_task and not room.game_loop_task.done():
                room.game_loop_task.cancel()
            logger.info(f"Game room object {room_id} and its tasks have been deleted.")
            await self._notifier._connection_manager.close_and_remove_room_connections(room_id)

    def set_roles_settings(self, room_id: str, client_id: str, new_roles: Roles) -> GameRoom:
        room = self.get_room(room_id)
        if client_id != room.host_id: raise HTTPException(status_code=403, detail="Только хост может менять настройки")
        if room.status != RoomStatus.WAITING: raise HTTPException(status_code=400, detail="Нельзя менять настройки после начала игры")
        total_roles = sum(new_roles.model_dump().values())
        if len(room.players) != total_roles: raise HTTPException(status_code=400, detail=f"Количество ролей ({total_roles}) не совпадает с количеством игроков ({len(room.players)})")
        if len(room.players) > 0 and new_roles.mafia > 0 and len(room.players) / 3 < new_roles.mafia: raise HTTPException(status_code=400, detail="Мафии не может быть больше трети игроков")
        room.roles = new_roles
        return room

    def set_environ(self, room_id: str, client_id: str, environ: str) -> GameRoom:
        room = self.get_room(room_id)
        if client_id != room.host_id: raise HTTPException(status_code=403, detail="Только хост может менять настройки")
        if room.status != RoomStatus.WAITING: raise HTTPException(status_code=400, detail="Нельзя менять настройки после начала игры")
        if len(environ) > 300: raise HTTPException(status_code=400, detail=f"Длина описания не может превышать 300 символов (текущая: {len(environ)})")
        room.environ = environ
        return room
    
    async def process_websocket_message(self, room_id: str, client_id: str, data: Dict):
        message_type = data.get("type")
        payload = data.get("payload", {})
        if message_type == "team_select_target":
            await self._handle_team_activity(room_id, client_id, payload, is_confirmed=False)
        elif message_type == "team_confirm_target":
            await self._handle_team_activity(room_id, client_id, payload, is_confirmed=True)
        elif message_type == "send_emote":
            await self._handle_send_emote(room_id, client_id, payload)
        else:
            logger.warning(f"Unknown WebSocket message type received from {client_id}: {message_type}")

    async def _handle_team_activity(self, room_id: str, sender_client_id: str, payload: Dict, is_confirmed: bool):
        try:
            room = self.get_room(room_id)
            sender = next((p for p in room.players if p.client_id == sender_client_id), None)
            
            if not sender or not sender.is_alive or not sender.role or sender.role == PlayerRole.CITIZEN:
                return

            teammates = [
                p for p in room.players 
                if p.is_alive and p.role == sender.role and p.client_id != sender_client_id
            ]

            if not teammates:
                return

            message_payload = {
                "voter_name": sender.name,
                "target_name": payload.get("target_name"),
                "is_confirmed": is_confirmed,
            }
            for teammate in teammates:
                await self._notifier.send_team_activity_update(
                    room_id, teammate.client_id, message_payload
                )

        except HTTPException:
            pass

    async def _handle_send_emote(self, room_id: str, sender_client_id: str, payload: Dict):
        try:
            room = self.get_room(room_id)
            target_name = payload.get("target_name")
            sender_player = next((p for p in room.players if p.client_id == sender_client_id), None)
            target_player = next((p for p in room.players if p.name == target_name and p.is_alive), None)
            if not sender_player or not target_player or sender_player == target_player: return
            
            emote_payload = {"from_player": sender_player.name}

            await self._notifier.send_emote_notification(
                room.room_id, target_player.client_id, emote_payload
            )
        except HTTPException:
            pass