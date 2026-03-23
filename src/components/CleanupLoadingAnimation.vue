<template>
    <div ref="containerRef" class="cleanup-loader">
        <div class="loader-container">
            <svg
                :viewBox="viewBox"
                class="loader-svg"
                xmlns="http://www.w3.org/2000/svg"
            >
                <defs>
                    <clipPath :id="clipPathId">
                        <path d="M -45 -65 L 15 -65 L 45 -35 L 45 65 L -45 65 Z" />
                    </clipPath>

                    <g :id="fileIconId">
                        <path
                            d="M -45 -65 L 15 -65 L 45 -35 L 45 65 L -45 65 Z"
                            fill="#ffffff"
                        />
                        <g class="dots-wrapper">
                            <g :clip-path="`url(#${clipPathId})`">
                                <g id="layer-1" class="parallax-layer-1">
                                    <circle
                                        v-for="dot in layer1Dots"
                                        :key="`l1-${dot.cx}-${dot.cy}`"
                                        :cx="dot.cx"
                                        :cy="dot.cy"
                                        r="3"
                                        fill="#e8eaed"
                                    />
                                </g>
                                <g id="layer-2" class="parallax-layer-2">
                                    <circle
                                        v-for="dot in layer2Dots"
                                        :key="`l2-${dot.cx}-${dot.cy}`"
                                        :cx="dot.cx"
                                        :cy="dot.cy"
                                        r="3"
                                        fill="#1a73e8"
                                    />
                                </g>
                            </g>
                        </g>
                        <path
                            d="M -45 -65 L 15 -65 L 45 -35 L 45 65 L -45 65 Z"
                            fill="none"
                            stroke="#c4c4c4"
                            stroke-width="4"
                            stroke-linejoin="round"
                        />
                    </g>
                </defs>

                <g class="icon icon-1"><use :href="`#${fileIconId}`" /></g>
                <g class="icon icon-2"><use :href="`#${fileIconId}`" /></g>
                <g class="icon icon-3"><use :href="`#${fileIconId}`" /></g>
                <g class="icon icon-4"><use :href="`#${fileIconId}`" /></g>
            </svg>
        </div>
        <div v-if="showProgressBar" class="progress-bar-wrapper">
            <DlProgressBar
                label="Progress"
                :width="progressBarWidth"
                :show-value="true"
                :show-percentage="true"
                :value="progress"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
import { DlProgressBar } from '@dataloop-ai/components'
import { computed, onMounted, onUnmounted, ref } from 'vue-demi'

const props = withDefaults(
    defineProps<{
        progress?: number
        showProgressBar?: boolean
    }>(),
    {
        progress: 0,
        showProgressBar: true
    }
)

const viewBox = '0 0 600 400'

const clipPathId = `file-clip-${Math.random().toString(36).slice(2)}`
const fileIconId = `file-icon-${Math.random().toString(36).slice(2)}`

const spacing = 13
const cols = 14
const rows = 18

const layer1Dots = computed(() => {
    const dots: { cx: number; cy: number }[] = []
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if ((r + c) % 2 !== 0) {
                const offsetX = r % 2 === 0 ? 0 : spacing / 2
                dots.push({
                    cx: -90 + c * spacing + offsetX,
                    cy: -110 + r * spacing
                })
            }
        }
    }
    return dots
})

const layer2Dots = computed(() => {
    const dots: { cx: number; cy: number }[] = []
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if ((r + c) % 2 === 0) {
                const offsetX = r % 2 === 0 ? 0 : spacing / 2
                dots.push({
                    cx: -90 + c * spacing + offsetX,
                    cy: -110 + r * spacing
                })
            }
        }
    }
    return dots
})

const progressBarWidth = computed(() => {
    if (typeof window === 'undefined') return '240px'
    const w = window.innerWidth - 32
    return `${Math.min(520, Math.max(240, w))}px`
})

let currentX = 0
let currentY = 0
let targetX = 0
let targetY = 0
let rafId: number

const handleMouseMove = (e: MouseEvent) => {
    targetX = (e.clientX / window.innerWidth - 0.5) * 2
    targetY = (e.clientY / window.innerHeight - 0.5) * 2
}

const containerRef = ref<HTMLElement | null>(null)

const animateParallax = () => {
    currentX += (targetX - currentX) * 0.08
    currentY += (targetY - currentY) * 0.08
    const el = containerRef.value
    if (el) {
        el.style.setProperty('--mouseX', String(currentX))
        el.style.setProperty('--mouseY', String(currentY))
    }
    rafId = requestAnimationFrame(animateParallax)
}

onMounted(() => {
    document.addEventListener('mousemove', handleMouseMove)
    animateParallax()
})

onUnmounted(() => {
    document.removeEventListener('mousemove', handleMouseMove)
    cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.cleanup-loader {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 24px;
    gap: 24px;
}

.loader-container {
    width: 100%;
    max-width: 480px;
    min-width: 120px;
    max-height: 480px;
    min-height: 120px;
    aspect-ratio: 600 / 400;
    padding: 20px;
}

.loader-svg {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.icon {
    animation: carousel 8s infinite cubic-bezier(0.4, 0, 0.2, 1);
}

.icon-1 {
    animation-delay: 0s;
    --delay: 0s;
}
.icon-2 {
    animation-delay: -2s;
    --delay: -2s;
}
.icon-3 {
    animation-delay: -4s;
    --delay: -4s;
}
.icon-4 {
    animation-delay: -6s;
    --delay: -6s;
}

@keyframes carousel {
    0%,
    18.75% {
        transform: translate(80px, 160px) scale(0);
        opacity: 0;
    }
    25%,
    43.75% {
        transform: translate(190px, 160px) scale(0.6);
        opacity: 0.25;
    }
    50%,
    68.75% {
        transform: translate(300px, 160px) scale(1);
        opacity: 1;
    }
    75%,
    93.75% {
        transform: translate(410px, 160px) scale(0.6);
        opacity: 0.25;
    }
    100% {
        transform: translate(520px, 160px) scale(0);
        opacity: 0;
    }
}

.dots-wrapper {
    animation: dots-visibility 8s infinite cubic-bezier(0.4, 0, 0.2, 1);
    animation-delay: var(--delay, 0s);
}

@keyframes dots-visibility {
    0%,
    43.75% {
        opacity: 0;
    }
    50%,
    68.75% {
        opacity: 1;
    }
    75%,
    100% {
        opacity: 0;
    }
}

.parallax-layer-1 {
    transform: translate(
        calc(var(--mouseX, 0) * -5px),
        calc(var(--mouseY, 0) * -5px)
    );
    will-change: transform;
}

.parallax-layer-2 {
    transform: translate(
        calc(var(--mouseX, 0) * -16px),
        calc(var(--mouseY, 0) * -16px)
    );
    will-change: transform;
}

.progress-bar-wrapper {
    width: 100%;
    max-width: 520px;
    min-width: 240px;
    padding: 0 16px;
}
</style>
