<template>
  <div class="room-view">
    <div v-if="gameStore.room">
      <h1>Комната: {{ gameStore.room.room_id }}</h1>
      <p>Статус: {{ gameStore.room.status }}</p>

      <h2>Игроки ({{ gameStore.room.players.length }}):</h2>
      <ul>
        <li v-for="player in gameStore.room.players" :key="player.client_id">
          {{ player.name }}
          <span v-if="player.client_id === gameStore.room.host.client_id">(Хост)</span>
          <span v-if="player.client_id === userStore.clientId">(Это вы)</span>
        </li>
      </ul>

      <div class="connection-status">
        WS Соединение:
        <span :class="{
          connected: gameStore.isConnected,
          disconnected: !gameStore.isConnected,
        }">
          {{ gameStore.isConnected ? "Подключено" : "Отключено" }}
        </span>
      </div>

      <button @click="gameStore.leaveRoom()">Выйти из комнаты</button>
    </div>
    <div v-else>
      <p>Загрузка комнаты или комната не найдена...</p>
      <router-link to="/">Вернуться в лобби</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { useGameStore } from "@/stores/gameStore";
import { useUserStore } from "@/stores/userStore";

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
</script>

<style scoped>
.connected {
  color: green;
}

.disconnected {
  color: red;
}
</style>
