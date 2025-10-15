<template>
    <div class="timer-container">
        <div class="timer-bar">
            <div class="timer-bar-inner" :style="{ width: progress + '%' }"></div>
        </div>
        <span class="timer-text">{{ formattedTime }}</span>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
    initialTimeLeft: number;
    totalDuration: number;
}>();

const timeLeft = ref(Math.round(props.initialTimeLeft));
let timerId: number | null = null;

const startTimer = () => {
    stopTimer();
    timerId = window.setInterval(() => {
        if (timeLeft.value > 0) {
            timeLeft.value--;
        } else {
            stopTimer();
        }
    }, 1000);
};

const stopTimer = () => {
    if (timerId) {
        clearInterval(timerId);
        timerId = null;
    }
};

watch(() => props.initialTimeLeft, (newTime) => {
    timeLeft.value = Math.round(newTime);
    startTimer();
});

onMounted(startTimer);
onUnmounted(stopTimer);

const formattedTime = computed(() => {
    const minutes = Math.floor(timeLeft.value / 60);
    const seconds = timeLeft.value % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
});

const progress = computed(() => {
    const duration = props.totalDuration > 0 ? props.totalDuration : 1;
    return (timeLeft.value / duration) * 100;
});
</script>

<style scoped>
.timer-container {
    display: flex;
    align-items: center;
    gap: 1rem;
    width: 100%;
    background: var(--input-bg-color);
    border: 1px solid var(--input-border-color);
    border-radius: 8px;
    padding: 8px 16px;
}

.timer-text {
    font-weight: 700;
    color: var(--primary-text-color);
    font-variant-numeric: tabular-nums;
}

.timer-bar {
    flex-grow: 1;
    height: 10px;
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 5px;
    overflow: hidden;
}

.timer-bar-inner {
    height: 100%;
    background: var(--primary-brand-color);
    border-radius: 5px;
    transition: width 1s linear;
}

@media (max-width: 768px) {
    .timer-container {
        justify-content: center;
    }
}
</style>