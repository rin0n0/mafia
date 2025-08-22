<template>
    <div class="game-layout">
        <div v-if="isDiscussionPhase" class="timer-bar">
            <span>Обсуждение: {{ formattedTimeLeft }}</span>
            <div class="timer-bar-inner" :style="{ width: timerProgress + '%' }"></div>
        </div>

        <HostDisplay :message="hostMessage" />

        <IntroductionForm v-if="gameStore.room?.phase === 'introduction_night' && !gameStore.myPlayerHasActed"
            @submit-description="submitDescription" />

        <PlayerGrid v-else>
            <PlayerCard v-for="player in gameStore.room?.players" :key="player.name" :player="player"
                :is-selectable="isVotingPhase && player.is_alive && !gameStore.myPlayerHasActed"
                :is-selected="player.name === selectedPlayerName"
                @click="isVotingPhase && player.is_alive && !gameStore.myPlayerHasActed && $emit('playerSelect', player.name)" />
        </PlayerGrid>

        <MyRolePanel :role="gameStore.myRole" />
    </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, computed, watch } from 'vue';
import { useGameStore } from '@/stores/gameStore';

import HostDisplay from './HostDisplay.vue';
import PlayerGrid from './PlayerGrid.vue';
import PlayerCard from './PlayerCard.vue';
import MyRolePanel from './MyRolePanel.vue';
import IntroductionForm from './IntroductionForm.vue';

defineProps<{
    selectedPlayerName: string | null;
}>();
defineEmits(['playerSelect']);

const gameStore = useGameStore();
const DISCUSSION_TIME = 300; // 5 минут
const timeLeft = ref(DISCUSSION_TIME);
let timerInterval: number | null = null;

const isResultsPhase = computed(() => !!gameStore.lastVoteResults);

const isDiscussionPhase = computed(() =>
    gameStore.room?.phase === 'introduction_day' &&
    !gameStore.currentVoteQuestion &&
    !isResultsPhase.value
);

const isVotingPhase = computed(() =>
    gameStore.room?.phase === 'introduction_day' &&
    !!gameStore.currentVoteQuestion &&
    !isResultsPhase.value
);

const hostMessage = computed(() => {
    if (isResultsPhase.value) return gameStore.lastVoteResults!;
    if (isVotingPhase.value) return gameStore.currentVoteQuestion!;
    if (isDiscussionPhase.value) return "Обсудите произошедшее!";

    switch (gameStore.room?.phase) {
        case 'introduction_night':
            return 'Игроки знакомятся со своими ролями...';
        case 'day':
            return `Наступил день ${gameStore.room.day_number}. Город просыпается и обсуждает события прошедшей ночи.`;
        case 'night':
            return `Город засыпает. Просыпаются обладатели особых ролей...`;
        default:
            return 'Игра началась!';
    }
});


const startTimer = () => {
    stopTimer();
    timeLeft.value = DISCUSSION_TIME;
    timerInterval = window.setInterval(() => {
        if (timeLeft.value > 0) {
            timeLeft.value--;
        } else {
            stopTimer();
        }
    }, 1000);
};

const stopTimer = () => {
    if (timerInterval) clearInterval(timerInterval);
};

watch(isDiscussionPhase, (isDiscussion) => {
    if (isDiscussion) {
        startTimer();
    } else {
        stopTimer();
    }
}, { immediate: true });
onUnmounted(stopTimer);

const formattedTimeLeft = computed(() => {
    const minutes = Math.floor(timeLeft.value / 60);
    const seconds = timeLeft.value % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
});

const timerProgress = computed(() => (timeLeft.value / DISCUSSION_TIME) * 100);

const submitDescription = (description: string) => {
    gameStore.performAction('introduce', { description });
};
</script>

<style scoped>
.game-layout {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    width: 100%;
}

.timer-bar {
    width: 100%;
    background: var(--input-bg-color);
    border: 1px solid var(--input-border-color);
    border-radius: 8px;
    position: relative;
    overflow: hidden;
    padding: 8px 16px;
    text-align: center;
    color: var(--primary-text-color);
    font-weight: 700;
}

.timer-bar span {
    position: relative;
    z-index: 2;
}

.timer-bar-inner {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: var(--primary-brand-color);
    opacity: 0.5;
    transition: width 1s linear;
    z-index: 1;
}
</style>