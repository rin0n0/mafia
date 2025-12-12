<template>
    <div class="game-over-overlay">
        <div class="game-over-card">
            <div class="header-group">
                <h1 class="title">Игра окончена</h1>
                <div class="divider"></div>
                <h2 class="winner-announcement" :class="winnerTeamClass">
                    {{ winnerTeamText }}
                </h2>
            </div>

            <div v-if="epilogue" class="narrator-epilogue">
                <h3 class="epilogue-title">{{ epilogue.title }}</h3>
                <p class="epilogue-text" v-html="epilogue.narration"></p>
            </div>

            <div class="roles-reveal">
                <div class="team-column mafia-column">
                    <h3 class="team-title">Мафия</h3>
                    <ul class="player-list">
                        <li v-for="player in mafiaTeam" :key="player.name" class="player-item">
                            <span class="player-name" :class="{ 'is-me': isMe(player.name) }">
                                {{ player.name }}
                            </span>
                            <span class="player-role">{{ formatRole(player.role) }}</span>
                        </li>
                        <li v-if="mafiaTeam.length === 0" class="empty-list">Никого</li>
                    </ul>
                </div>

                <div class="team-column citizen-column">
                    <h3 class="team-title">Мирные жители</h3>
                    <ul class="player-list">
                        <li v-for="player in citizensTeam" :key="player.name" class="player-item">
                            <span class="player-name" :class="{ 'is-me': isMe(player.name) }">
                                {{ player.name }}
                            </span>
                            <span class="player-role">{{ formatRole(player.role) }}</span>
                        </li>
                    </ul>
                </div>
            </div>
            <button @click="playAgain" class="btn primary-btn">
                Вернуться в лобби
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';
import { useUserStore } from '@/stores/userStore';
import type { GameEvent } from '@/types/game';

const gameStore = useGameStore();
const userStore = useUserStore();

const isMe = (name: string) => userStore.playerName === name;

const winnerTeamText = computed(() => {
    return gameStore.room?.winner === 'mafia' ? 'Победа Мафии' : 'Победа Мирных жителей';
});

const winnerTeamClass = computed(() => {
    return gameStore.room?.winner === 'mafia' ? 'mafia-win' : 'citizens-win';
});

const mafiaTeam = computed(() => gameStore.room?.players.filter(p => p.role === 'mafia' || p.role === 'whore') || []);
const citizensTeam = computed(() => gameStore.room?.players.filter(p => p.role !== 'mafia' && p.role !== 'whore') || []);

const roleMap: Record<string, string> = {
    mafia: "Мафия", citizen: "Мирный", doctor: "Доктор", comissar: "Комиссар", whore: "Потаскуха"
};
const formatRole = (role: string | null) => role ? roleMap[role] || role : '—';

const epilogue = computed(() => {
    if (!gameStore.room?.last_events) return null;
    return gameStore.room.last_events.find((e: GameEvent) => e.type === 'game_over_narration') || null;
});

const playAgain = () => {
    gameStore.leaveRoom();
};
</script>

<style scoped>
.game-over-overlay {
    position: fixed;
    inset: 0;
    backdrop-filter: blur(12px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 300;
    animation: fadeIn 0.8s ease-out;
    padding: 16px;
}

.game-over-card {
    background: var(--input-bg-color);
    border: 2px solid var(--input-border-color);
    border-radius: 16px;
    padding: 1.5rem;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    animation: scaleIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.header-group {
    text-align: center;
    margin-bottom: 2rem;
    width: 100%;
}

.title {
    font-size: 1.2rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--secondary-text-color);
    margin: 0;
    opacity: 0.8;
}

.divider {
    height: 2px;
    width: 40px;
    background: var(--input-border-color);
    margin: 0.8rem auto;
}

.winner-announcement {
    font-size: 2rem;
    margin: 0;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1px;
    line-height: 1.1;
    text-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
}

.mafia-win {
    color: var(--primary-brand-color);
}

.citizens-win {
    color: #90caf9;
}

.narrator-epilogue {
    background: rgba(0, 0, 0, 0.3);
    border-left: 4px solid var(--input-border-color);
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 2rem;
    width: 100%;
    text-align: left;
}

.epilogue-title {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
    color: var(--primary-text-color);
    font-weight: 700;
}

.epilogue-text {
    margin: 0;
    color: var(--secondary-text-color);
    font-style: italic;
    line-height: 1.4;
    font-size: 0.95rem;
}

.roles-reveal {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.5rem;
    width: 100%;
    margin-bottom: 2rem;
}

.team-column {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    flex-direction: column;
}

.team-title {
    font-size: 1.1rem;
    text-transform: uppercase;
    margin: 0 0 0.8rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    text-align: center;
    font-weight: 700;
}

.mafia-column {
    border-top: 4px solid var(--primary-brand-color);
}

.mafia-column .team-title {
    color: var(--primary-brand-color);
}

.citizen-column {
    border-top: 4px solid #90caf9;
}

.citizen-column .team-title {
    color: #90caf9;
}

.player-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.player-item {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 1rem;
}

.player-name {
    font-weight: 700;
    color: var(--primary-text-color);
}

.player-name.is-me {
    color: #fff;
    text-decoration: underline;
    text-decoration-color: rgba(255, 255, 255, 0.3);
}

.player-role {
    font-size: 0.85rem;
    color: var(--secondary-text-color);
    text-transform: uppercase;
    font-weight: 500;
}

.empty-list {
    text-align: center;
    color: var(--secondary-text-color);
    font-style: italic;
    opacity: 0.5;
}

.primary-btn {
    width: 100%;
    padding: 16px;
    font-size: 1.1rem;
    background-color: var(--primary-brand-color);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-top: auto;
}

.primary-btn:hover {
    transform: translateY(-2px);
    background-color: var(--primary-brand-hover-color);
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

@keyframes scaleIn {
    from {
        opacity: 0;
        transform: scale(0.95);
    }

    to {
        opacity: 1;
        transform: scale(1);
    }
}


@media (min-width: 768px) {
    .game-over-card {
        padding: 3rem;
        max-width: 800px;
    }

    .title {
        font-size: 1.5rem;
        letter-spacing: 4px;
    }

    .winner-announcement {
        font-size: 3.5rem;
    }

    .narrator-epilogue {
        padding: 1.5rem;
    }

    .epilogue-title {
        font-size: 1.25rem;
    }

    .epilogue-text {
        font-size: 1.1rem;
    }

    .roles-reveal {
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
    }

    .team-column {
        padding: 1.5rem;
    }

    .team-title {
        font-size: 1.3rem;
    }

    .player-item {
        font-size: 1.15rem;
    }

    .primary-btn {
        max-width: 400px;
        font-size: 1.2rem;
        padding: 18px;
    }
}
</style>