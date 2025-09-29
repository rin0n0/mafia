<template>
    <div class="notification-container">
        <transition-group name="notification" tag="div">
            <div v-for="notification in uiStore.notifications" :key="notification.id" class="notification-toast">
                {{ notification.message }}
            </div>
        </transition-group>
    </div>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/uiStore';
const uiStore = useUiStore();
</script>

<style scoped>
.notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 2000;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.notification-toast {
    background: rgba(0, 0, 0, 0.8);
    color: var(--primary-text-color);
    padding: 15px 25px;
    border-radius: 8px;
    border-left: 5px solid var(--primary-brand-color);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(5px);
    font-weight: 700;
}

.notification-enter-active,
.notification-leave-active {
    transition: all 0.5s ease;
}

.notification-enter-from,
.notification-leave-to {
    opacity: 0;
    transform: translateX(100%);
}
</style>