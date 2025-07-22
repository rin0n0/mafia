export interface PlayerPublic {
  name: string;
  is_alive: boolean;
  is_host: boolean; 
}

export interface GameRoomPublic {
  room_id: string;
  players: PlayerPublic[];
  status: 'waiting' | 'in_progress' | 'finished'; 
  roles: Roles;          
  environ: string | null;  
}

export interface GameRoomPersonalizedResponse {
  room_details: GameRoomPublic;
  is_current_user_host: boolean;
}

export interface Roles {
  mafia: number;
  citizen: number;
  doctor: number;
  comissar: number;
  whore: number;
} 
