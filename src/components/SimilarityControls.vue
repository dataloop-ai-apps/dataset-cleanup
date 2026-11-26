<template>
    <div class="similarity-controls" :class="{ stacked }">
        <div v-if="stacked" class="settings-title">Settings</div>
        <div class="field">
            <span v-if="stacked" class="field-label">Similarity</span>
            <DlSlider
                v-model="similarityModel"
                class="similarity-slider"
                text=""
                :min="0.001"
                :max="0.3"
                :step="0.001"
                thumb-size="16px"
            />
        </div>
        <div class="field">
            <span v-if="stacked" class="field-label">Minimal cluster size</span>
            <DlSelect
                v-model="clusterSizeModel"
                class="size-select"
                :options="clusterSizeOptions"
                :width="stacked ? '100%' : '64px'"
                highlight-selected
            />
        </div>
        <DlIcon v-if="!stacked" icon="icon-dl-info" size="16px" color="dell-blue-500">
            <DlTooltip>Minimal cluster size</DlTooltip>
        </DlIcon>
    </div>
</template>

<script setup lang="ts">
import { DlSlider, DlSelect, DlIcon, DlTooltip } from '@dataloop-ai/components'
import { computed, defineEmits, defineProps, withDefaults } from 'vue-demi'

const props = withDefaults(
    defineProps<{
        similarity: number
        minClusterSize: number
        clusterSizes: number[]
        stacked?: boolean
    }>(),
    { stacked: false }
)
const emit = defineEmits(['update:similarity', 'update:minClusterSize'])

const similarityModel = computed({
    get: () => props.similarity,
    set: (value: number) => emit('update:similarity', value)
})
const clusterSizeOptions = computed(() => props.clusterSizes.map(String))
const clusterSizeModel = computed({
    get: () => String(props.minClusterSize),
    set: (value: string) => emit('update:minClusterSize', Number(value))
})
</script>

<style scoped>
.similarity-controls {
    display: flex;
    align-items: center;
    gap: 8px;
}

.field {
    display: contents;
}

.similarity-slider {
    width: 190px;
}

.similarity-slider :deep(.slider.non-slim) {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 8px;
}

.similarity-slider :deep(.slider-bar-container) {
    flex: 1 1 0;
    min-width: 0;
    order: 1;
    padding-left: 8px;
}

.similarity-slider :deep(.header) {
    order: 2;
    margin: 0;
    flex-shrink: 0;
}

.similarity-slider :deep(.header .row.text) {
    display: none;
}

.similarity-slider :deep(.header .right-container) {
    display: flex;
    align-items: center;
    gap: 8px;
}

.similarity-slider :deep(.header .dl-button) {
    --dl-button-font-size: 14px;
    font-size: 14px;
    color: var(--dell-blue-600);
}

.similarity-slider :deep(#slider-input) {
    box-sizing: border-box;
    width: 60px;
    height: 32px;
    margin: 0;
    padding: 4px 8px;
    border-color: var(--dell-gray-500);
    border-radius: 0;
    font-size: 14px;
    text-align: center;
}

.size-select :deep(.dl_select__select) {
    box-sizing: border-box;
    width: 100%;
    height: 32px;
    padding: 0 28px 0 12px;
    border-color: var(--dell-gray-500);
    border-radius: 0;
    font-size: 14px;
}

.size-select :deep(.selected-label) {
    font-size: 14px;
    line-height: 20px;
    color: var(--dell-gray-800);
}

.size-select :deep(.adornment-container) {
    height: 100%;
}

.stacked {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
    box-sizing: border-box;
    width: 232px;
    padding: 16px;
    background: var(--dell-white);
}

.stacked .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.stacked .similarity-slider {
    width: 100%;
}

.settings-title {
    font-size: 16px;
    line-height: 24px;
    color: var(--dell-gray-800);
}

.field-label {
    font-size: 12px;
    line-height: 18px;
    color: var(--dell-gray-600);
}
</style>

<style>
@container (max-width: 1079px) {
    .similarity-controls:not(.stacked) .similarity-slider {
        width: 180px;
    }
}

@container (max-width: 725px) {
    .similarity-controls:not(.stacked) .similarity-slider {
        width: 148px;
    }
}

@container (max-width: 627px) {
    .similarity-controls:not(.stacked) {
        display: none;
    }
}
</style>
