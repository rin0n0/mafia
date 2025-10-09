export interface PlayerPublic {
  name: string;
  is_alive: boolean;
  is_host: boolean;
  has_acted: boolean;
  role: string | null;
}

export interface GameEvent {
  type: string;
  text: string;
  killed_player_name?: string;
}

export interface GameRoomPublic {
  room_id: string;
  players: PlayerPublic[];
  status: "waiting" | "in_progress" | "finished";
  phase: string | null;
  day_number: number;
  winner: "mafia" | "citizens" | null;
  roles: Roles;
  environ: string | null;
  last_events: GameEvent[];
}

export interface EmotePayload {
  from_player: string;
}

export interface GameRoomPersonalizedResponse {
  room_details: GameRoomPublic;
  is_current_user_host: boolean;
  my_role: string | null;
  winner: "mafia" | "citizens" | null;
  teammates: string[];
  team_votes: { [voterName: string]: string };
}

export interface Roles {
  mafia: number;
  citizen: number;
  doctor: number;
  comissar: number;
  whore: number;
}

export interface TeamActivity {
  [targetName: string]: {
    voterName: string;
    isConfirmed: boolean;
  }[];
}

export interface JokeVotePayload {
  question: string;
}

export interface VoteResultsPayload {
  text: string;
}
export interface PersonalEventPayload {
  text: string;
}

export type GameEventPayload = GameEvent;

export type WsMessagePayload =
  | GameRoomPublic
  | GameRoomPersonalizedResponse
  | JokeVotePayload
  | EmotePayload
  | PersonalEventPayload
  | GameEventPayload;

export interface WsMessage {
  type:
    | "public_state_update"
    | "personal_state_update"
    | "joke_vote_started"
    | "receive_emote"
    | "personal_event"
    | "game_event";
  payload: WsMessagePayload;
}
