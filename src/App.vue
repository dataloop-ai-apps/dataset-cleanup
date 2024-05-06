<template>
    <DlThemeProvider :is-dark="isDark">
        <div v-if="!isReady" class="loading-spinner">
            <DlSpinner text="Loading App..." size="128px" />
        </div>
        <div v-else>
            <div class="top-bar">
                <div
                    style="
                        display: flex;
                        flex-direction: row;
                        align-items: center;
                        gap: 15px;
                    "
                >
                    <DlTypography variant="h4">
                        Last updated: {{ lastUpdated }}
                    </DlTypography>
                    <DlButton
                        :label="buttonLabel"
                        :disabled="operationRunning"
                        :outlined="operationRunning"
                        @click="onClick"
                    />
                </div>
                <div>
                    <DlProgressBar
                        label="Progress bar"
                        :value="progressValue"
                        v-bind="{
                            width: '200px',
                            showValue: true,
                            showPercentage: true
                        }"
                        :indeterminate="frameLoadFailed"
                    />
                </div>
            </div>

            <CleaningItem
                v-if="showCleaning && lastUpdated !== 'Error'"
                ref="cleaningItemRef"
                :item-id="exportItemId"
                :dataset-id="datasetId"
                @trigger-refresh="handleEmptystateTrigger"
            />
        </div>
    </DlThemeProvider>
</template>

<script setup lang="ts">
import {
    DlThemeProvider,
    DlTypography,
    DlButton,
    DlProgressBar,
    DlSpinner
} from '@dataloop-ai/components'
import { DlEvent, ThemeType } from '@dataloop-ai/jssdk'
import { ref, onMounted, computed, nextTick } from 'vue-demi'
import { debounce } from 'lodash'
import CleaningItem from './components/CleaningItem.vue'

const contentIframe = ref<HTMLIFrameElement | null>(null)
const isReady = ref<boolean>(false)
const showCleaning = ref<boolean>(false)
const buildReady = ref<boolean>(false)
const currentTheme = ref<ThemeType>(ThemeType.LIGHT)
const lastUpdated = ref<string>('Never')
const operationRunning = ref<boolean>(true)
const buttonLabel = ref<string>('Run')
const progressValue = ref<number>(0)
const datasetId = ref<string>(null)
const projectId = ref<string>(null)
const exportItemId = ref<string>(null)
const frameLoadFailed = ref<boolean>(false)
const cleaningItemRef = ref(null)

function triggerCleaningMethod(data: any) {
    if (cleaningItemRef.value) {
        cleaningItemRef.value.deletedItemsRemove(data) // Call method on the child component
    }
}

const isDark = computed<boolean>(() => {
    return currentTheme.value === ThemeType.DARK
})

const updateStatus = async () => {
    const exportStatus = await fetch(
        `/api/export/status?datasetId=${datasetId.value}`
    )
    if (!exportStatus.ok) {
        throw new Error(`HTTP error! status: ${exportStatus.status}`)
    }
    const data = await exportStatus.json()
    if (Object.keys(data).length === 0) {
        return false
    }

    if (frameLoadFailed.value) {
        frameLoadFailed.value = false
    }
    lastUpdated.value = data.exportDate
    progressValue.value = data.progress / 100
    exportItemId.value = data.exportItemId

    const completed = data.progress === 100
    if (data.status == 'error') {
        console.error('Error fetching feature vectors')
        lastUpdated.value = 'Error'
        progressValue.value = 0
        return true
    }
    return completed
}

const handleEmptystateTrigger = async () => {
    showCleaning.value = false
    operationRunning.value = true
    buttonLabel.value = 'Running'
    progressValue.value = 0
    frameLoadFailed.value = true
    buildReady.value = false
    await pollStatus()
    showCleaning.value = true
}

const handleInitialFrameLoading = async () => {
    buildReady.value = false
    try {
        if (datasetId.value) {
            const existingStatus = await updateStatus()
            if (!existingStatus) {
                await pollStatus()
            }
        } else {
            console.error('No dataset found to fetch feature vectors')
        }
    } catch (e) {
        console.error('Error fetching feature vectors', e)
    }
    buildReady.value = true
    buttonLabel.value = 'Run'
    operationRunning.value = false
    showCleaning.value = true
}

const triggerMainAppLoad = async () => {
    const project = await window.dl.projects.get()
    projectId.value = project?.id ?? null
    const dataset = await window.dl.datasets.get()
    datasetId.value = dataset?.id ?? null

    buttonLabel.value = 'Running'
    operationRunning.value = true
}

onMounted(() => {
    window.dl.on(DlEvent.READY, async () => {
        const settings = await window.dl.settings.get()
        currentTheme.value = settings.theme
        window.dl.on(DlEvent.THEME, (data) => {
            currentTheme.value = data
        })
        window.dl.on('items:deleted', (data) => {
            triggerCleaningMethod(data)
        })
        isReady.value = true

        nextTick(() => {
            triggerMainAppLoad().then(() => {
                nextTick(() => {
                    handleInitialFrameLoading()
                })
            })
        })
        window.dl.sendEvent({
            name: 'dl:items:update:selection',
            payload: []
        })
    })
})

const pollStatus = async () => {
    const interval = 1000
    const maxAttempts = 600 // max 10 minutes
    let attempts = 0

    return new Promise<boolean>((resolve, reject) => {
        const intervalId = setInterval(async () => {
            attempts++
            const completed = await updateStatus()
            if (completed) {
                buildReady.value = true
                buttonLabel.value = 'Run'
                operationRunning.value = false
                clearInterval(intervalId)
                resolve(true)
            } else if (attempts >= maxAttempts) {
                clearInterval(intervalId)
                reject(new Error('Max attempts reached'))
            }
        }, interval)
    })
}

const runDatasetInsightGeneration = async () => {
    showCleaning.value = false
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
    fetch(`/api/export/run?datasetId=${datasetId.value}&timezone=${timezone}`)
    await pollStatus()
    showCleaning.value = true
}

const debouncedRunDatasetInsightGeneration = debounce(
    runDatasetInsightGeneration,
    300
)

const initCleaning = async () => {
    const response = await fetch(`/api/get_items`)
    const clusters = await response.json()
    const images = clusters[0].items
    const selectedIds = [...images]
    const mainItem = clusters[0].main_item

    window.dl.sendEvent({
        name: 'dl:items:update:selection',
        payload: selectedIds
    })
}

async function onClick() {
    operationRunning.value = true
    buttonLabel.value = 'Running'
    progressValue.value = 0
    frameLoadFailed.value = true
    buildReady.value = false

    debouncedRunDatasetInsightGeneration()
}
</script>

<style scoped>
#iframe1 {
    width: 100vw;
    height: 100vh;
}

.container {
    width: 100vw;
    height: 100vh;
    justify-content: center;
    margin: 0%;
}

.container iframe {
    width: 100vh;
    height: 100vh;
}

.loading-spinner {
    display: grid;
    place-items: center;
    height: 100vh;
}

.top-bar {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid var(--dl-color-disabled);
}
</style>
