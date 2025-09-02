<template>
    <div class="results-overlay" @click="dismiss">
        <div class="results-content">
            <h3>{{ panelTitle }}</h3>
            <div v-for="(item, index) in resultItems" :key="index" class="event-item">
                <span class="event-icon">{{ item.icon }}</span>
                <p class="event-text" v-html="item.text"></p>
            </div>
            <button class="btn" @click="dismiss">Понятно</button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';

const gameStore = useGameStore();

const panelTitle = computed(() => {
    if (gameStore.room?.phase === 'day') return 'События прошедшей ночи';
    return 'Итоги голосования';
});

const eventIcons: Record<string, string> = {
    kill: '💀', save: '🛡️', no_kill: '🌙', lynch_result: '⚖️', joke_vote_result: '🤡'
};

const formatText = (text: string) => text.replace(/{{{(.*?)}}}/g, '<strong class="player-name-highlight">$1</strong>');

const resultItems = computed(() => {
    return gameStore.lastEvents.map(event => ({
        icon: eventIcons[event.type] || '🔹',
        text: formatText(event.text)
    }));
});

const dismiss = () => {
    gameStore.clearResults();
};
</script>

<style scoped>
.results-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
    animation: fade-in 0.3s;
}

.results-content {
    background: var(--input-bg-color);
    border: 2px solid var(--input-border-color);
    border-radius: 12px;
    padding: 2rem;
    width: 90%;
    max-width: 500px;
    text-align: center;
    box-shadow: 0 10px 30px #000;
    animation: scale-in 0.3s;
}

h3 {
    margin: 0 0 1.5rem 0;
    font-size: 1.8rem;
    color: var(--secondary-text-color);
}

.event-item {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    font-size: 1.3rem;
    margin-bottom: 1rem;
}

.event-icon {
    font-size: 2.5rem;
}

.btn {
    margin-top: 1.5rem;
}

:deep(.player-name-highlight) {
    color: var(--primary-brand-color);
    font-weight: 900;
}

@keyframes fade-in {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

@keyframes scale-in {
    from {
        transform: scale(0.9);
        opacity: 0;
    }

    to {
        transform: scale(1);
        opacity: 1;
    }
}
</style>