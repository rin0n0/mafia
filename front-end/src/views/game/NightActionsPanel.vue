<template>
    <div v-if="isMyRoleActive && isAlive" class="night-actions-panel">
        <div class="panel-header">
            <h3>{{ actionConfig.title }}</h3>
            <p>{{ actionConfig.description }}</p>
        </div>

        <PlayerGrid>
            <PlayerCard v-for="player in eligibleTargets" :key="player.name" :player="player"
                :is-selectable="!gameStore.myPlayerHasActed" :is-selected="player.name === selectedPlayerName"
                @click="!gameStore.myPlayerHasActed && $emit('playerSelect', player.name)" />
        </PlayerGrid>

        <div class="actions">
            <button @click="submitAction" :disabled="!selectedPlayerName || gameStore.myPlayerHasActed" class="btn">
                {{ buttonText }}
            </button>
        </div>
    </div>
    <div v-if="!isAlive">
        <h3>Вы мертвы</h3>
        <p>Наблюдайте за тем, как все пытаются выжить без вас.</p>
    </div>
    <div v-else class="night-wait-panel">
        <h3>Ночь в городе...</h3>
        <p>Вы мирно спите, пока другие вершат судьбы. Ожидайте наступления утра.</p>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';
import PlayerGrid from './PlayerGrid.vue';
import PlayerCard from './PlayerCard.vue';

const props = defineProps<{
    selectedPlayerName: string | null;
}>();
const emit = defineEmits(['playerSelect']);

const gameStore = useGameStore();
const isAlive = computed(() => gameStore.myPlayer?.is_alive ?? false);


const ACTION_CONFIGS: Record<string, { title: string; description: string; buttonText: string; actionType: string; }> = {
    mafia: {
        title: 'Голосование Мафии',
        description: 'Выберите жертву, которую хотите устранить этой ночью. Ваша команда должна прийти к единому мнению.',
        buttonText: 'Убить',
        actionType: 'mafia_kill'
    },
    doctor: {
        title: 'Выбор Доктора',
        description: 'Выберите игрока, которого хотите спасти от смерти этой ночью. Вы можете выбрать себя.',
        buttonText: 'Вылечить',
        actionType: 'doctor_heal'
    },
    comissar: {
        title: 'Проверка Комиссара',
        description: 'Выберите игрока, чтобы узнать, принадлежит ли он к Мафии.',
        buttonText: 'Проверить',
        actionType: 'commissar_check'
    },
    whore: {
        title: 'Визит Ночной Бабочки',
        description: 'Выберите игрока, чтобы лишить его возможности действовать и голосовать этой ночью.',
        buttonText: 'Блокировать',
        actionType: 'whore_block'
    }
};

const actionConfig = computed(() => ACTION_CONFIGS[gameStore.myRole || '']);
const isMyRoleActive = computed(() => !!gameStore.myRole && gameStore.myRole !== 'citizen');

const eligibleTargets = computed(() => {
    if (!gameStore.room) return [];
    const alivePlayers = gameStore.room.players.filter(p => p.is_alive);

    if (gameStore.myRole === 'doctor') {
        return alivePlayers;
    }

    return alivePlayers.filter(p =>
        p.name !== gameStore.myPlayer?.name &&
        !gameStore.teammates.includes(p.name)
    );
});

const buttonText = computed(() => {
    if (gameStore.myPlayerHasActed) return 'Ожидаем других...';
    if (props.selectedPlayerName) return `${actionConfig.value.buttonText} "${props.selectedPlayerName}"`;
    return 'Выберите цель';
});

const submitAction = () => {
    if (!props.selectedPlayerName) return;
    gameStore.performAction(actionConfig.value.actionType, { target_name: props.selectedPlayerName });
    gameStore.confirmTeamTarget(props.selectedPlayerName);
};

</script>

<style scoped>
.night-actions-panel,
.night-wait-panel {
    background: rgba(0, 0, 0, 0.2);
    border: 2px solid var(--input-border-color);
    border-radius: 10px;
    padding: 1.5rem;
    width: 100%;
    animation: fade-in 0.5s ease-out;
}

.panel-header {
    text-align: center;
    margin-bottom: 1.5rem;
}


.night-wait-panel,
.panel-header h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    color: var(--primary-text-color);
}

.night-wait-panel,
.panel-header p {
    color: var(--secondary-text-color);
    max-width: 600px;
    margin: 0 auto;
}

.actions {
    margin-top: 1.5rem;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
}

.night-wait-panel {
    text-align: center;
}
</style>