<template>
  <div class="room-view">
    <div v-if="gameStore.room" class="room-content">
      <div class="header">
        <router-link to="/" @click="gameStore.leaveRoom" class="back-btn" title="Покинуть комнату">
          <span class="back-btn-arrow">←</span>
          <span class="back-btn-text">Назад в лобби</span>
        </router-link>
        <h1>Комната #{{ gameStore.room.room_id }}</h1>
      </div>

      <div class="room-layout">
        <PlayerList :players="gameStore.room.players" :roles="gameStore.room.roles" />
        <SettingsPanel :initial-roles="gameStore.room.roles" :initial-environment="gameStore.room.environ"
          :is-host="gameStore.isHost" :player-count="gameStore.playerCount" :is-loading="gameStore.isLoading"
          @update-roles="handleUpdateRoles" @update-environment="handleUpdateEnvironment" />
      </div>

      <div class="actions">
        <button @click="startGame" class="btn start-game-btn" :disabled="!gameStore.isHost || !canStartGame">
          {{ startGameButtonText }}
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
import { onMounted, onUnmounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useGameStore } from '@/stores/gameStore';
import type { Roles } from '@/types/game';

import PlayerList from '@/views/PlayerList.vue';
import SettingsPanel from '@/views/SettingsPanel.vue';

const gameStore = useGameStore();
const route = useRoute();

onMounted(async () => {
  const roomId = route.params.id as string;

  if (!gameStore.room || gameStore.room.room_id !== roomId) {
    await gameStore.fetchRoomDetails(roomId);
  }
  if (gameStore.room?.room_id == roomId) {
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
    console.log("Отправляем запрос на старт игры!");
    gameStore.startGame();
  }
};
</script>

/* src/views/RoomView.vue */
<style scoped>
.room-view {
  background-image: url('@/assets/background_light.png');
  background-size: cover;
  background-position: center center;
  min-height: 100vh;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.room-content {
  width: 100%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transition: max-width 0.3s ease;
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

.room-layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.actions {
  width: 100%;
}

.state-panel {
  text-align: center;
  padding-top: 40vh;
}

@media (min-width: 992px) {
  .room-view {
    align-items: center;
  }

  .room-content {
    max-width: 1100px;
  }

  .room-layout {
    flex-direction: row;
    align-items: stretch;
    gap: 2rem;
  }

  .room-layout> :first-child {
    flex: 0 0 350px;
  }

  .room-layout> :last-child {
    flex: 1;
  }

  .back-btn-text {
    display: inline;
  }
}
</style>