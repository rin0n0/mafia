<template>
    <transition name="announcer-fade">
        <div v-if="show" class="announcer-overlay">
            <div class="announcer-content">
                <h1 class="announcer-title">{{ title }}</h1>
                <h2 v-if="subtitle" :class="subtitleClasses">{{ subtitle }}</h2>
                <button v-if="isRole" @click="emit('close')" class="btn">Продолжить</button>
            </div>
        </div>
    </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
    show: boolean;
    title: string;
    subtitle?: string;
    isRole?: boolean;
    role?: string;
}>();

const emit = defineEmits<{
    (e: 'close'): void;
}>();

const subtitleClasses = computed(() => {
    const classes = ['announcer-subtitle'];
    if (props.role === 'mafia' || props.role === 'whore') {
        classes.push('role-mafia');
    } else {
        classes.push('role-citizen');
    }
    return classes;
});
</script>

<style scoped>
.announcer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    width: 100vw;
    height: 100vh;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(5px);
}

.announcer-content {
    text-align: center;
    color: white;
}

.announcer-title {
    font-size: 5rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 5px;
    animation: slide-in 0.8s cubic-bezier(0.25, 1, 0.5, 1) forwards;
    text-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
}

.announcer-subtitle {
    font-size: 2.5rem;
    padding: 0 20px;
    opacity: 0;
    animation: fade-in 0.5s 0.5s ease-out forwards;
    font-weight: 700;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    transition: color 0.3s ease;
}

.announcer-subtitle.role-mafia {
    color: var(--primary-brand-color);
}

.announcer-subtitle.role-citizen {
    color: var(--citizen-color, #5ea8ff);
}


.btn {
    margin-top: 3rem;
    opacity: 0;
    animation: fade-in 0.5s 1s ease-out forwards;
    min-width: 200px;
    width: auto;
}

@media (max-width: 768px) {
    .announcer-title {
        font-size: 2.5rem;
    }

    .announcer-subtitle {
        font-size: 1.5rem;
    }
}

@keyframes slide-in {
    from {
        transform: translateY(50px);
        opacity: 0;
    }

    to {
        transform: translateY(0);
        opacity: 1;
    }
}

@keyframes fade-in {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

.announcer-fade-enter-active {
    transition: opacity 0.3s ease;
}

.announcer-fade-enter-from,
.announcer-fade-leave-to {
    opacity: 0;
}

.announcer-fade-leave-active {
    transition: opacity 0.5s ease;
}
</style>