<template>
  <div class="room-view" :class="{ 'is-night': gameStore.isNight }">
    <PhaseAnnouncer :show="showAnnouncer" :title="announcerTitle" :subtitle="announcerSubtitle"
      :is-role="isRoleAnnouncement" :role="gameStore.myRole || undefined" @close="handleAnnouncerClose" />
    <ErrorDisplay :message="gameStore.error" @close="gameStore.clearError()" />
    <SpecialAnnouncement />
    <NotificationDisplay />
    <GameOverScreen v-if="gameStore.isGameOver" />
    <DayResultsPanel v-if="shouldShowResultsPanel" />

    <div v-else-if="gameStore.room" class="room-content"
      :class="{ 'in-game': gameStore.room.status === 'in_progress' }">
      <div class="header">
        <router-link to="/" @click="gameStore.leaveRoom" class="back-btn" title="Покинуть комнату">
          <span class="back-btn-arrow">←</span>
          <span class="back-btn-text">Назад в лобби</span>
        </router-link>
        <div v-if="gameStore.room.status === 'waiting'" class="room-title-wrapper">
          <div>
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
        </div>
        <div class="room-title-wrapper-game" v-if="gameStore.room.status === 'in_progress'">
          <h1>Комната #{{ gameStore.room.room_id }}</h1>
        </div>
      </div>

      <LobbyLayout v-if="gameStore.room.status === 'waiting'" :players="gameStore.room.players"
        :roles="gameStore.room.roles" :initial-environment="gameStore.room.environ" :is-host="gameStore.isHost"
        :player-count="gameStore.playerCount" :is-loading="gameStore.isLoading" @update-roles="handleUpdateRoles"
        @update-environment="handleUpdateEnvironment" />

      <IntroductionForm v-else-if="gameStore.room.phase === 'introduction_night' && !gameStore.myPlayerHasActed"
        @submit-description="submitDescription" />

      <GameLayout v-else-if="gameStore.room.status === 'in_progress'" :selected-player-name="selectedPlayerName"
        @player-select="handlePlayerSelect" />
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
import NotificationDisplay from '@/views/ui/NotificationDisplay.vue';
import LobbyLayout from './wait/LobbyLayout.vue';
import GameLayout from '@/views/game/GameLayout.vue';
import PhaseAnnouncer from '@/views/game/PhaseAnnouncer.vue';
import SpecialAnnouncement from '@/views/game/SpecialAnnouncement.vue';
import ErrorDisplay from '@/views/ui/ErrorDisplay.vue';
import GameOverScreen from '@/views/game/GameOverScreen.vue';
import IntroductionForm from '@/views/game/IntroductionForm.vue';
import DayResultsPanel from '@/views/game/DayResultsPanel.vue';

const gameStore = useGameStore();
const route = useRoute();
const showAnnouncer = ref(false);
const announcerTitle = ref('');
const announcerSubtitle = ref('');
const isRoleAnnouncement = ref(false);
const isCopied = ref(false);
const selectedPlayerName = ref<string | null>(null);

const roleMap: Record<string, string> = {
  mafia: "Мафия", citizen: "Мирный житель", doctor: "Доктор", comissar: "Комиссар", whore: "Потаскуха"
};
const phaseMap: Record<string, string> = {
  introduction_night: "Ночь знакомств", introduction_day: "Первый день", night: "Ночь", day: "День", voting: "Голосование"
};
const roleSubtitleMap: Record<string, string> = {
  mafia: "Ваша цель — истребить всех мирных жителей.",
  citizen: "Ваша цель — найти и казнить всю мафию.",
  doctor: "Каждую ночь вы можете кого-то одного от смерти. Помогайте мирным жителям.",
  comissar: "Каждую ночь вы можете проверить одного игрока. Истрибите мафию.",
  whore: "Каждую ночь вы можете лишить одного игрока голоса и действия. Помогайте мафии."
};

watch([() => gameStore.room?.status, () => gameStore.room?.phase], ([newStatus, newPhase], [oldStatus, oldPhase]) => {
  if (oldStatus === 'waiting' && newStatus === 'in_progress') {
    const myRole = gameStore.myRole || '';
    announcerTitle.value = roleMap[myRole] || myRole;
    announcerSubtitle.value = roleSubtitleMap[myRole] || 'Выполняйте цели своей роли для победы.';
    isRoleAnnouncement.value = true;
    showAnnouncer.value = true;
    return;
  }
  if (newPhase && newPhase !== oldPhase) {
    if (isRoleAnnouncement.value && showAnnouncer.value) return;
    announcerTitle.value = phaseMap[newPhase] || 'Новая фаза';
    announcerSubtitle.value = '';
    isRoleAnnouncement.value = false;
    showAnnouncer.value = true;
    setTimeout(() => { showAnnouncer.value = false; }, 3500);
  }
});

const shouldShowResultsPanel = computed(() => {
  return gameStore.lastEvents.length > 0 && !gameStore.isGameOver;
});

const handleAnnouncerClose = () => {
  const wasRoleAnnouncement = isRoleAnnouncement.value;
  showAnnouncer.value = false;
  if (wasRoleAnnouncement) {
    const currentPhase = gameStore.room?.phase;
    if (currentPhase && phaseMap[currentPhase]) {
      setTimeout(() => {
        announcerTitle.value = phaseMap[currentPhase];
        announcerSubtitle.value = '';
        isRoleAnnouncement.value = false;
        showAnnouncer.value = true;
        setTimeout(() => { showAnnouncer.value = false; }, 3500);
      }, 500);
    }
  }
};

watch(() => gameStore.room?.phase, () => {
  selectedPlayerName.value = null;
});

const copyRoomId = async () => {
  if (!gameStore.room?.room_id || isCopied.value) return;
  try {
    await navigator.clipboard.writeText(gameStore.room.room_id);
    isCopied.value = true;
    setTimeout(() => { isCopied.value = false; }, 2000);
  } catch (err) {
    console.error('Не удалось скопировать ID комнаты:', err);
  }
};

const handlePlayerSelect = (playerName: string) => {
  selectedPlayerName.value = selectedPlayerName.value === playerName ? null : playerName;
  if (gameStore.myPlayerHasActed) {
    setTimeout(() => { selectedPlayerName.value = null; }, 300);
  }
};

const submitDescription = (description: string) => {
  gameStore.performAction('introduce', { description });
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
  if (route.name === 'Room') {
    return;
  }
  gameStore.disconnectWebSocket();
});

const handleUpdateRoles = (newRoles: Roles) => {
  gameStore.setRoles(newRoles);
};

const handleUpdateEnvironment = (newEnvironment: string | null) => {
  gameStore.setEnvironment(newEnvironment);
};
</script>

<style scoped>
.room-view {
  min-height: 100vh;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  position: relative;
  z-index: 1;
}

.room-view::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  background-image: url('@/assets/background_light.png');
  background-size: cover;
  background-position: center center;
  transition: opacity 0.8s ease-in-out;
  opacity: 1;
}

.room-view::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -2;
  background-image: url('@/assets/background_dark.png');
  background-position: center center;
  background-size: cover;
  transition: opacity 0.8s ease-in-out;
  opacity: 0;
}

/* --- ИСПРАВЛЕНИЕ ЗДЕСЬ --- */
/* Когда наступает ночь, мы скрываем дневной фон... */
.room-view.is-night::before {
  opacity: 0;
}

/* ...и показываем ночной фон. */
.room-view.is-night::after {
  opacity: 1;
}

/* --- КОНЕЦ ИСПРАВЛЕНИЯ --- */


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
  left: -10px;
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


.room-content.in-game {
  max-width: 900px;
  padding-bottom: 80px;
}

.back-btn-arrow {
  font-size: 1.5rem;
  line-height: 1;
}

.back-btn-text {
  display: none;
}

.state-panel {
  text-align: center;
  padding-top: 40vh;
}

.room-title-wrapper,
.room-title-wrapper-game {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.room-title-wrapper-game {
  display: none;
}

.copy-icon {
  display: none;
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
    padding-bottom: 60px;
  }

  .room-content {
    max-width: 1100px;
  }

  .room-title-wrapper-game {
    display: flex;
  }

  .room-content.in-game {
    max-width: 900px;
  }

  .back-btn-text {
    display: inline;
  }

  .copy-icon {
    display: block;
  }

  .header h1:hover .copy-icon {
    opacity: 1;
  }
}
</style>