<template>
    <div class="intro-form">
        <h3 class="form-title">Расскажите о своем персонаже</h3>
        <p class="form-subtitle">
            Это описание увидит ведущий. Оно поможет сделать игру атмосфернее.
        </p>

        <div class="theme-info">
            <p v-if="gameStore.room?.environ">
                Тема игры: <br /><strong>"{{ gameStore.room.environ }}"</strong>
            </p>
            <p v-else>
                Тема игры не задана. Можете придумать любую историю.
            </p>
        </div>

        <textarea v-model="description" class="form-input" rows="4" maxlength="300"
            placeholder="Например: 'Я старый алкаш, который видел в этом городе всё...'"></textarea>
        <div class="char-counter">{{ description.length }} / 300</div>
        <button @click="submit" class="btn">
            <span v-if="description.length === 0">Пропустить описание</span>
            <span v-else>Отправить</span>
        </button>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useGameStore } from '@/stores/gameStore';

const gameStore = useGameStore();

const description = ref('');

const emit = defineEmits<{
    (e: 'submitDescription', description: string): void
}>();
const submit = () => {
    emit('submitDescription', description.value);
};
</script>

<style scoped>
.intro-form {
    display: flex;
    flex-direction: column;
    background: rgba(0, 0, 0, 0.2);
    border: 2px solid var(--input-border-color);
    border-radius: 10px;
    padding: 1.5rem 2rem;
    width: 100%;
    max-width: 600px;
    margin: 0 auto;
    animation: fade-in 0.5s ease-out;
}

.form-title {
    color: var(--primary-text-color);
    text-align: center;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
}

.form-subtitle {
    color: var(--secondary-text-color);
    text-align: center;
    font-size: 1rem;
    margin: 0 0 1.5rem 0;
}

/* Стили для нового блока */
.theme-info {
    text-align: center;
    color: var(--secondary-text-color);
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
    padding: 0.75rem;
    background-color: rgba(0, 0, 0, 0.15);
    border-radius: 8px;
    border: 1px solid var(--input-border-color);
}

.theme-info p {
    margin: 0;
    color: var(--secondary-text-color);
}

.theme-info strong {
    color: var(--primary-text-color);
    font-weight: 600;
}

.form-input {
    font-size: 1.1rem;
    text-align: left;
    padding: 1rem;
    font-weight: 400;
}

.char-counter {
    text-align: right;
    font-size: 0.9rem;
    color: var(--secondary-text-color);
    margin-top: 0.5rem;
}

.btn {
    margin-top: 1rem;
}

@keyframes fade-in {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>