<template>
    <div v-if="gameStore.myRole" class="my-role-panel">
        <div class="role-info">
            <span>Ваша роль:</span>
            <strong>{{ formattedRole }}</strong>
        </div>

        <div v-if="teamMembers.length > 1" class="teammates-info">
            <span class="teammates-title">Команда:</span>
            <ul class="teammates-list">
                <li v-for="member in teamMembers" :key="member.name" :class="{ 'is-me': member.isMe }">
                    {{ member.name }}
                </li>
            </ul>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useGameStore } from '@/stores/gameStore';

const gameStore = useGameStore();

const roleMap: Record<string, string> = {
    mafia: "Мафия",
    citizen: "Мирный житель",
    doctor: "Доктор",
    comissar: "Комиссар",
    whore: "Потаскуха"
};

const formattedRole = computed(() => {
    const role = gameStore.myRole;
    return role ? roleMap[role] || role : '';
});

const teamMembers = computed(() => {
    if (!gameStore.myPlayer) return [];
    const members = [{ name: `${gameStore.myPlayer.name} (Вы)`, isMe: true }];
    gameStore.teammates.forEach(name => members.push({ name, isMe: false }));
    return members;
});
</script>

<style scoped>
.teammates-list li.is-me {
    font-weight: 700;
    color: #fff;
}

.my-role-panel {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background-color: var(--primary-brand-color);
    color: white;
    padding: 12px 20px;
    border-radius: 10px;
    font-size: 0.9rem;
    z-index: 100;
    text-align: center;
    box-shadow: inset 0 -4px 0 var(--shadow-color), 0 5px 15px rgba(0, 0, 0, 0.3);
    border: none;
    max-width: 300px;
    margin: 0 auto;
}

.role-info span {
    opacity: 0.8;
    margin-right: 0.5rem;
    font-weight: 400;
}

.role-info strong {
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.teammates-info {
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    padding-top: 0.75rem;
}

.teammates-title {
    font-weight: 600;
    opacity: 0.8;
    display: block;
    margin-bottom: 0.25rem;
}

.teammates-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    justify-content: center;
    gap: 1rem;
    font-weight: 500;
}

@media (min-width: 992px) {
    .my-role-panel {
        position: fixed;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        flex-direction: row;
        align-items: center;
        gap: 1.5rem;
        padding: 14px 30px;
        font-size: 1rem;
        max-width: none;
    }

    .role-info {
        display: flex;
        align-items: baseline;
    }

    .role-info strong {
        font-size: 1.1rem;
    }

    .teammates-info {
        border-top: none;
        border-left: 1px solid rgba(255, 255, 255, 0.2);
        padding-top: 0;
        padding-left: 1.5rem;
    }

    .teammates-list {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.25rem;
    }
}
</style>