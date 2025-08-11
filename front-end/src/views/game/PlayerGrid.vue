<template>
    <div class="player-grid">
        <slot></slot>
    </div>
</template>

<style scoped>
.player-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 1rem;
}

@media (min-width: 768px) {
    .player-grid {
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 1.5rem;
    }
}
</style>