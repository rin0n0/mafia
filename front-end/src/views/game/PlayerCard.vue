<template>
    <div class="player-card" :class="{ 'is-dead': !player.is_alive }">
        <div class="player-avatar">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path
                    d="M12 2C9.243 2 7 4.243 7 7s2.243 5 5 5 5-2.243 5-5S14.757 2 12 2zM12 14c-3.86 0-7 3.14-7 7h14c0-3.86-3.14-7-7-7z">
                </path>
            </svg>
        </div>
        <p class="player-name">{{ player.name }}</p>
        <div v-if="player.is_host" class="host-badge" title="Хост комнаты">👑</div>
        <div v-if="!player.is_alive" class="dead-overlay">
            <span>ВЫБЫЛ</span>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import type { PlayerPublic } from '@/types/game';

defineProps({
    player: { type: Object as PropType<PlayerPublic>, required: true },
});
</script>

<style scoped>
.player-card {
    background: var(--input-bg-color);
    border: 2px solid var(--input-border-color);

    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.2s ease;
    aspect-ratio: 1 / 1.2;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    /* Убираем все сложные тени */
    box-shadow: none;
}

.player-card:not(.is-dead):hover {
    /* Простой и понятный эффект приподнимания */
    transform: translateY(-5px);
    /* Подсветка рамки, как у полей ввода при фокусе */
    border-color: var(--input-focus-border-color);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.player-card.is-dead {
    opacity: 0.5;
    filter: grayscale(100%);
    cursor: not-allowed;
    box-shadow: none;
}

.player-card.is-dead:hover {
    transform: none;
    border-color: var(--input-border-color);
}

.player-avatar {
    width: 50%;
    margin-bottom: 0.75rem;
    color: var(--secondary-text-color);
    filter: none;
    /* Убираем тень с иконки */
}

.player-name {
    font-weight: 700;
    font-size: 1rem;
    margin: 0;
    word-break: break-all;
    text-shadow: none;
    /* Убираем тень с текста */
}

.host-badge {
    position: absolute;
    top: 8px;
    left: 8px;
    font-size: 1.2rem;
    filter: none;
}

.dead-overlay {
    /* Стиль для этого элемента уже был хорош, оставляем */
    position: absolute;
    inset: 0;
    background: rgba(150, 44, 39, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    color: var(--primary-text-color);
    font-size: 1.2rem;
    letter-spacing: 2px;
    backdrop-filter: blur(2px);
}
</style>