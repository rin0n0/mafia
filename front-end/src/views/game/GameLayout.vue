<template>
    <div class="game-layout">
        <HostDisplay :message="hostMessage" />
        <PlayerGrid>
            <PlayerCard v-for="player in gameStore.room?.players" :key="player.name" :player="player"
                @click="handlePlayerClick(player)" />
        </PlayerGrid>
        <MyRolePanel :role="gameStore.myRole" />
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';
import type { PlayerPublic } from '@/types/game';

import HostDisplay from './HostDisplay.vue';
import PlayerGrid from './PlayerGrid.vue';
import PlayerCard from './PlayerCard.vue';
import MyRolePanel from './MyRolePanel.vue';

const gameStore = useGameStore();

const hostMessage = computed(() => {
    switch (gameStore.room?.phase) {
        case 'introduction_night':
            return 'Все игроки закрывают глаза, наступает ночь знакомств. Ведущий раздает роли...';
        case 'day':
            return `Наступил день ${gameStore.room.day_number}. Город просыпается и обсуждает события прошедшей ночи.`;
        case 'night':
            return `Город засыпает. Просыпаются обладатели особых ролей...`;
        default:
            return 'Игра началась!';
    }
});

const handlePlayerClick = (player: PlayerPublic) => {
    if (!player.is_alive) return;
    console.log('Выбран игрок:', player.name);
};
</script>

<style scoped>
.game-layout {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    width: 100%;
}
</style>