<template>
  <div class="lobby-container">
    <div class="lobby-content">

      <img src="../assets/logo.png" alt="Mafia Game Logo" class="logo">

      <div class="name-entry-block">
        <h3 class="form-label">Представьтесь, пожалуйста</h3>
        <input type="text" v-model="localPlayerName" class="form-input" placeholder="Ваш никнейм">
        <div class="player-feedback">
          <span v-if="isNameTooLong" class="error-message short">
            Не более 20 символов.
          </span>
          <span v-if="isNameTooShort" class="char-counter">
            Не менее 3 символов.
          </span>
          <span class="char-counter" :class="{ 'error': isNameTooLong }">
            {{ localPlayerName.length }} / 20
          </span>
        </div>
      </div>

      <div class="main-lobby-block">
        <button class="btn" @click="gameStore.createRoom()">
          Создать комнату
        </button><br />
        <p class="form-label">Присоединиться к комнате по коду</p>
        <input v-model="joinRoomId" class="form-input room-code-input" placeholder="КОД" maxlength="4"
          @keydown.enter.prevent="joinGame">

        <button class="btn" @click="joinGame" :disabled="joinRoomId.length < 4">
          Присоединиться
        </button>
        <ErrorDisplay :message="gameStore.error" @close="gameStore.clearError()" />
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useUserStore } from '@/stores/userStore';
import { useGameStore } from '@/stores/gameStore';
import { useRoute } from 'vue-router';
const route = useRoute();
import ErrorDisplay from './ui/ErrorDisplay.vue';
const userStore = useUserStore();
const gameStore = useGameStore();

const localPlayerName = ref(userStore.playerName);
const joinRoomId = ref('');

onMounted(() => {
  if (route.query.room) {
    joinRoomId.value = (route.query.room as string).toUpperCase();
  }
});

watch(localPlayerName, (newValue) => {
  if (newValue.length <= 20) {
    userStore.setPlayerName(newValue);
  }
});

const isNameTooLong = computed(() => localPlayerName.value.length > 20);
const isNameTooShort = computed(() => localPlayerName.value.length < 3);

const joinGame = () => {
  if (joinRoomId.value) {
    gameStore.joinRoom(joinRoomId.value.toUpperCase());
  }
};
</script>

<style scoped>
.lobby-container {
  background-image: url('@/assets/background_light.png');
  background-size: cover;
  background-position: center center;
  min-height: 100vh;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
}


.lobby-content {
  width: 100%;
  max-width: 380px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo {
  width: 100%;
  max-width: 250px;
  margin-bottom: 2.5rem;
}

.name-entry-block,
.main-lobby-block {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.room-code-input {
  text-transform: uppercase;
  letter-spacing: 0.5em;
  padding-left: calc(15px + 0.25em);
}

.player-feedback {
  width: 100%;
  text-align: right;
  padding-right: 5px;
  height: 20px;
  margin-top: 5px;
}

.char-counter {
  font-size: 0.9em;
  color: rgba(255, 255, 255, 0.6);
}

.char-counter.error {
  color: var(--error-color);
  font-weight: bold;
}
</style>