import { defineStore } from "pinia";
import axios from "axios";
import { useUserStore } from "./userStore";
import type { GameRoom } from "@/types/game";
import router from "@/router";

const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/ws";
interface GameState {
  room: GameRoom | null;
  socket: WebSocket | null;
  isConnected: boolean;
  error: string | null;
}

export const useGameStore = defineStore("game", {
  state: (): GameState => ({
    room: null,
    socket: null,
    isConnected: false,
    error: null,
  }),

  actions: {
    async createRoom() {
      const userStore = useUserStore();
      if (!userStore.playerName || !userStore.clientId) {
        this.error = "Необходимо ввести имя.";
        return;
      }

      this.error = null;

      try {
        const response = await axios.post<GameRoom>(`${API_BASE}/rooms`, {
          host_name: userStore.playerName,
          host_client_id: userStore.clientId,
        });
        this.room = response.data;
        router.push(`/room/${this.room.room_id}`);
      } catch (err: any) {
        this.error =
          err.response?.data?.detail || "Ошибка при создании комнаты";
        console.error(this.error);
      }
    },

    async joinRoom(roomId: string) {
      const userStore = useUserStore();
      if (!userStore.playerName || !userStore.clientId) {
        this.error = "Необходимо ввести имя.";
        return;
      }

      this.error = null;

      try {
        const response = await axios.post<GameRoom>(
          `${API_BASE}/rooms/${roomId}/join`,
          {
            player_name: userStore.playerName,
            player_client_id: userStore.clientId,
          }
        );
        this.room = response.data;
        router.push(`/room/${this.room.room_id}`);
      } catch (err: any) {
        this.error = err.response?.data?.detail || "Ошибка при входе в комнату";
        console.error(this.error);
        alert(this.error);
      }
    },

    connectWebSocket() {
      const userStore = useUserStore();
      if (!this.room || !userStore.clientId) {
        console.error(
          "Невозможно подключиться к WS: нет данных о комнате или пользователе."
        );
        return;
      }

      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        return;
      }

      const wsUrl = `${WS_BASE}/${this.room.room_id}/${userStore.clientId}`;
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log("WebSocket Connected");
        this.isConnected = true;
      };

      this.socket.onmessage = (event) => {
        const updatedRoom: GameRoom = JSON.parse(event.data);
        this.room = updatedRoom;
      };

      this.socket.onclose = (event) => {
        console.log("WebSocket Disconnected", event);
        this.isConnected = false;
      };

      this.socket.onerror = (error) => {
        console.error("WebSocket Error:", error);
        this.isConnected = false;
      };
    },

    disconnectWebSocket() {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      this.isConnected = false;
    },

    leaveRoom() {
      this.disconnectWebSocket();
      this.room = null;
      router.push("/");
    },
  },
});
