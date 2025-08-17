<template>
  <div class="room-view" :style="backgroundStyle">
    <PhaseAnnouncer :show="showAnnouncer" :title="announcerTitle" :subtitle="announcerSubtitle"
      :is-role="isRoleAnnouncement" @close="showAnnouncer = false" />
    <div v-if="gameStore.room" class="room-content" :class="{ 'in-game': gameStore.room.status === 'in_progress' }">

      <div class="header">
        <router-link to="/" @click="gameStore.leaveRoom" class="back-btn" title="Покинуть комнату">
          <span class="back-btn-arrow">←</span>
          <span class="back-btn-text">Назад в лобби</span>
        </router-link>

        <div class="room-title-wrapper">
          <div v-if="gameStore.room.status === 'waiting'">
            <h1 @click="copyRoomId" title="Нажмите, чтобы скопировать ID">
              Комната #{{ gameStore.room.room_id }}
              <svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-5zm0 16H8V7h11v14z">
                </path>
              </svg>
            </h1>
            <transition name="fade-fast">
              <span v-if="isCopied" class="copy-feedback">Код скопирован!</span>
            </transition>
          </div>
          <h1 v-else>
            Комната #{{ gameStore.room.room_id }}
          </h1>
        </div>

      </div>

      <LobbyLayout v-if="gameStore.room.status === 'waiting'" :players="gameStore.room.players"
        :roles="gameStore.room.roles" :initial-environment="gameStore.room.environ" :is-host="gameStore.isHost"
        :player-count="gameStore.playerCount" :is-loading="gameStore.isLoading" @update-roles="handleUpdateRoles"
        @update-environment="handleUpdateEnvironment" />
      <GameLayout v-else-if="gameStore.room.status === 'in_progress'" :selected-player-name="selectedPlayerName"
        @player-select="handlePlayerSelect" />

      <div class="actions">
        <button v-if="gameStore.room.status === 'waiting'" @click="startGame" class="btn start-game-btn"
          :disabled="!gameStore.isHost || !canStartGame">
          {{ startGameButtonText }}
        </button>

        <button v-if="isDiscussionPhase" @click="readyForVote" :disabled="gameStore.myPlayerHasActed" class="btn">
          {{ gameStore.myPlayerHasActed ? 'Ожидаем других...' : 'Перейти к голосованию' }}
        </button>

        <button v-if="isVotingPhase" @click="submitVote" :disabled="!selectedPlayerName || gameStore.myPlayerHasActed"
          class="btn">
          {{ voteButtonText }}
        </button>
      </div>

    </div>

    <div v-else-if="gameStore.isLoading" class="state-panel">
      <p>Загрузка комнаты...</p>
    </div>
    <div v-else class="state-panel">
      <p>Комната не найдена или произошла ошибка.</p>
      <router-link to="/" class="btn">Вернуться в лобби</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useGameStore } from '@/stores/gameStore';
import type { Roles } from '@/types/game';

import LobbyLayout from './wait/LobbyLayout.vue';
import GameLayout from './game/GameLayout.vue';
import PhaseAnnouncer from './game/PhaseAnnouncer.vue';

const gameStore = useGameStore();
const route = useRoute();
const showAnnouncer = ref(false);
const announcerTitle = ref('');
const announcerSubtitle = ref('');
const isRoleAnnouncement = ref(false);
const isCopied = ref(false);
const selectedPlayerName = ref<string | null>(null);
/* eslint-disable */
const bgLight = require('@/assets/background_light.png');
/* eslint-disable */
const bgDark = require('@/assets/background_dark.png');
const roleMap: Record<string, string> = {
  mafia: "Мафия",
  citizen: "Мирный житель",
  doctor: "Доктор",
  comissar: "Комиссар",
  whore: "Потаскуха"
};

const phaseMap: Record<string, string> = {
  introduction_night: "Ночь знакомств",
  introduction_day: "Первый день",
  night: "Ночь",
  day: "День",
};

const backgroundStyle = computed(() => {
  const isNight = gameStore.room?.phase?.includes('night');
  const imageUrl = isNight ? bgDark : bgLight;
  return {
    backgroundImage: `url(${imageUrl})`
  };
});

watch(() => gameStore.room?.status, (newStatus, oldStatus) => {
  if (oldStatus === 'waiting' && newStatus === 'in_progress') {
    announcerTitle.value = 'Ваша роль';
    const role = gameStore.myRole;
    announcerSubtitle.value = role ? (roleMap[role] || role) : '';
    isRoleAnnouncement.value = true;
    showAnnouncer.value = true;
  }
});

watch(() => gameStore.room?.phase, (newPhase) => {
  if (newPhase && phaseMap[newPhase]) {
    announcerTitle.value = phaseMap[newPhase];
    announcerSubtitle.value = '';
    isRoleAnnouncement.value = false;
    showAnnouncer.value = true;
    setTimeout(() => {
      if (!isRoleAnnouncement.value) showAnnouncer.value = false;
    }, 3500);
  }
});

const copyRoomId = async () => {
  if (!gameStore.room?.room_id || isCopied.value) return;
  try {
    await navigator.clipboard.writeText(gameStore.room.room_id);
    isCopied.value = true;
    setTimeout(() => {
      isCopied.value = false;
    }, 2000);
  } catch (err) {
    console.error('Не удалось скопировать ID комнаты:', err);
  }
};

const handlePlayerSelect = (playerName: string) => {
  if (selectedPlayerName.value === playerName) {
    selectedPlayerName.value = null;
  } else {
    selectedPlayerName.value = playerName;
  }
};

const isResultsPhase = computed(() => !!gameStore.lastVoteResults);

const isDiscussionPhase = computed(() =>
  gameStore.room?.phase === 'introduction_day' &&
  !gameStore.currentVoteQuestion &&
  !isResultsPhase.value
);

const isVotingPhase = computed(() =>
  gameStore.room?.phase === 'introduction_day' &&
  !!gameStore.currentVoteQuestion &&
  !isResultsPhase.value
);
const voteButtonText = computed(() => {
  if (gameStore.myPlayerHasActed) return 'Ожидаем других...';
  if (selectedPlayerName.value) return `Голосовать за "${selectedPlayerName.value}"`;
  return 'Выберите игрока для голосования';
});

const readyForVote = () => {
  gameStore.performAction('ready_for_vote', {});
};
const submitVote = () => {
  if (!selectedPlayerName.value) return;
  gameStore.performAction('vote', { target_name: selectedPlayerName.value });
};

onMounted(async () => {
  const roomId = route.params.id as string;
  if (!gameStore.room || gameStore.room.room_id !== roomId) {
    await gameStore.fetchRoomDetails(roomId);
  }
  if (gameStore.room?.room_id === roomId) {
    gameStore.connectWebSocket();
  }
});

onUnmounted(() => {
  gameStore.disconnectWebSocket();
});

const handleUpdateRoles = (newRoles: Roles) => {
  gameStore.setRoles(newRoles);
};

const handleUpdateEnvironment = (newEnvironment: string | null) => {
  gameStore.setEnvironment(newEnvironment);
};

const canStartGame = computed(() => {
  if (!gameStore.room) return false;
  const totalRoles = Object.values(gameStore.room.roles).reduce((sum, count) => sum + count, 0);
  return gameStore.room.players.length === totalRoles && totalRoles > 0;
});

const startGameButtonText = computed(() => {
  if (!canStartGame.value) {
    return 'Распределите роли';
  }
  return 'Начать игру';
});

const startGame = () => {
  if (gameStore.isHost && canStartGame.value) {
    gameStore.startGame();
  }
};
</script>

<style scoped>
.room-view {
  background-image: url('@/assets/background_light.png');
  background-size: cover;
  background-position: center center;
  background-attachment: fixed;
  min-height: 100vh;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  transition: background-image 0.8s ease-in-out;
}

.room-content {
  width: 100%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transition: max-width 0.5s ease;
}

.header {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 100%;
}

.header h1 {
  margin: 0;
  font-size: 1.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.header h1:hover {
  background-color: rgba(0, 0, 0, 0.15);
  color: #fff;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--secondary-text-color);
  text-decoration: none;
  padding: 0.5rem 1rem;
  transition: all 0.2s ease;
}

.back-btn:hover {
  color: var(--primary-text-color);
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.back-btn-arrow {
  font-size: 1.5rem;
  line-height: 1;
}

.back-btn-text {
  display: none;
}

.actions {
  width: 100%;
}

.state-panel {
  text-align: center;
  padding-top: 40vh;
}

.room-title-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copy-icon {
  width: 1.1em;
  height: 1.1em;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.header h1:hover .copy-icon {
  opacity: 1;
}

.copy-feedback {
  position: absolute;
  top: 100%;
  margin-top: 8px;
  background: #1a1a1a;
  color: #fff;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 700;
  pointer-events: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.fade-fast-enter-from,
.fade-fast-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

.fade-fast-enter-active,
.fade-fast-leave-active {
  transition: all 0.3s ease;
}

@media (min-width: 992px) {
  .room-view {
    align-items: center;
  }

  .room-content {
    max-width: 1100px;
  }

  .room-content.in-game {
    max-width: 900px;
  }

  .back-btn-text {
    display: inline;
  }
}
</style>