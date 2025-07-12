<template>
  <div class="lobby">
    <h1>Добро пожаловать в Мафию</h1>

    <div class="player-setup">
      <label for="playerName">Ваш никнейм:</label>
      <input id="playerName" type="text" v-model="playerName" placeholder="Введите имя" />
    </div>

    <div class="actions">
      <h2>Создать игру</h2>
      <button @click="gameStore.createRoom()">Создать новую комнату</button>

      <h2>Присоединиться к игре</h2>
      <input v-model="joinRoomId" placeholder="Введите код комнаты (напр. ABCD)" />
      <button @click="joinGame">Присоединиться</button>
    </div>

    <p v-if="gameStore.error" class="error">{{ gameStore.error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGameStore } from "@/stores/gameStore";
import { useUserStore } from "@/stores/userStore";

const userStore = useUserStore();
const gameStore = useGameStore();

const joinRoomId = ref("");

const playerName = computed({
  get(){

  },
  set(newValue:string){
    userStore.setPlayerName(newValue);
  }
})

const joinGame = () => {
  if (joinRoomId.value) {
    gameStore.joinRoom(joinRoomId.value.toUpperCase());
  }
};
</script>

<style scoped>
.lobby {
  text-align: center;
  max-width: 600px;
  margin: 0 auto;
}

.error {
  color: red;
}

input {
  margin: 5px;
  padding: 5px;
}

button {
  padding: 5px 10px;
}
</style>
