import { defineStore } from "pinia";
import axios from "axios";
import { useUserStore } from "./userStore";
import router from "@/router";
import { useUiStore } from "./uiStore";
import { nextTick, ref, computed, type Ref } from "vue";

import type {
  GameRoomPublic,
  GameRoomPersonalizedResponse,
  Roles,
  PersonalEventPayload,
  EmotePayload,
  TeamActivity,
} from "@/types/game";

function updateFullState(
  room: Ref<GameRoomPublic | null>,
  isHost: Ref<boolean>,
  myRole: Ref<string | null>,
  teammates: Ref<string[]>,
  teamVotes: Ref<Map<string, string>>,
  error: Ref<string | null>,
  data: GameRoomPersonalizedResponse
) {
  room.value = data.room_details;
  isHost.value = data.is_current_user_host;
  myRole.value = data.my_role ?? null;
  teammates.value = data.teammates ?? [];
  teamVotes.value = new Map(Object.entries(data.team_votes ?? {}));
  error.value = null;
}

const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/ws";

interface GameStore {
  room: Ref<GameRoomPublic | null>;
  myRole: Ref<string | null>;
  isHost: Ref<boolean>;
  socket: Ref<WebSocket | null>;
  isConnected: Ref<boolean>;
  isLoading: Ref<boolean>;
  teamActivity: Ref<TeamActivity>;
  error: Ref<string | null>;
  teammates: Ref<string[]>;
  teamVotes: Ref<Map<string, string>>;
  specialAnnouncement: Ref<string | null>;

  playerCount: Ref<number>;
  myPlayer: Ref<any>;
  isNight: Ref<boolean>;
  isNightActionPhase: Ref<boolean>;
  isDayDiscussionPhase: Ref<boolean>;
  isVotingPhase: Ref<boolean>;
  isGameOver: Ref<boolean>;
  myPlayerHasActed: Ref<boolean>;
  getVotersForPlayer: (playerName: string) => string[];

  clearError: () => void;
  clearSpecialAnnouncement: () => void;
  createRoom: () => Promise<void>;
  joinRoom: (roomId: string) => Promise<void>;
  fetchRoomDetails: (roomId: string) => Promise<void>;
  setRoles: (newRoles: Roles) => Promise<void>;
  setEnvironment: (newEnviron: string | null) => Promise<void>;
  startGame: () => Promise<void>;
  performAction: (action_type: string, payload: object) => Promise<void>;
  sendEmote: (targetName: string) => void;
  selectTeamTarget: (targetName: string | null) => void;
  confirmTeamTarget: (targetName: string) => void;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  leaveRoom: () => void;
  confirmReadResults: () => Promise<void>;
  setApiKey: (apiKey: string) => Promise<void>;
}

export const useGameStore = defineStore("game", (): GameStore => {
  const room = ref<GameRoomPublic | null>(null);
  const myRole = ref<string | null>(null);
  const isHost = ref(false);
  const socket = ref<WebSocket | null>(null);
  const isConnected = ref(false);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const teamActivity = ref<TeamActivity>({});
  const teammates = ref<string[]>([]);
  const teamVotes = ref<Map<string, string>>(new Map());
  const specialAnnouncement = ref<string | null>(null);

  const userStore = useUserStore();

  const playerCount = computed(() => room.value?.players.length || 0);

  const myPlayer = computed(() => {
    if (!room.value || !userStore.playerName) return null;
    return room.value.players.find((p) => p.name === userStore.playerName);
  });

  const isNight = computed(() => room.value?.phase?.includes("night") ?? false);
  const isNightActionPhase = computed(() => room.value?.phase === "night");
  const isDayDiscussionPhase = computed(() =>
    room.value
      ? room.value.phase === "day" || room.value.phase === "introduction_day"
      : false
  );
  const isVotingPhase = computed(() =>
    room.value
      ? room.value.phase === "voting" || room.value.phase === "joke_voting"
      : false
  );
  const isGameOver = computed(() => room.value?.status === "finished");

  const myPlayerHasActed = computed(() => {
    if (!myPlayer.value?.is_alive) return true;
    return myPlayer.value?.has_acted ?? false;
  });

  const getVotersForPlayer = (playerName: string): string[] => {
    const voters: string[] = [];
    if (teamVotes.value.size === 0) return voters;

    for (const [voter, target] of teamVotes.value.entries()) {
      if (target === playerName) {
        voters.push(voter);
      }
    }
    return voters;
  };

  const clearError = () => {
    error.value = null;
  };

  const clearSpecialAnnouncement = () => {
    specialAnnouncement.value = null;
  };

  const updateState = (data: GameRoomPersonalizedResponse) => {
    updateFullState(room, isHost, myRole, teammates, teamVotes, error, data);
  };

  async function createRoom() {
    if (!userStore.playerName || !userStore.clientId) {
      error.value = "Необходимо ввести имя.";
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      const response = await axios.post<GameRoomPersonalizedResponse>(
        `${API_BASE}/rooms`,
        {
          host_name: userStore.playerName,
          host_client_id: userStore.clientId,
        }
      );
      updateState(response.data);
      await nextTick();
      router.push(`/room/${room.value!.room_id}`);
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Ошибка при создании комнаты";
      console.error(error.value);
    } finally {
      isLoading.value = false;
    }
  }

  async function joinRoom(roomId: string) {
    if (!userStore.playerName || !userStore.clientId) {
      error.value = "Необходимо ввести имя.";
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      const response = await axios.post<GameRoomPersonalizedResponse>(
        `${API_BASE}/rooms/${roomId}/join`,
        {
          player_name: userStore.playerName,
          player_client_id: userStore.clientId,
        }
      );
      updateState(response.data);
      await nextTick();
      router.push(`/room/${room.value!.room_id}`);
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Ошибка при входе в комнату";
      console.error(error.value);
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchRoomDetails(roomId: string) {
    if (!userStore.clientId) {
      router.push({ name: "lobby", query: { room: roomId } });
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      const response = await axios.get<GameRoomPersonalizedResponse>(
        `${API_BASE}/rooms/${roomId}`,
        {
          headers: {
            "X-Client-ID": userStore.clientId,
          },
        }
      );
      updateState(response.data);
    } catch (err: any) {
      error.value =
        "Вы не являетесь участником этой комнаты. Войдите, чтобы присоединиться.";
      console.error(
        "Failed to fetch room details:",
        err.response?.data?.detail || err.message
      );
      router.push({ name: "lobby", query: { room: roomId } });
    } finally {
      isLoading.value = false;
    }
  }

  async function setRoles(newRoles: Roles) {
    if (!isHost.value || !room.value || !userStore.clientId) return;

    isLoading.value = true;
    error.value = null;

    try {
      await axios.put(
        `${API_BASE}/rooms/${room.value.room_id}/roles`,
        { roles: newRoles },
        { headers: { "X-Client-ID": userStore.clientId } }
      );
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Ошибка при смене ролей";
      console.error(error.value);
    } finally {
      isLoading.value = false;
    }
  }

  async function setEnvironment(newEnviron: string | null) {
    if (!isHost.value || !room.value || !userStore.clientId) return;

    isLoading.value = true;
    error.value = null;

    try {
      await axios.put(
        `${API_BASE}/rooms/${room.value.room_id}/environ`,
        { environ: newEnviron },
        { headers: { "X-Client-ID": userStore.clientId } }
      );
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Ошибка при смене сеттинга";
      console.error(error.value);
    } finally {
      isLoading.value = false;
    }
  }

  async function startGame() {
    if (!isHost.value || !room.value || !userStore.clientId) return;

    isLoading.value = true;
    error.value = null;

    try {
      const response = await axios.post<GameRoomPersonalizedResponse>(
        `${API_BASE}/rooms/${room.value.room_id}/start`,
        {},
        {
          headers: { "X-Client-ID": userStore.clientId },
        }
      );
      console.log(
        "[DEBUG] startGame: Received HTTP response. Data:",
        JSON.parse(JSON.stringify(response.data))
      );
      updateState(response.data);
      console.log(
        "[DEBUG] startGame: State updated. Current active_narration:",
        JSON.parse(JSON.stringify(room.value?.active_narration))
      );
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Ошибка при старте игры";
      console.error(error.value);
    } finally {
      isLoading.value = false;
    }
  }

  async function performAction(action_type: string, payload: object) {
    if (!room.value || !userStore.clientId) return;
    isLoading.value = true;
    try {
      await axios.post(
        `${API_BASE}/rooms/${room.value.room_id}/act`,
        { action_type, payload },
        { headers: { "X-Client-ID": userStore.clientId } }
      );
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Ошибка действия";
    } finally {
      isLoading.value = false;
    }
  }

  function sendEmote(targetName: string) {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      const message = {
        type: "send_emote",
        payload: { target_name: targetName },
      };
      socket.value.send(JSON.stringify(message));
    } else {
      console.error("WebSocket is not connected. Cannot send emote.");
    }
  }

  async function setApiKey(apiKey: string) {
    const userStore = useUserStore();
    if (!isHost.value || !room.value || !userStore.clientId) return;

    isLoading.value = true;
    try {
      await axios.put(
        `${API_BASE}/rooms/${room.value.room_id}/key`,
        { api_key: apiKey },
        { headers: { "X-Client-ID": userStore.clientId } }
      );
      const uiStore = useUiStore();
      uiStore.addNotification("API ключ установлен!");
    } catch (err: any) {
      console.error("Ошибка установки ключа:", err);
      const uiStore = useUiStore();
      uiStore.addNotification(
        "Ошибка: " +
          (err.response?.data?.detail || "Не удалось установить ключ")
      );
    } finally {
      isLoading.value = false;
    }
  }

  function selectTeamTarget(targetName: string | null) {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      const message = {
        type: "team_select_target",
        payload: { target_name: targetName },
      };
      socket.value.send(JSON.stringify(message));
    }
  }

  function confirmTeamTarget(targetName: string) {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      const message = {
        type: "team_confirm_target",
        payload: { target_name: targetName },
      };
      socket.value.send(JSON.stringify(message));
    }
  }

  async function confirmReadResults() {
    if (!room.value || !userStore.clientId) return;
    try {
      await axios.post(
        `${API_BASE}/rooms/${room.value.room_id}/act`,
        { action_type: "confirm_read", payload: {} },
        { headers: { "X-Client-ID": userStore.clientId } }
      );
    } catch (err: any) {
      console.error("Ошибка подтверждения чтения:", err);
    }
  }

  function disconnectWebSocket() {
    if (socket.value) {
      socket.value.onclose = null;
      socket.value.close();
      socket.value = null;
    }
    isConnected.value = false;
  }

  function connectWebSocket() {
    const uiStore = useUiStore();
    if (!room.value || !userStore.clientId) {
      console.error(
        "Невозможно подключиться к WS: нет данных о комнате или пользователе."
      );
      return;
    }

    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      console.log("WebSocket уже подключен.");
      return;
    }

    disconnectWebSocket();
    const wsUrl = `${WS_BASE}/${room.value.room_id}/${userStore.clientId}`;
    socket.value = new WebSocket(wsUrl);

    socket.value.onopen = () => {
      console.log("WebSocket Connected");
      isConnected.value = true;
    };

    socket.value.onmessage = (event) => {
      let message = JSON.parse(event.data);
      console.log(
        `[DEBUG] WebSocket: Received message of type "${message.type}". Payload:`,
        JSON.parse(JSON.stringify(message.payload))
      );
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
          const payload = message.payload as GameRoomPersonalizedResponse;
          if (room.value?.phase !== payload.room_details.phase) {
            teamActivity.value = {};
          }

          updateState(payload);
          break;
        }
        case "public_state_update": {
          const publicState = message.payload as GameRoomPublic;
          if (room.value?.phase !== publicState.phase) {
            teamActivity.value = {};
            teamVotes.value.clear();
          }

          room.value = publicState;
          break;
        }

        case "personal_event": {
          specialAnnouncement.value = (
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
        case "team_activity_update": {
          const { voter_name, target_name, is_confirmed } = message.payload;
          Object.keys(teamActivity.value).forEach((target) => {
            teamActivity.value[target] =
              teamActivity.value[target]?.filter(
                (v) => v.voterName !== voter_name
              ) || [];
          });
          if (target_name) {
            if (!teamActivity.value[target_name]) {
              teamActivity.value[target_name] = [];
            }
            teamActivity.value[target_name].push({
              voterName: voter_name,
              isConfirmed: is_confirmed,
            });
          }
          break;
        }
      }
    };

    socket.value.onclose = (event) => {
      console.log("WebSocket Disconnected", event.reason);
      isConnected.value = false;
    };

    socket.value.onerror = (error) => {
      console.error("WebSocket Error:", error);
      isConnected.value = false;
    };
  }

  function leaveRoom() {
    disconnectWebSocket();
    room.value = null;
    isHost.value = false;
    error.value = null;
    router.push("/");
  }

  return {
    room,
    myRole,
    isHost,
    socket,
    isConnected,
    isLoading,
    teamActivity,
    error,
    teammates,
    teamVotes,
    specialAnnouncement,

    playerCount,
    myPlayer,
    isNight,
    isNightActionPhase,
    isDayDiscussionPhase,
    isVotingPhase,
    isGameOver,
    myPlayerHasActed,
    getVotersForPlayer,

    clearError,
    clearSpecialAnnouncement,
    createRoom,
    joinRoom,
    fetchRoomDetails,
    setRoles,
    setEnvironment,
    startGame,
    performAction,
    sendEmote,
    selectTeamTarget,
    confirmTeamTarget,
    connectWebSocket,
    disconnectWebSocket,
    leaveRoom,
    confirmReadResults,
    setApiKey,
  };
});
