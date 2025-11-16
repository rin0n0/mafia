<template>
    <div class="results-overlay">
        <div class="results-content">
            <div v-for="(item, index) in resultItems" :key="index" class="event-item">
                <span class="event-icon">{{ item.icon }}</span>
                <div class="event-text-content">
                    <h4 v-if="item.title" class="event-title">{{ item.title }}</h4>
                    <p class="event-narration" v-html="item.narration"></p>
                </div>
            </div>
        </div>
    </div>
</template>


<script setup lang="ts">
import { computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';
import type { GameEvent } from '@/types/game';

const gameStore = useGameStore();

const eventIcons: Record<string, string> = {
    kill: '💀',
    save: '🛡️',
    no_kill: '🌙',
    lynch_result: '⚖️',
    lynch_tie: '🤷',
    joke_vote_result: '🤡',
    joke_vote_tie: '🤔',
    day_start_narration: '☀️',
    night_start_narration: '🌃',
    voting_start_narration: '🗳️',
};

const formatText = (text: string) => text.replace(/{{{(.*?)}}}/g, '<strong class="player-name-highlight">$1</strong>');

const resultItems = computed(() => {
    return (gameStore.room?.last_events ?? []).map((event: GameEvent) => {
        const narration = event.narration || event.summary || event.text || '';
        return {
            icon: eventIcons[event.type] || '🔹',
            title: event.title,
            narration: formatText(narration)
        };
    });
});
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
    max-width: 600px;
    /* Увеличим для красивого текста */
    text-align: center;
    box-shadow: 0 10px 30px #000;
    animation: scale-in 0.3s;
    max-height: 80vh;
    overflow-y: auto;
}

.event-item {
    display: flex;
    align-items: flex-start;
    /* Выравниваем по верху */
    gap: 1.5rem;
    text-align: left;
    margin-bottom: 2rem;
}

.event-item:last-child {
    margin-bottom: 0;
}

.event-icon {
    font-size: 2.5rem;
    line-height: 1.2;
}

.event-text-content {
    flex: 1;
}

.event-title {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    color: var(--primary-text-color);
    font-weight: 700;
}

.event-narration {
    margin: 0;
    font-size: 1.1rem;
    line-height: 1.6;
    color: var(--secondary-text-color);
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