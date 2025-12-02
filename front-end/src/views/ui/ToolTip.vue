<template>
    <teleport to="body">
        <transition name="tooltip-fade">
            <div v-if="show" ref="tooltipRef" class="tooltip-container" :style="tooltipStyle">
                {{ text }}
                <div class="tooltip-arrow" :style="arrowStyle"></div>
            </div>
        </transition>
    </teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue';
import type { Ref, CSSProperties } from 'vue';

const props = defineProps<{
    show: boolean;
    text: string;
    targetElement: HTMLElement | null;
}>();

const position = ref({ x: 0, y: 0 });
const arrowLeft = ref<number | null>(null);
const tooltipRef: Ref<HTMLElement | null> = ref(null);

const tooltipStyle = computed((): CSSProperties => ({
    top: `${position.value.y}px`,
    left: `${position.value.x}px`,
}));

const arrowStyle = computed((): CSSProperties => ({
    left: arrowLeft.value !== null ? `${arrowLeft.value}px` : '50%',
}));


watch(() => [props.show, props.targetElement], async ([newShow, newTarget]) => {
    if (newShow && newTarget && typeof newTarget === 'object') {
        await nextTick();

        const targetRect = newTarget.getBoundingClientRect();
        const tooltipEl = tooltipRef.value;
        if (!tooltipEl) return;
        const tooltipRect = tooltipEl.getBoundingClientRect();

        const spacing = 8;

        let y = targetRect.top - tooltipRect.height - spacing;
        let x = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);

        const viewportWidth = window.innerWidth;
        if (x < spacing) {
            x = spacing;
        } else if (x + tooltipRect.width > viewportWidth - spacing) {
            x = viewportWidth - tooltipRect.width - spacing;
        }

        if (y < spacing) {
            y = targetRect.bottom + spacing;
        }

        const targetCenter = targetRect.left + targetRect.width / 2;
        arrowLeft.value = targetCenter - x;


        position.value = { x, y };
    }
});
</script>

<style scoped>
.tooltip-container {
    position: fixed;
    z-index: 9999;
    background-color: rgba(26, 26, 26, 0.95);
    color: #fff;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 600;
    max-width: 200px;
    text-align: center;
    pointer-events: none;
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.tooltip-arrow {
    position: absolute;
    width: 0;
    height: 0;
    border-style: solid;
    transform: translateX(-50%);
}

.tooltip-container[style*="top"] .tooltip-arrow {
    top: 100%;
    border-width: 6px 6px 0 6px;
    border-color: rgba(26, 26, 26, 0.95) transparent transparent transparent;
}

.tooltip-container[style*="bottom"] .tooltip-arrow {
    bottom: 100%;
    border-width: 0 6px 6px 6px;
    border-color: transparent transparent rgba(26, 26, 26, 0.95) transparent;
}

.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
    opacity: 0;
    transform: translateY(5px);
}
</style>