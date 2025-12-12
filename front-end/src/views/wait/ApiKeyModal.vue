<template>
    <div class="modal-overlay" @click="$emit('close')">
        <div class="modal-content" @click.stop>
            <h3>🔑 API Ключ (Dev)</h3>
            <p class="desc">
                Введите Gemini API Key для этой сессии.
                Он будет использован только для этой комнаты.
            </p>

            <input v-model="key" type="password" class="form-input" placeholder="Вставьте ключ сюда...">

            <div class="actions">
                <button class="btn" @click="save" :disabled="!isValid">Сохранить</button>
                <button class="btn btn-outline" @click="$emit('close')">Отмена</button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';

const emit = defineEmits(['close']);
const gameStore = useGameStore();
const key = ref('');

const isValid = computed(() => key.value.length > 20);

const save = async () => {
    if (isValid.value) {
        await gameStore.setApiKey(key.value);
        emit('close');
    }
};
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    backdrop-filter: blur(5px);
}

.modal-content {
    background: var(--input-bg-color);
    border: 2px solid var(--input-border-color);
    padding: 2rem;
    border-radius: 12px;
    width: 90%;
    max-width: 400px;
    text-align: center;
}

.desc {
    color: var(--secondary-text-color);
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
    line-height: 1.4;
}

.actions {
    display: flex;
    gap: 10px;
    margin-top: 1.5rem;
}

.btn-outline {
    background: transparent;
    border: 1px solid var(--secondary-text-color);
    color: var(--secondary-text-color);
}
</style>