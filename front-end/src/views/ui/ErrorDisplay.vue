<template>
    <div class="error-container">
        <transition name="error-fade">
            <div v-if="message" class="error-toast">
                <div class="error-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                        <path
                            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z">
                        </path>
                    </svg>
                </div>
                <p class="error-message">{{ message }}</p>
                <button @click="$emit('close')" class="close-btn" title="Закрыть">
                    &times;
                </button>
            </div>
        </transition>
    </div>
</template>

<script setup lang="ts">
defineProps<{
    message: string | null;
}>();
defineEmits(['close']);
</script>

<style scoped>
.error-container {
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 3000;
    pointer-events: none;
    /* Контейнер не должен мешать кликам */
}

.error-toast {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(40, 15, 15, 0.9);
    color: var(--primary-text-color);
    padding: 1rem 1.5rem;
    border-radius: 12px;
    border: 2px solid var(--error-color);
    box-shadow: 0 5px 25px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    max-width: 90vw;
    width: 500px;
    pointer-events: auto;
    /* А вот само уведомление должно быть кликабельным */
}

.error-icon {
    color: var(--error-color);
    flex-shrink: 0;
}

.error-icon svg {
    width: 28px;
    height: 28px;
}

.error-message {
    margin: 0;
    font-weight: 700;
    flex-grow: 1;
}

.close-btn {
    background: none;
    border: none;
    color: var(--secondary-text-color);
    font-size: 2rem;
    line-height: 1;
    padding: 0 0.5rem;
    cursor: pointer;
    transition: color 0.2s;
}

.close-btn:hover {
    color: var(--primary-text-color);
}

.error-fade-enter-active,
.error-fade-leave-active {
    transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1);
}

.error-fade-enter-from,
.error-fade-leave-to {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
}
</style>