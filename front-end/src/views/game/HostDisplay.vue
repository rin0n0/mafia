<template>
    <div class="host-display">
        <p>{{ message }}</p>
    </div>
</template>

<script setup lang="ts">
defineProps({
    message: { type: String, required: true },
});
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

@media (min-width: 768px) {
    .host-display {
        padding: 2rem;
    }
}
</style>