<template>
    <div v-if="gameStore.specialAnnouncement" class="announcement-overlay" @click="clear">
        <div class="announcement-content">
            <p v-html="formattedText"></p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';
import { useGameStore } from '@/stores/gameStore';

const gameStore = useGameStore();

const formattedText = computed(() =>
    gameStore.specialAnnouncement?.replace(/{{(.*?)}}/g, '<strong class="player-name-highlight">$1</strong>') || ''
);

const clear = () => {
    gameStore.clearSpecialAnnouncement();
};

watch(() => gameStore.specialAnnouncement, (newVal) => {
    if (newVal) {
        setTimeout(() => {
            clear();
        }, 6000);
    }
});
</script>

<style scoped>
.announcement-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(5px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 250;
    cursor: pointer;
    animation: fade-in 0.3s ease-out;
}

.announcement-content {
    background-color: var(--input-bg-color);
    border: 2px solid var(--primary-brand-color);
    border-radius: 10px;
    padding: 2rem 3rem;
    max-width: 600px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    transform: scale(0.95);
    animation: scale-in 0.3s ease-out forwards;
}

.announcement-content p {
    font-size: 1.5rem;
    font-weight: 500;
    margin: 0;
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
        transform: scale(0.95);
        opacity: 0;
    }

    to {
        transform: scale(1);
        opacity: 1;
    }
}
</style>