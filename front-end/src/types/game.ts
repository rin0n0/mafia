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
}

export interface GameRoomPublic {
  room_id: string;
  players: PlayerPublic[];
  status: "waiting" | "in_progress" | "finished";
  phase: string | null;
  day_number: number;
  roles: Roles;
  environ: string | null;
  last_events: GameEvent[];
}

export interface MyActionStatus {
  has_acted: boolean;
  mafia_kill_votes_by_name?: { [voterName: string]: string };
}

export interface EmotePayload {
  from_player: string;
}

export interface GameRoomPersonalizedResponse {
  room_details: GameRoomPublic;
  is_current_user_host: boolean;
  my_role: string | null;
  winner: "mafia" | "citizens" | null;
  my_action_status: MyActionStatus | null;
}

export interface Roles {
  mafia: number;
  citizen: number;
  doctor: number;
  comissar: number;
  whore: number;
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

export type WsMessagePayload =
  | GameRoomPublic
  | GameRoomPersonalizedResponse
  | JokeVotePayload
  | VoteResultsPayload
  | EmotePayload
  | PersonalEventPayload;

export interface WsMessage {
  type:
    | "public_state_update"
    | "personal_state_update"
    | "joke_vote_started"
    | "vote_results"
    | "receive_emote"
    | "personal_event";
  payload: WsMessagePayload;
}
