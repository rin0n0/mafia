<template>
    <div class="game-layout">
        <MyRolePanel />
        <NightActionsPanel v-if="gameStore.isNightActionPhase" :selected-player-name="selectedPlayerName"
            @player-select="$emit('playerSelect', $event)" />
        <div v-else class="day-view">
            <HostDisplay :message="cleanedHostMessage" />
            <div v-if="isDiscussionPhase" class="timer-bar">
                <span>Обсуждение: {{ formattedTimeLeft }}</span>
                <div class="timer-bar-inner" :style="{ width: timerProgress + '%' }"></div>
            </div>
            <PlayerGrid>
                <PlayerCard v-for="player in gameStore.room?.players" :key="player.name" :player="player"
                    :is-selectable="isPlayerSelectable(player)" :is-selected="player.name === selectedPlayerName"
                    @click="isPlayerSelectable(player) && $emit('playerSelect', player.name)" />
            </PlayerGrid>
        </div>

        <div class="actions">
            <button v-if="isDiscussionPhase" @click="readyForVote" :disabled="gameStore.myPlayerHasActed" class="btn">
                {{ gameStore.myPlayerHasActed ? 'Ожидаем других...' : 'Готов к голосованию' }}
            </button>
            <button v-if="isVotingPhase" @click="submitVote"
                :disabled="!selectedPlayerName || gameStore.myPlayerHasActed" class="btn">
                {{ voteButtonText }}
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from 'vue';
import { useGameStore } from '@/stores/gameStore';
import type { PlayerPublic } from '@/types/game';

import MyRolePanel from './MyRolePanel.vue';
import NightActionsPanel from './NightActionsPanel.vue';
import HostDisplay from './HostDisplay.vue';
import PlayerGrid from './PlayerGrid.vue';
import PlayerCard from './PlayerCard.vue';

const props = defineProps<{ selectedPlayerName: string | null; }>();
defineEmits(['playerSelect']);

const gameStore = useGameStore();
const DISCUSSION_TIME = 180;
const timeLeft = ref(DISCUSSION_TIME);
let timerInterval: number | null = null;

const isDiscussionPhase = computed(() => {
    const phase = gameStore.room?.phase;
    return phase === 'day' || phase === 'introduction_day';
});

const isVotingPhase = computed(() => gameStore.isVotingPhase);

const hostMessage = computed(() => {
    const phase = gameStore.room?.phase;
    const day = gameStore.room?.day_number;

    switch (phase) {
        case 'introduction_night':
            return "Ночь знакомств. Расскажите ведущему о себе в форме ниже.";
        case 'introduction_day':
            return "Первый день. Познакомьтесь друг с другом и обсудите, кто кажется вам подозрительным.";
        case 'day':
            return `День ${day}. Обсудите события прошедшей ночи и решите, кто следующий кандидат на выбывание.`;
        case 'joke_voting':
            return "Шуточное голосование! Выберите самого подозрительного игрока. Это ни на что не повлияет... пока что.";
        case 'voting':
            return "Голосование за казнь! Выберите игрока, которого вы считаете мафией.";
        default:
            return 'Ожидание следующей фазы...';
    }
});
const isPlayerSelectable = (player: PlayerPublic) => {
    if (!player.is_alive || gameStore.myPlayerHasActed) return false;
    return isVotingPhase.value;
};


const voteButtonText = computed(() => {
    if (gameStore.myPlayerHasActed) return 'Ожидаем других...';
    if (props.selectedPlayerName) {
        const actionText = gameStore.room?.phase === 'joke_voting' ? 'Голосовать за' : 'Казнить';
        return `${actionText} "${props.selectedPlayerName}"`;
    }
    return 'Выберите игрока';
});

const readyForVote = () => gameStore.performAction('ready_for_vote', {});
const submitVote = () => {
    if (!props.selectedPlayerName) return;
    gameStore.performAction('vote', { target_name: props.selectedPlayerName });
};

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
const cleanedHostMessage = computed(() => {
    const message = hostMessage.value;
    if (!message) return '';
    return message.replace(/{{{|}}}/g, '');
});

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

</script>

<style scoped>
.game-layout {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    width: 100%;
}

.actions {
    margin-top: 1rem;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
    width: 100%;
}

.day-view {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
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