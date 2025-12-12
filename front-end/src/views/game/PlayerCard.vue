<template>
    <div class="player-card" :class="{
        'is-dead': !player.is_alive,
        'is-selectable': isSelectable,
        'is-selected': isSelected,
        'is-me': isMyCard,
    }">
        <div class="card-border"></div>
        <div v-if="player.has_acted" class="acted-indicator" title="Действие выполнено"></div>

        <div class="player-avatar">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path
                    d="M12 2C9.243 2 7 4.243 7 7s2.243 5 5 5 5-2.243 5-5S14.757 2 12 2zM12 14c-3.86 0-7 3.14-7 7h14c0-3.86-3.14-7-7-7z">
                </path>
            </svg>
        </div>
        <p class="player-name">{{ player.name }}</p>
        <div v-if="player.is_alive && !isMyCard" class="emote-wrapper">
            <button @click.stop="sendEmote" class="emote-btn" title="Подмигнуть">👁️</button>
        </div>
        <div v-if="indicators.length" class="team-indicators">
            <div v-for="indicator in indicators" :key="indicator.voterName" class="indicator-dot"
                :class="{ 'is-confirmed': indicator.isConfirmed }" @mouseenter="showDotTooltip($event, indicator)"
                @mouseleave="hideTooltip" @click.stop="showDotTooltip($event, indicator)">
                {{ indicator.voterName.charAt(0).toUpperCase() }}
            </div>
        </div>

        <div v-if="!player.is_alive" class="dead-overlay">
            <span>ВЫБЫЛ</span>
        </div>
        <Tooltip :show="showTooltip" :text="tooltipText" :target-element="tooltipTarget" />
    </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useGameStore } from '@/stores/gameStore';
import { useUserStore } from '@/stores/userStore';
import type { PlayerPublic } from '@/types/game';
import Tooltip from '@/views/ui/ToolTip.vue';

interface Indicator {
    voterName: string;
    isConfirmed: boolean;
}

const showTooltip = ref(false);
const tooltipText = ref('');
const tooltipTarget = ref<HTMLElement | null>(null);
let hideTooltipTimeout: number;

const showDotTooltip = (event: MouseEvent, indicator: Indicator) => {
    clearTimeout(hideTooltipTimeout);
    tooltipTarget.value = event.currentTarget as HTMLElement;
    const actionText = indicator.isConfirmed ? 'выбрал' : 'хочет выбрать';
    tooltipText.value = `Игрок ${indicator.voterName} ${actionText} эту цель`;
    showTooltip.value = true;
};

const hideTooltip = () => {
    hideTooltipTimeout = window.setTimeout(() => {
        showTooltip.value = false;
    }, 100);
};

const props = defineProps<{ player: PlayerPublic; isSelectable?: boolean; isSelected?: boolean; }>();
const gameStore = useGameStore();
const userStore = useUserStore();
const isMyCard = computed(() => props.player.name === userStore.playerName);
const isTeamTarget = computed(() => gameStore.getVotersForPlayer(props.player.name).length > 0);
const sendEmote = () => gameStore.sendEmote(props.player.name);

const indicators = computed(() => {
    const allIndicators = gameStore.teamActivity[props.player.name] || [];
    return allIndicators.filter(indicator => indicator.voterName !== userStore.playerName);
});
</script>

<style scoped>
.player-card {
    background: rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(6px);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    cursor: default;
    transition: box-shadow 0.2s ease;
    aspect-ratio: 1 / 1.2;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border: 2px solid transparent;
    -webkit-tap-highlight-color: transparent;
}

.card-border {
    position: absolute;
    inset: 0;
    border-radius: 12px;
    border: 2px solid var(--input-border-color);
    transition: border-color 0.2s ease, border-width 0.2s ease;
}

.player-card.is-selectable:not(.is-dead) {
    cursor: pointer;
}

.player-card.is-selected .card-border {
    border-color: var(--primary-brand-color);
    border-width: 3px;
}

.player-card.is-me .card-border {
    border-color: rgba(239, 233, 227, 0.4);
}

.player-card.is-me.is-selected .card-border {
    border-color: var(--primary-brand-color);
}

.acted-indicator {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 12px;
    height: 12px;
    background-color: #4CAF50;
    border-radius: 50%;
    box-shadow: 0 0 8px #4CAF50;
}

.player-avatar {
    width: 45%;
    margin-bottom: 0.5rem;
    color: var(--secondary-text-color);
}

.player-name {
    font-weight: 700;
    font-size: 0.9rem;
    margin: 0;
    line-height: 1.2;
    min-height: 2.2em;
    overflow-wrap: break-word;
    word-break: break-all;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
}

.player-card.is-dead {
    opacity: 0.6;
    filter: grayscale(80%);
}

.dead-overlay {
    position: absolute;
    inset: 0;
    background: rgba(80, 20, 20, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    color: var(--primary-text-color);
    font-size: 1.2rem;
    letter-spacing: 2px;
    backdrop-filter: blur(2px);
}

.emote-wrapper {
    position: absolute;
    bottom: 4px;
    right: 4px;
}

.emote-btn {
    background: transparent;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    opacity: 0.6;
    transition: all 0.2s ease;
}

.team-indicators {
    position: absolute;
    bottom: 8px;
    left: 8px;
    display: flex;
    gap: 4px;
}

.indicator-dot {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background-color: #808080;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.8rem;
    border: 2px solid rgba(0, 0, 0, 0.5);
    transition: background-color 0.3s ease;
    cursor: pointer;
}

.indicator-dot.is-confirmed {
    background-color: var(--primary-brand-color);
}

@media (hover: hover) and (pointer: fine) {
    .player-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .player-card.is-selectable:not(.is-dead):hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }

    .player-card.is-selectable:not(.is-dead):hover .card-border {
        border-color: var(--input-focus-border-color);
    }

    .emote-btn {
        opacity: 0;
    }

    .player-card:hover .emote-btn {
        opacity: 0.6;
    }

    .emote-btn:hover {
        opacity: 1;
        transform: scale(1.2);
    }

    .indicator-dot {
        cursor: help;
    }
}
</style>