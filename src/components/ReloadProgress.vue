<template>
    <DlProgressBar
        v-if="progress < 1"
        label="Progress"
        width="200px"
        :show-value="true"
        :show-percentage="true"
        :value="progress"
    />
    <div v-else style="display: flex; flex-direction: row; gap: 8px; align-items: center">
        <DlIcon
            icon="icon-dl-reload"
            color="dell-blue-500"
            size="16px"
            style="cursor: pointer"
            @click="onReloadClick"
        />
        <div style="display: flex; flex-direction: column">
            <DlTypography color="dell-gray-500" size="small"> Last updated </DlTypography>
            <DlTypography color="dell-gray-900">
                {{ lastUpdated }}
            </DlTypography>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref } from 'vue-demi'
import { DlIcon, DlProgressBar, DlTypography } from '@dataloop-ai/components'

export default defineComponent({
    name: 'ReloadProgress',
    components: {
        DlIcon,
        DlProgressBar,
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

<style scoped></style>
