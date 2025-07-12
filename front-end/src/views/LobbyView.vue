<template>
  <div class="lobby-container">
    <div class="lobby-content">
      
      <img src="../assets/logo.png" alt="Mafia Game Logo" class="logo">
      
      <div class="name-entry-block">
        <h3 class="input-label">Представьтесь, пожалуйста</h3>
        <input 
          type="text" 
          v-model="localPlayerName" 
          class="lobby-input" 
          placeholder="Ваш никнейм"
        >
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
        <button class="btn btn-lobby" @click="gameStore.createRoom()">
          Создать комнату
        </button><br/>
        <p class="join-label">Присоединиться к комнате по коду</p>
        <input 
          v-model="joinRoomId" 
          class="lobby-input room-code-input" 
          placeholder="КОД"
          maxlength="4"
        >
        
        <button 
          class="btn btn-lobby" 
          @click="joinGame" 
          :disabled="joinRoomId.length < 4"
        >
          Присоединиться
        </button>
        <p v-if="gameStore.error" class="error-message">{{ gameStore.error }}</p>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useUserStore } from '@/stores/userStore';
import { useGameStore } from '@/stores/gameStore';

const userStore = useUserStore();
const gameStore = useGameStore();


const localPlayerName = ref(userStore.playerName);
const isNameSaved = ref(userStore.playerName.length > 2);

watch(localPlayerName, (newValue) => {
  if (newValue.length <= 20) {
    userStore.setPlayerName(newValue);
  }
});

const isNameTooLong = computed(() => localPlayerName.value.length > 20);
const isNameTooShort = computed(() => localPlayerName.value.length < 3);


const joinRoomId = ref('');
const joinGame = () => {
  if (joinRoomId.value) {
    gameStore.joinRoom(joinRoomId.value.toUpperCase());
  }
};
</script>

<style scoped>
.lobby-container {
  background-image: url('../assets/background_light.png');
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

.input-label,
.join-label {
  color: rgba(239, 233, 227, 0.7);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.8rem;
  margin-bottom: 0.75rem;
  font-weight: 700;
}

.lobby-input {
  background: rgba(0, 0, 0, 0.35);
  border: 2px solid #5a1e1e;
  border-radius: 10px;
  padding: 15px;
  width: 100%;
  text-align: center;
  color: #EFE9E3;
  font-size: 1.5rem;
  font-weight: 700;
  outline: none;
  transition: all 0.3s ease;
}

.lobby-input::placeholder {
  color: rgba(239, 233, 227, 0.4);
  font-weight: 400;
}

.lobby-input:focus {
  border-color: #EFE9E3; 
}

.room-code-input::placeholder {
  font-weight: 700;
}

.room-code-input {
  text-transform: uppercase;
  letter-spacing: 0.5em; 
  padding-left: calc(15px + 0.25em); 
}

.btn {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 1.5rem;
}

.btn-lobby {
  background-color: #d92c27; 
  color: white;
  box-shadow: inset 0 -4px 0 rgba(0, 0, 0, 0.3);
}
.btn-lobby:hover {
  background-color: #ff4d4d; 
}
.btn-lobby:active {
  transform: translateY(2px);
  box-shadow: inset 0 -2px 0 rgba(0, 0, 0, 0.3);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: inset 0 -4px 0 rgba(0, 0, 0, 0.3) !important;
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
    color: #ff4d4d;
    font-weight: bold;
}
.error-message {
    margin-top: 1rem;
    color: #ff4d4d;
    font-weight: bold;
}
.error-message.short {
  margin-top: 0.5rem;
  font-size: 0.9rem;
}
</style>