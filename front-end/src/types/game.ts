export interface Player {
  client_id: string;
  name: string;
  is_host: boolean;
  is_alive: boolean;
  role: string | null;
}

export interface GameRoom {
  room_id: string;
  players: Player[];
  status: "waiting" | "in_progressing" | "finished";
  host: Player;
}
