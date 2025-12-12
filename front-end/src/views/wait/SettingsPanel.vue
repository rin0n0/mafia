<template>
  <div class="settings-panel">
    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'roles' }]" @click="activeTab = 'roles'">
        Настройки Ролей
      </button>
      <button :class="['tab-btn', { active: activeTab === 'environment' }]" @click="activeTab = 'environment'">
        Сеттинг Игры
      </button>
    </div>

    <div class="tab-content">
      <div v-if="activeTab === 'roles'">
        <RoleSettings :initial-roles="initialRoles" :is-host="isHost" :player-count="playerCount"
          @update-roles="emit('update-roles', $event)" />
      </div>
      <div v-if="activeTab === 'environment'">
        <EnvironmentSettings :initial-environment="initialEnvironment" :is-host="isHost" :is-loading="isLoading"
          @update-environment="emit('update-environment', $event)" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { Roles } from '@/types/game';

import RoleSettings from './RoleSettings.vue';
import EnvironmentSettings from './EnvironmentSettings.vue';

defineProps<{
  initialRoles: Roles,
  initialEnvironment: string | null,
  isHost: boolean,
  playerCount: number,
  isLoading: boolean
}>();

const emit = defineEmits<{
  (e: 'update-roles', newRoles: Roles): void,
  (e: 'update-environment', newEnvironment: string | null): void
}>();

const activeTab = ref<'roles' | 'environment'>('roles');
</script>

<style scoped>
.settings-panel {
  width: 100%;
  background-color: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(6px);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.tabs {
  display: flex;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid var(--input-border-color);
}

.tab-btn {
  flex: 1;
  padding: 1rem;
  background-color: transparent;
  border: none;
  color: var(--secondary-text-color);
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 4px solid transparent;
  transform: translateY(2px);
}

.tab-content {
  flex-grow: 1;
  display: flex;
}

.tab-content>div {
  flex-grow: 1;
  display: flex;
}

.tab-btn.active {
  color: var(--primary-text-color);
  border-bottom-color: var(--primary-brand-color);
}

.tab-btn:not(.active):hover {
  background-color: rgba(255, 255, 255, 0.05);
}
</style>