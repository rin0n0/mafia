import { defineStore } from "pinia";
import axios from "axios";
import { useUserStore } from "./userStore";
import router from "@/router";

import type {
  GameRoomPublic,
  GameRoomPersonalizedResponse,
  Roles,
  WsMessage,
  JokeVotePayload,
  VoteResultsPayload,
} from "@/types/game";

function updatePersonalState(
  store: GameState,
  data: GameRoomPersonalizedResponse
) {
  store.room = data.room_details;
  store.isHost = data.is_current_user_host;
  if (data.my_role !== undefined) {
    store.myRole = data.my_role;
  }
  store.error = null;
}

const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/ws";

interface GameState {
  room: GameRoomPublic | null;
  myRole: string | null;
  isHost: boolean;
  socket: WebSocket | null;
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  currentVoteQuestion: string | null;
  lastVoteResults: string | null;
}

export const useGameStore = defineStore("game", {
  state: (): GameState => ({
    room: null,
    myRole: null,
    isHost: false,
    socket: null,
    isConnected: false,
    isLoading: false,
    error: null,
    currentVoteQuestion: null,
    lastVoteResults: null,
  }),

  getters: {
    playerCount: (state) => {
      if (!state.room?.players) {
        return 0;
      }
      return state.room?.players.length;
    },

    myPlayerHasActed(state): boolean {
      const userStore = useUserStore();
      if (!state.room || !userStore.clientId) return false;
      const me = state.room.players.find(
        (p) => p.name === userStore.playerName
      );
      return me?.has_acted ?? false;
    },
  },

  actions: {
    async createRoom() {
      const userStore = useUserStore();
      if (!userStore.playerName || !userStore.clientId) {
        this.error = "Необходимо ввести имя.";
        return;
      }

      this.isLoading = true;
      this.error = null;

      try {
        const response = await axios.post<GameRoomPersonalizedResponse>(
          `${API_BASE}/rooms`,
          {
            host_name: userStore.playerName,
            host_client_id: userStore.clientId,
          }
        );
        updatePersonalState(this, response.data);
        router.push(`/room/${this.room!.room_id}`);
      } catch (err: any) {
        this.error =
          err.response?.data?.detail || "Ошибка при создании комнаты";
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
        updatePersonalState(this, response.data);
        router.push(`/room/${this.room!.room_id}`);
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
      if (!userStore.clientId) {
        router.push({ name: "lobby", query: { room: roomId } });
        return;
      }

      this.isLoading = true;
      this.error = null;

      try {
        const response = await axios.get<GameRoomPersonalizedResponse>(
          `${API_BASE}/rooms/${roomId}`,
          {
            headers: {
              "X-Client-ID": userStore.clientId,
            },
          }
        );
        updatePersonalState(this, response.data);
      } catch (err: any) {
        this.error =
          "Вы не являетесь участником этой комнаты. Войдите, чтобы присоединиться.";
        console.error(
          "Failed to fetch room details:",
          err.response?.data?.detail || err.message
        );
        router.push({ name: "lobby", query: { room: roomId } });
      } finally {
        this.isLoading = false;
      }
    },

    async setRoles(newRoles: Roles) {
      const userStore = useUserStore();
      if (!this.isHost || !this.room || !userStore.clientId) return;

      this.isLoading = true;
      this.error = null;

      try {
        await axios.put(
          `${API_BASE}/rooms/${this.room.room_id}/roles`,
          { roles: newRoles },
          { headers: { "X-Client-ID": userStore.clientId } }
        );
      } catch (err: any) {
        this.error = err.response?.data?.detail || "Ошибка при смене ролей";
        console.error(this.error);
        alert(this.error);
      } finally {
        this.isLoading = false;
      }
    },

    async setEnvironment(newEnviron: string | null) {
      const userStore = useUserStore();
      if (!this.isHost || !this.room || !userStore.clientId) return;

      this.isLoading = true;
      this.error = null;

      try {
        await axios.put(
          `${API_BASE}/rooms/${this.room.room_id}/environ`,
          { environ: newEnviron },
          { headers: { "X-Client-ID": userStore.clientId } }
        );
      } catch (err: any) {
        this.error = err.response?.data?.detail || "Ошибка при смене сеттинга";
        console.error(this.error);
        alert(this.error);
      } finally {
        this.isLoading = false;
      }
    },
    async startGame() {
      const userStore = useUserStore();
      if (!this.isHost || !this.room || !userStore.clientId) return;

      this.isLoading = true;
      this.error = null;

      try {
        await axios.post(
          `${API_BASE}/rooms/${this.room.room_id}/start`,
          {},
          {
            headers: {
              "X-Client-ID": userStore.clientId,
            },
          }
        );
      } catch (err: any) {
        this.error = err.response?.data?.detail || "Ошибка при старте игры";
        console.error(this.error);
        alert(this.error);
      } finally {
        this.isLoading = false;
      }
    },

    async performAction(action_type: string, payload: object) {
      const userStore = useUserStore();
      if (!this.room || !userStore.clientId) return;

      this.isLoading = true;
      try {
        await axios.post(
          `${API_BASE}/rooms/${this.room.room_id}/act`,
          { action_type, payload },
          { headers: { "X-Client-ID": userStore.clientId } }
        );
      } catch (err: any) {
        this.error = err.response?.data?.detail || "Ошибка действия";
        alert(this.error);
      } finally {
        this.isLoading = false;
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
        const message = JSON.parse(event.data);

        switch (message.type) {
          case "personal_state_update": {
            updatePersonalState(
              this,
              message.payload as GameRoomPersonalizedResponse
            );
            break;
          }
          case "public_state_update": {
            const oldPhase = this.room?.phase;

            const newRoomState = message.payload as GameRoomPublic;
            this.room = newRoomState;

            if (oldPhase !== newRoomState.phase) {
              console.log(
                `Phase changed from ${oldPhase} to ${newRoomState.phase}. Clearing context.`
              );
              this.currentVoteQuestion = null;
              this.lastVoteResults = null;
            }
            break;
          }
          case "joke_vote_started": {
            const payload = message.payload as JokeVotePayload;
            this.currentVoteQuestion = payload.question;
            this.lastVoteResults = null;
            break;
          }
          case "vote_results": {
            const payload = message.payload as VoteResultsPayload;
            this.lastVoteResults = payload.text;
            this.currentVoteQuestion = null;
            break;
          }
        }
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
