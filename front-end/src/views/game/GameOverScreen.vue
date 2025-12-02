<template>
    <div class="game-over-screen">
        <div class="game-over-content">
            <h1 class="title">Игра окончена</h1>
            <h2 class="winner-announcement" :class="winnerTeamClass">
                {{ winnerTeamText }}
            </h2>

            <div class="roles-reveal">
                <div class="team-column">
                    <h3>Мафия</h3>
                    <ul>
                        <li v-for="player in mafiaTeam" :key="player.name">
                            <span class="player-name">{{ player.name }}</span>
                            <span class="player-role">{{ formatRole(player.role) }}</span>
                        </li>
                    </ul>
                </div>
                <div class="team-column">
                    <h3>Мирные жители</h3>
                    <ul>
                        <li v-for="player in citizensTeam" :key="player.name">
                            <span class="player-name">{{ player.name }}</span>
                            <span class="player-role">{{ formatRole(player.role) }}</span>
                        </li>
                    </ul>
                </div>
            </div>

            <button @click="playAgain" class="btn">Вернуться в лобби</button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';

const gameStore = useGameStore();

const winnerTeamText = computed(() => {
    return gameStore.room?.winner === 'mafia' ? 'Победила Мафия!' : 'Победили Мирные жители!';
});

const winnerTeamClass = computed(() => {
    return gameStore.room?.winner === 'mafia' ? 'mafia-win' : 'citizens-win';
});

const mafiaTeam = computed(() => gameStore.room?.players.filter(p => p.role === 'mafia' || p.role === 'whore') || []);
const citizensTeam = computed(() => gameStore.room?.players.filter(p => p.role !== 'mafia' && p.role !== 'whore') || []);

const roleMap: Record<string, string> = {
    mafia: "Мафия", citizen: "Мирный житель", doctor: "Доктор", comissar: "Комиссар", whore: "Ночная бабочка"
};
const formatRole = (role: string | null) => role ? roleMap[role] || role : 'Неизвестно';

const playAgain = () => {
    gameStore.leaveRoom();
};
</script>

<style scoped>
.game-over-screen {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
    animation: fade-in 1s;
}

.game-over-content {
    text-align: center;
    color: var(--primary-text-color);
}

.title {
    font-size: 3rem;
    text-transform: uppercase;
    letter-spacing: 4px;
    color: var(--secondary-text-color);
}

.winner-announcement {
    font-size: 2.5rem;
    margin: 1rem 0 3rem 0;
}

.mafia-win {
    color: var(--primary-brand-color);
}

.citizens-win {
    color: #4CAF50;
}

.roles-reveal {
    display: flex;
    gap: 3rem;
    margin-bottom: 3rem;
}

.team-column {
    background: rgba(255, 255, 255, 0.05);
    padding: 1rem 1.5rem;
    border-radius: 8px;
    min-width: 250px;
}

.team-column h3 {
    border-bottom: 1px solid var(--input-border-color);
    padding-bottom: 0.5rem;
    margin-top: 0;
}

.team-column ul {
    list-style: none;
    padding: 0;
}

.team-column li {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
}

.player-role {
    color: var(--secondary-text-color);
}
</style>