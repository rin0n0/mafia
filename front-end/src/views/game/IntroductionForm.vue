<template>
    <div class="intro-form">
        <div v-if="welcomeNarration" class="ai-welcome">
            <h3 class="form-title">{{ welcomeNarration.title }}</h3>
            <p class="form-subtitle" v-html="welcomeNarration.narration"></p>
        </div>

        <div class="action-prompt">
            <h3 class="form-title-secondary">Теперь ваша очередь</h3>
            <p class="form-subtitle">Расскажите о своем персонаже, чтобы ведущий мог вплести вашу историю в игру.</p>
        </div>

        <div class="theme-info">
            <p v-if="gameStore.room?.environ">
                Тема игры: <strong>"{{ gameStore.room.environ }}"</strong>
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
import { ref, computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';

const gameStore = useGameStore();
const description = ref('');

const welcomeNarration = computed(() => {
    const narration = gameStore.room?.active_narration;
    if (narration && narration.type === 'game_start_narration') {
        return {
            title: narration.title || 'Начало игры',
            narration: narration.narration?.replace(/{{{(.*?)}}}/g, '<strong>$1</strong>') || ''
        }
    }
    return null;
});

const emit = defineEmits<{ (e: 'submitDescription', description: string): void }>();
const submit = () => { emit('submitDescription', description.value); };
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

.ai-welcome {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--input-border-color);
}

.ai-welcome .form-title {
    font-size: 1.8rem;
}

.ai-welcome .form-subtitle {
    font-size: 1.1rem;
    line-height: 1.6;
}

.action-prompt {
    margin-bottom: 1rem;
}

.form-title-secondary {
    color: var(--primary-text-color);
    text-align: center;
    font-size: 1.3rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
}

.form-subtitle {
    color: var(--secondary-text-color);
    text-align: center;
    font-size: 1rem;
    margin: 0 0 1.5rem 0;
}

.theme-info {
    text-align: center;
    width: 100%;
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
    word-break: break-all;
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