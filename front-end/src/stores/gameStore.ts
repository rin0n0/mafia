import { defineStore } from "pinia";
import axios from "axios";
import { useUserStore } from "./userStore";
import router from "@/router";

import type { 
  GameRoomPublic, 
  GameRoomPersonalizedResponse 
} from "@/types/game";

const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/ws";

interface GameState {
  room: GameRoomPublic | null;
  isHost: boolean; 
  socket: WebSocket | null;
  isConnected: boolean;
  isLoading: boolean; 
  error: string | null;
}

export const useGameStore = defineStore("game", {
  state: (): GameState => ({
    room: null,
    isHost: false,
    socket: null,
    isConnected: false,
    isLoading: false,
    error: null,
  }),

  actions: {
    _handleSuccessfulJoin(response: GameRoomPersonalizedResponse) {
      this.room = response.room_details;
      this.isHost = response.is_current_user_host;
      this.error = null;
      router.push(`/room/${response.room_details.room_id}`);
    },

    async createRoom() {
      const userStore = useUserStore();
      if (!userStore.playerName || !userStore.clientId) {
        this.error = "Необходимо ввести имя.";
        return;
      }
      
      this.isLoading = true;
      this.error = null;

      try {
        const response = await axios.post<GameRoomPersonalizedResponse>(`${API_BASE}/rooms`, {
          host_name: userStore.playerName,
          host_client_id: userStore.clientId,
        });
        this._handleSuccessfulJoin(response.data);
      } catch (err: any) {
        this.error = err.response?.data?.detail || "Ошибка при создании комнаты";
        console.error(this.error);
      } finally {
        this.isLoading = false;
      }
    },

    async joinRoom(roomId: string) {
      const userStore = useUserStore();
      if (!userStore.playerName || !userStore.clientId) {
        this.error = "Необходимо ввести имя.";
        return;
      }

      this.isLoading = true;
      this.error = null;

      try {
        const response = await axios.post<GameRoomPersonalizedResponse>(
          `${API_BASE}/rooms/${roomId}/join`,
          {
            player_name: userStore.playerName,
            player_client_id: userStore.clientId,
          }
        );
        this._handleSuccessfulJoin(response.data);
      } catch (err: any) {
        this.error = err.response?.data?.detail || "Ошибка при входе в комнату";
        console.error(this.error);
        alert(this.error); 
      } finally {
        this.isLoading = false;
      }
    },


    async fetchRoomDetails(roomId: string) {
        const userStore = useUserStore();
        if (!userStore.clientId) return;

        this.isLoading = true;
        this.error = null;

        try {
            const response = await axios.get<GameRoomPersonalizedResponse>(`${API_BASE}/rooms/${roomId}`, {
                headers: {
                    'X-Client-ID': userStore.clientId
                }
            });
            this._handleSuccessfulJoin(response.data);
        } catch (err: any) {
            this.error = err.response?.data?.detail || "Не удалось загрузить данные комнаты";
            console.error(this.error);
            router.push('/');
        } finally {
            this.isLoading = false;
        }
    },

    connectWebSocket() {
      const userStore = useUserStore();
      if (!this.room || !userStore.clientId) {
        console.error("Невозможно подключиться к WS: нет данных о комнате или пользователе.");
        return;
      }

      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        console.log("WebSocket уже подключен.");
        return;
      }

      this.disconnectWebSocket();

      const wsUrl = `${WS_BASE}/${this.room.room_id}/${userStore.clientId}`;
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log("WebSocket Connected");
        this.isConnected = true;
      };

      this.socket.onmessage = (event) => {
        const updatedRoom: GameRoomPublic = JSON.parse(event.data);
        this.room = updatedRoom;
        console.log("Room state updated via WebSocket:", updatedRoom);
      };

      this.socket.onclose = (event) => {
        console.log("WebSocket Disconnected", event.reason);
        this.isConnected = false;
      };

      this.socket.onerror = (error) => {
        console.error("WebSocket Error:", error);
        this.isConnected = false;
      };
    },

    disconnectWebSocket() {
      if (this.socket) {
        this.socket.onclose = null; 
        this.socket.close();
        this.socket = null;
      }
      this.isConnected = false;
    },

    leaveRoom() {
      this.disconnectWebSocket();
      this.room = null;
      this.isHost = false;
      this.error = null;
      router.push("/");
    },
  },
});