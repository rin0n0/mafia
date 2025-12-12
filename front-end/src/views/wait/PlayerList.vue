<template>
  <section class="players-section">
    <h2 class="section-title">Игроки: {{ players.length }}</h2>
    <div class="player-list">
      <div v-for="player in players" :key="player.name" class="player-slot">
        <div class="player-info">
          <span v-if="player.is_host" class="host-icon" title="Администратор">👑</span>
          <div class="player-name">{{ player.name }}</div>
        </div>
      </div>
      <div v-for="i in emptySlots" :key="`empty-${i}`" class="player-slot empty">
        <div class="player-name">Ожидание игрока...</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { PlayerPublic, Roles } from '@/types/game';
import { computed } from 'vue';

const props = defineProps<{
  players: PlayerPublic[],
  roles: Roles,
}>();

const totalRoles = computed(() => Object.values(props.roles).reduce((sum, count) => sum + count, 0));
const emptySlots = computed(() => Math.max(0, totalRoles.value - props.players.length));
</script>

<style scoped>
.players-section {
  width: 100%;
  background-color: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(6px);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.section-title {
  color: var(--primary-text-color);
  text-transform: uppercase;
  font-weight: 900;
  letter-spacing: 1px;
  margin-bottom: 1.5rem;
  text-align: center;
  font-size: 1.2rem;
}

.player-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
  overflow-y: auto;
}

.player-slot {
  background: var(--input-bg-color);
  border: 1px solid var(--input-border-color);
  border-radius: 8px;
  padding: 1rem;
  min-height: 70px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition: all 0.3s ease;
}

.player-slot.empty {
  opacity: 0.5;
  border-style: dashed;
  align-items: center;
}

.player-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.host-icon {
  font-size: 1.5rem;
}

.player-name {
  color: var(--primary-text-color);
  font-weight: 900;
  text-transform: uppercase;
  font-size: 1.2rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (min-width: 992px) {
  .player-list {
    grid-template-columns: 1fr;
  }
}
</style>