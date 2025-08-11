<template>
  <section class="settings-section">
    <h2 class="section-title">Настройки ролей</h2>
    <div class="settings-list">
      <div v-for="setting in roleSettings" :key="setting.role" class="setting-item">
        <span class="role-name">{{ setting.label }}</span>
        <div class="counter">
          <button class="counter-btn" @click="decrementRole(setting.role as keyof Roles)"
            :disabled="!isHost || setting.count <= setting.min">-</button>
          <span class="counter-value">{{ setting.count }}</span>
          <button class="counter-btn" @click="incrementRole(setting.role as keyof Roles)"
            :disabled="!isHost || totalRoles >= playerCount">+</button>
        </div>
      </div>
    </div>
    <transition name="fade">
      <div v-if="isHost && hasChanges" class="actions">
        <button class="btn" @click="applyChanges">Применить</button>
        <button class="btn btn-outline" @click="resetChanges">Сбросить</button>
      </div>
    </transition>
  </section>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { Roles } from '@/types/game';

const props = defineProps<{
  initialRoles: Roles,
  isHost: boolean,
  playerCount: number
}>();

const emit = defineEmits<{
  (e: 'update-roles', newRoles: Roles): void
}>();

const localRoles = ref<Roles>({ ...props.initialRoles });
watch(() => props.initialRoles, (newRoles) => {
  localRoles.value = { ...newRoles };
}, { deep: true });

const hasChanges = computed(() => JSON.stringify(localRoles.value) !== JSON.stringify(props.initialRoles));

const roleSettings = computed(() => [
  { role: 'mafia', label: 'Мафия', count: localRoles.value.mafia, min: 1 },
  { role: 'citizen', label: 'Мирные', count: localRoles.value.citizen, min: 0 },
  { role: 'doctor', label: 'Доктор', count: localRoles.value.doctor, min: 0 },
  { role: 'comissar', label: 'Комиссар', count: localRoles.value.comissar, min: 0 },
  { role: 'whore', label: 'Потаскуха', count: localRoles.value.whore, min: 0 },
]);

const totalRoles = computed(() => Object.values(localRoles.value).reduce((sum, count) => sum + count, 0));

const incrementRole = (role: keyof Roles) => {
  if (totalRoles.value < props.playerCount) {
    localRoles.value[role]++;
  }
};

const decrementRole = (role: keyof Roles) => {
  const min = role === 'mafia' ? 1 : 0;
  if (localRoles.value[role] > min) {
    localRoles.value[role]--;
  }
};

const applyChanges = () => {
  emit('update-roles', { ...localRoles.value });
};

const resetChanges = () => {
  localRoles.value = { ...props.initialRoles };
}
</script>

<style scoped>
.settings-section {
  flex: 1;
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

.settings-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.setting-item,
.counter {
  display: flex;
  align-items: center;
}

.setting-item {
  justify-content: space-between;
}

.role-name {
  color: var(--primary-text-color);
  font-weight: 700;
  text-transform: uppercase;
  font-size: 1rem;
}

.counter-btn,
.counter-value {
  background: var(--input-bg-color);
  border: 1px solid var(--input-border-color);
  color: var(--primary-text-color);
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.2rem;
  font-weight: 700;
  height: 45px;
}

.counter-btn {
  width: 45px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.counter-btn:hover {
  background-color: #3e1e1e;
}

.counter-btn:first-child {
  border-radius: 8px 0 0 8px;
}

.counter-btn:last-child {
  border-radius: 0 8px 8px 0;
}

.counter-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.counter-value {
  width: 50px;
  border-left: none;
  border-right: none;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-top: auto;
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

@media (max-width: 992px) {
  .btn {
    font-size: 0.8rem;
  }
}
</style>