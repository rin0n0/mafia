export interface PlayerPublic {
  name: string;
  is_alive: boolean;
  is_host: boolean;
  has_acted: boolean;
}

export interface GameRoomPublic {
  room_id: string;
  players: PlayerPublic[];
  status: "waiting" | "in_progress" | "finished";
  phase: string | null;
  day_number: number;
  roles: Roles;
  environ: string | null;
}

export interface EmotePayload {
  from_player: string;
}

export interface GameRoomPersonalizedResponse {
  room_details: GameRoomPublic;
  is_current_user_host: boolean;
  my_role: string | null;
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

export interface WsMessage {
  type:
    | "public_state_update"
    | "personal_state_update"
    | "joke_vote_started"
    | "vote_results"
    | "receive_emote";
  payload:
    | GameRoomPublic
    | GameRoomPersonalizedResponse
    | JokeVotePayload
    | VoteResultsPayload
    | EmotePayload;
}
