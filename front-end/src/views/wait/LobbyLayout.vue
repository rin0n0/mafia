<template>
    <div class="lobby-layout">
        <PlayerList :players="players" :roles="roles" />
        <SettingsPanel :initial-roles="roles" :initial-environment="initialEnvironment" :is-host="isHost"
            :player-count="playerCount" :is-loading="isLoading" @update-roles="emit('updateRoles', $event)"
            @update-environment="emit('updateEnvironment', $event)" />
    </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import type { PlayerPublic, Roles } from '@/types/game';
import PlayerList from '@/views/wait/PlayerList.vue';
import SettingsPanel from '@/views/wait/SettingsPanel.vue';

defineProps({
    players: { type: Array as PropType<PlayerPublic[]>, required: true },
    roles: { type: Object as PropType<Roles>, required: true },
    initialEnvironment: { type: String as PropType<string | null>, required: true },
    isHost: { type: Boolean, required: true },
    playerCount: { type: Number, required: true },
    isLoading: { type: Boolean, required: true },
});

const emit = defineEmits(['updateRoles', 'updateEnvironment']);
</script>

<style scoped>
.lobby-layout {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    width: 100%;
}

@media (min-width: 992px) {
    .lobby-layout {
        flex-direction: row;
        align-items: stretch;
        gap: 2rem;
    }

    .lobby-layout> :first-child {
        flex: 0 0 350px;
    }

    .lobby-layout> :last-child {
        flex: 1;
    }
}
</style>