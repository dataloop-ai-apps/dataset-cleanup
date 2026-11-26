<template>
    <div v-if="progress >= 1" class="reload-progress">
        <div class="reload-button" @click="onReloadClick">
            <DlIcon icon="icon-dl-reload" color="dell-blue-500" size="16px" />
        </div>
        <div v-if="lastUpdated" class="last-updated">
            <DlTypography color="dell-gray-600" size="12px"> Last Updated </DlTypography>
            <DlTypography color="dell-gray-800" size="12px">
                {{ lastUpdated }}
            </DlTypography>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref } from 'vue-demi'
import { DlIcon, DlTypography } from '@dataloop-ai/components'

export default defineComponent({
    name: 'ReloadProgress',
    components: {
        DlIcon,
        DlTypography
    },
    props: {
        lastUpdated: { type: String, required: true },
        progress: { type: Number, required: true }
    },
    emits: ['reload'],
    methods: {
        onReloadClick() {
            this.$emit('reload')
        }
    }
})
</script>

<style scoped>
.reload-progress {
    display: flex;
    align-items: center;
    gap: 4px;
    padding-right: 16px;
    border-right: 1px solid var(--dell-gray-200);
}

.reload-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    cursor: pointer;
}

.last-updated {
    display: flex;
    flex-direction: column;
    white-space: nowrap;
}
</style>

<style>
@container (max-width: 1079px) {
    .reload-progress {
        padding-right: 8px;
    }

    .reload-progress .last-updated {
        display: none;
    }
}
</style>
