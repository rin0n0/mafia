<template>
    <div v-if="role" class="my-role-panel">
        <span>Ваша роль:</span>
        <strong>{{ formattedRole }}</strong>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { PropType } from 'vue';

const props = defineProps({
    role: { type: String as PropType<string | null>, required: true },
});

const roleMap: Record<string, string> = {
    mafia: "Мафия",
    citizen: "Мирный житель",
    doctor: "Доктор",
    comissar: "Комиссар",
    whore: "Потаскуха"
};

const formattedRole = computed(() => {
    return props.role ? roleMap[props.role] || props.role : '';
});
</script>

<style scoped>
.my-role-panel {
    position: fixed;
    bottom: 15px;
    left: 50%;
    transform: translateX(-50%);
    background-color: var(--primary-brand-color);
    color: white;
    padding: 14px 30px;
    border-radius: 10px;
    font-size: 1rem;
    z-index: 100;
    text-align: center;
    box-shadow: inset 0 -4px 0 var(--shadow-color), 0 5px 15px rgba(0, 0, 0, 0.3);
    border: none;
}

.my-role-panel span {
    opacity: 0.8;
    margin-right: 0.75rem;
    font-weight: 500;
}

.my-role-panel strong {
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    display: block;
    line-height: 1.1;
}
</style>