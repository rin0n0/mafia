import { defineStore } from "pinia";
import axios from "axios";
import { useUserStore } from "./userStore";
import router from "@/router";
import { useUiStore } from "./uiStore";

import type {
  GameRoomPublic,
  GameRoomPersonalizedResponse,
  Roles,
  WsMessage,
  PersonalEventPayload,
  EmotePayload,
  JokeVotePayload,
  VoteResultsPayload,
  GameEvent,
} from "@/types/game";

function updateFullState(store: GameState, data: GameRoomPersonalizedResponse) {
  store.room = data.room_details;
  store.isHost = data.is_current_user_host;
  store.myRole = data.my_role ?? null;
  store.winner = data.winner ?? store.winner;
  store.teammates = data.teammates ?? [];
  store.teamVotes = new Map(Object.entries(data.team_votes ?? {}));
  store.lastEvents = data.room_details.last_events ?? [];
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
  winner: "mafia" | "citizens" | null;
  teammates: string[];
  teamVotes: Map<string, string>;
  lastEvents: GameEvent[];
  specialAnnouncement: string | null;
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
    winner: null,
    teammates: [],
    teamVotes: new Map(),
    lastEvents: [],
    specialAnnouncement: null,
  }),

  getters: {
    playerCount: (state): number => state.room?.players.length || 0,
    myPlayer(state) {
      const userStore = useUserStore();
      if (!state.room || !userStore.playerName) return null;
      return state.room.players.find((p) => p.name === userStore.playerName);
    },
    isNight(state): boolean {
      return state.room?.phase?.includes("night") ?? false;
    },
    isNightActionPhase(state): boolean {
      return state.room?.phase === "night";
    },
    isDayDiscussionPhase(state): boolean {
      return state.room?.phase === "day";
    },
    isVotingPhase(state): boolean {
      return (
        state.room?.phase === "voting" ||
        (state.room?.phase === "introduction_day" &&
          !!state.currentVoteQuestion)
      );
    },
    isGameOver(state): boolean {
      return state.room?.status === "finished";
    },
    myPlayerHasActed(): boolean {
      if (!this.myPlayer?.is_alive) return true;
      return this.myPlayer?.has_acted ?? false;
    },
    getVotersForPlayer: (state) => {
      return (playerName: string): string[] => {
        const voters: string[] = [];
        if (state.teamVotes.size === 0) return voters;

        for (const [voter, target] of state.teamVotes.entries()) {
          if (target === playerName) {
            voters.push(voter);
          }
        }
        return voters;
      };
    },
  },

  actions: {
    clearError() {
      this.error = null;
    },
    clearSpecialAnnouncement() {
      this.specialAnnouncement = null;
    },
    clearResults() {
      this.lastEvents = [];
      this.lastVoteResults = null;
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
        const response = await axios.post<GameRoomPersonalizedResponse>(
          `${API_BASE}/rooms`,
          {
            host_name: userStore.playerName,
            host_client_id: userStore.clientId,
          }
        );
        updateFullState(this, response.data);
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
        updateFullState(this, response.data);
        router.push(`/room/${this.room!.room_id}`);
      } catch (err: any) {
        this.error = err.response?.data?.detail || "Ошибка при входе в комнату";
        console.error(this.error);
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
        updateFullState(this, response.data);
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
      } finally {
        this.isLoading = false;
      }
    },

    sendEmote(targetName: string) {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        const message = {
          type: "send_emote",
          payload: { target_name: targetName },
        };
        this.socket.send(JSON.stringify(message));
      } else {
        console.error("WebSocket is not connected. Cannot send emote.");
      }
    },

    connectWebSocket() {
      const userStore = useUserStore();
      const uiStore = useUiStore();
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
        let message = JSON.parse(event.data);
        if (typeof message === "string") {
          try {
            message = JSON.parse(message);
          } catch (e) {
            console.error("Failed to double-parse WebSocket message:", e);
            return;
          }
        }
        switch (message.type) {
          case "personal_state_update": {
            updateFullState(
              this,
              message.payload as GameRoomPersonalizedResponse
            );
            break;
          }
          case "public_state_update": {
            const oldPhase = this.room?.phase;
            const publicState = message.payload as GameRoomPublic;
            this.room = publicState;
            if (publicState.phase !== "night") {
              this.teamVotes.clear();
            }
            this.lastEvents = publicState.last_events ?? [];
            if (
              publicState.phase !== oldPhase &&
              (publicState.phase === "night" || oldPhase === "night")
            ) {
              this.teamVotes.clear();
            }
            if (publicState.phase !== "introduction_day") {
              this.currentVoteQuestion = null;
            }
            if (
              publicState.phase !== "voting" &&
              publicState.phase !== "introduction_day"
            ) {
              this.lastVoteResults = null;
            }
            break;
          }

          case "personal_event": {
            this.specialAnnouncement = (
              message.payload as PersonalEventPayload
            ).text;
            break;
          }
          case "receive_emote": {
            const payload = message.payload as EmotePayload;
            uiStore.addNotification(
              `Игрок ${payload.from_player} таинственно вам подмигивает...`
            );
            break;
          }
          case "joke_vote_started": {
            const payload = message.payload as JokeVotePayload;
            this.currentVoteQuestion = payload.question;
            this.lastVoteResults = null;
            break;
          }
          case "vote_results": {
            this.lastVoteResults = (message.payload as VoteResultsPayload).text;
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
