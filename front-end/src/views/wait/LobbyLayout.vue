<template>
    <div class="lobby-layout">
        <PlayerList :players="players" :roles="roles" />

        <div class="panel-wrapper">
            <SettingsPanel :initial-roles="roles" :initial-environment="initialEnvironment" :is-host="isHost"
                :player-count="playerCount" :is-loading="isLoading" @update-roles="emit('updateRoles', $event)"
                @update-environment="emit('updateEnvironment', $event)" />

            <div v-if="isHost" class="actions">
                <button @click="startGame" class="btn start-game-btn" :disabled="!canStartGame || isLoading">
                    {{ startGameButtonText }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { PropType } from 'vue';
import { useGameStore } from '@/stores/gameStore';
import type { PlayerPublic, Roles } from '@/types/game';
import PlayerList from '@/views/wait/PlayerList.vue';
import SettingsPanel from '@/views/wait/SettingsPanel.vue';

const props = defineProps({
    players: { type: Array as PropType<PlayerPublic[]>, required: true },
    roles: { type: Object as PropType<Roles>, required: true },
    initialEnvironment: { type: String as PropType<string | null>, required: true },
    isHost: { type: Boolean, required: true },
    playerCount: { type: Number, required: true },
    isLoading: { type: Boolean, required: true },
});

const emit = defineEmits(['updateRoles', 'updateEnvironment']);

const gameStore = useGameStore();

const canStartGame = computed(() => {
    const totalRoles = Object.values(props.roles).reduce((sum, count) => sum + count, 0);
    return props.playerCount === totalRoles && totalRoles > 0;
});

const startGameButtonText = computed(() => {
    if (!canStartGame.value) {
        if (props.playerCount === 0) return 'Ожидание игроков';
        const totalRoles = Object.values(props.roles).reduce((sum, count) => sum + count, 0);
        if (props.playerCount !== totalRoles) {
            return 'Кол-во игроков и ролей не совпадает';
        }
        return 'Распределите роли';
    }
    return 'Начать игру';
});

const startGame = () => {
    if (props.isHost && canStartGame.value) {
        gameStore.startGame();
    }
};

</script>

<style scoped>
.lobby-layout {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    width: 100%;
}

.panel-wrapper {
    display: flex;
    flex-direction: column;
    width: 100%;
}

.actions {
    width: 100%;
    margin-top: 1rem;
}

.start-game-btn {
    padding: 20px;
    font-size: 1.2rem;
}

@media (min-width: 992px) {
    .lobby-layout {
        flex-direction: row;
        align-items: flex-start;
        gap: 2rem;
    }

    .lobby-layout> :first-child {
        flex: 0 0 350px;
    }

    .panel-wrapper {
        flex: 1;
        min-width: 0;
    }
}
</style>