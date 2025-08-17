<template>
    <div class="host-display">
        <p>{{ displayedText }}<span class="cursor"></span></p>
    </div>
</template>

<script setup lang="ts">
import { useTypewriter } from '@/composables/useTypewriter';

const props = defineProps({ message: { type: String, required: true } });
const { displayedText, isTyping } = useTypewriter(() => props.message);
</script>

<style scoped>
.host-display {
    background: var(--input-bg-color);
    border: 2px solid var(--input-border-color);
    border-radius: 10px;

    padding: 1.5rem 2rem;
    text-align: center;
    width: 100%;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: none;
}

.host-display p {
    margin: 0;
    font-size: 1.2rem;
    line-height: 1.6;
    color: var(--primary-text-color);
    text-shadow: none;
}

.cursor.is-typing {
    display: inline-block;
    background-color: var(--primary-text-color);
    margin-left: 8px;
    width: 4px;
    height: 1.2em;
    animation: blink 1s step-end infinite;
}

@keyframes blink {

    from,
    to {
        background-color: transparent;
    }

    50% {
        background-color: var(--primary-text-color);
    }
}

@media (min-width: 768px) {
    .host-display {
        padding: 2rem;
    }
}
</style>