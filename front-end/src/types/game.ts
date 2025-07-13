export interface PlayerPublic {
  name: string;
  is_alive: boolean;
  is_host: boolean; 
}

export interface GameRoomPublic {
  room_id: string;
  players: PlayerPublic[];
  status: 'waiting' | 'in_progress' | 'finished'; 
}

export interface GameRoomPersonalizedResponse {
  room_details: GameRoomPublic;
  is_current_user_host: boolean;
}