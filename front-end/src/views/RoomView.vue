<template>
  <div class="room-container">
    <img src="@/assets/logo.png" alt="Mafia Game Logo" class="logo">

    <div v-if="gameStore.room" class="room-panel">
      <router-link to="/" class="back-to-menu-btn">
        <span class="arrow">←</span> 
        <span>Главное меню</span>
      </router-link>
      <div class="room-header">
        <h1>Комната #{{ gameStore.room.room_id }}</h1>
        <p>Статус: {{ gameStore.room.status }}</p>  
      </div>
      <div class="room-main-content">
        <section class="players-section">
          <h2 class="section-title">Игроки: {{ gameStore.room.players.length }}</h2>
          <div class="player-list">
            <div 
              v-for="(player, index) in gameStore.room.players" 
              :key="index" 
              class="player-slot"
            >
              <div v-if="player">
                <div class="player-name">{{player.name}}</div>
                <div v-if="player.is_host" class="player-subtitle">Администратор</div>
              </div>
            </div>
          </div>
        </section>

        <section class="settings-section">
          <h2 class="section-title">Настройки комнаты</h2>
          <div class="settings-list">
            <div v-for="setting in roleSettings" :key="setting.role" class="setting-item">
              <span class="role-name">{{ setting.label }}</span>
              <div class="counter">
                <button class="counter-btn" @click="decrementRole(setting)" :disabled="setting.count <= setting.min">
                  -
                </button>
                <span class="counter-value">{{ setting.count }}</span>
                <button class="counter-btn" @click="incrementRole(setting)">
                  +
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div class="room-actions">
        <button @click="setRoles" class="btn start-game-btn">
          Начать игру
        </button>
      </div>
    </div>
     <div v-else>
        <p>Загрузка комнаты или комната не найдена...</p>
        <router-link to="/">Вернуться в лобби</router-link>
      </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, watch } from "vue";
import { useGameStore } from "@/stores/gameStore";
import { useUserStore } from "@/stores/userStore";
import '../assets/styles/global.css'
import '../assets/styles/room.css'
import type{Roles} from "@/types/game"

const gameStore = useGameStore();
const userStore = useUserStore();

onMounted(() => {
  if (gameStore.room) {
    gameStore.connectWebSocket();
  } else {
    console.error("Состояние комнаты потеряно при обновлении страницы.");
  }
});

onUnmounted(() => {
  gameStore.disconnectWebSocket();
});

const roleSettings = ref([
  { role: 'mafia', label: 'Мафия', count: 1, min: 1 },
  { role: 'citizen', label: 'Мирные', count: 0, min: 0 },
  { role: 'doctor', label: 'Доктор', count: 0, min: 0 },
  { role: 'commissar', label: 'Комиссар', count: 0, min: 0 },
  { role: 'whore', label: 'Потаскуха', count: 0, min: 0 },
]);

const createRoleObject = (roleSettings: any[]): Roles => {
  return roleSettings.reduce((acc, curr) => {
    acc[curr.role] = curr.count;
    return acc;
  }, {
    mafia: 0,
    citizen: 0,
    doctor: 0,
    commissar: 0,
    whore: 0
  });
};

const setRoles = () => {
  const roles = createRoleObject(roleSettings.value);
  gameStore.setRolesSetting(roles);
};

const incrementRole = (setting: { count: number }) => {
  const totalPlayers = gameStore.room?.players.length;
  const totalRoles = roleSettings.value.reduce((sum, s) => sum + s.count, 0);
  if (totalPlayers) if (totalRoles < totalPlayers) {
    setting.count++;
  }
};

const decrementRole = (setting: { count: number; min: number }) => {
  if (setting.count > setting.min) {
    setting.count--;
  }
};

</script>
