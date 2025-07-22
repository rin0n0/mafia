<template>
  <section class="settings-section">
    <h2 class="section-title">Сеттинг Игры</h2>
    <p class="section-description">
      Опишите мир, в котором происходит игра. Ведущий будет использовать это для создания атмосферы.
    </p>
    <textarea
      v-model="localEnviron"
      class="form-input environment-input"
      placeholder="Например: Гангстерский Чикаго 30-х"
      :disabled="!isHost"
      rows="3"
    ></textarea>
    
    <div v-if="isHost && hasChanges" class="actions">
      <button class="btn" @click="applyChanges" :disabled="isLoading">
        Применить
      </button>
      <button class="btn btn-outline" @click="resetChanges">
        Сбросить
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch, defineProps, defineEmits} from 'vue';

const props = defineProps<{
  initialEnvironment: string | null;
  isHost: boolean;
  isLoading: boolean; 
}>();

const emit = defineEmits<{
  (e: 'update-environment', newEnvironment: string | null): void
}>();

const localEnviron = ref(props.initialEnvironment);

watch(() => props.initialEnvironment, (newVal) => {
  localEnviron.value = newVal;
});

const hasChanges = computed(() => localEnviron.value !== props.initialEnvironment);

const applyChanges = () => {
  emit('update-environment', localEnviron.value);
};

const resetChanges = () => {
  localEnviron.value = props.initialEnvironment;
};
</script>

<style scoped>
.settings-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.section-description {
  color: var(--secondary-text-color);
  font-size: 0.9rem;
  text-align: center;
  margin-bottom: 1rem;
  line-height: 1.4;
}

.section-title {
  color: var(--secondary-text-color);
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 2px;
  margin-bottom: 1.5rem;
  text-align: center;
}

.environment-input {
  text-align: left;
  font-size: 1rem;
  font-weight: 500;
  resize: vertical; 
  resize: none;
  min-height: 251.7px;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-top: auto; 
}

.btn-secondary {
  background-color: var(--input-bg-color);
  color: var(--primary-text-color);
  border: 2px solid var(--primary-brand-color);
}

.btn:disabled, .btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>