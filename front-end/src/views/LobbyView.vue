<template>
  <div class="lobby-container">
    <div class="lobby-content">
      
      <img src="../assets/logo.png" alt="Mafia Game Logo" class="logo">
      
      <div class="name-entry-block">
        <h3 class="form-label">Представьтесь, пожалуйста</h3>
        <input 
          type="text" 
          v-model="localPlayerName" 
          class="form-input" 
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
        <button class="btn" @click="gameStore.createRoom()">
          Создать комнату
        </button><br/>
        <p class="form-label">Присоединиться к комнате по коду</p>
        <input 
          v-model="joinRoomId" 
          class="form-input room-code-input" 
          placeholder="КОД"
          maxlength="4"
        >
        
        <button 
          class="btn" 
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

import '../assets/styles/lobby.css'; 


const userStore = useUserStore();
const gameStore = useGameStore();

const localPlayerName = ref(userStore.playerName);

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