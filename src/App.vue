<template>
    <DlThemeProvider :is-dark="isDark">
        <div v-if="!isReady" class="loading-spinner">
            <DlSpinner text="Loading App..." size="128px" />
        </div>
        <div v-else>
            <CleaningItem
                v-if="datasetId"
                ref="cleaningItemRef"
                :dataset-id="datasetId"
                :last-updated="lastUpdated"
                :progress="progressValue"
                @trigger-refresh="handleEmptystateTrigger"
                @trigger-reload="handleReload"
            />
        </div>
    </DlThemeProvider>
</template>

<script setup lang="ts">
import { DlThemeProvider, DlSpinner } from '@dataloop-ai/components'
import { DlEvent, ThemeType } from '@dataloop-ai/jssdk'
import { ref, onMounted, computed, nextTick } from 'vue-demi'
import CleaningItem from './components/CleaningItem.vue'

const contentIframe = ref<HTMLIFrameElement | null>(null)
const isReady = ref<boolean>(false)
const buildReady = ref<boolean>(false)
const currentTheme = ref<ThemeType>(ThemeType.LIGHT)
const lastUpdated = ref<string>('Never')
const operationRunning = ref<boolean>(true)
const progressValue = ref<number>(0)
const datasetId = ref<string>(null)
const projectId = ref<string>(null)
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
    const exportStatus = await fetch(`/api/export/status?datasetId=${datasetId.value}`)
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

    const completed = data.progress === 100
    if (data.status == 'error') {
        console.error('Error fetching feature vectors')
        lastUpdated.value = 'Error'
        progressValue.value = 1
        return true
    }
    return completed
}

const handleEmptystateTrigger = async () => {
    operationRunning.value = true
    progressValue.value = 0
    frameLoadFailed.value = true
    buildReady.value = false
    await pollStatus()
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
    operationRunning.value = false
}

const triggerMainAppLoad = async () => {
    const project = await window.dl.projects.get()
    projectId.value = project?.id ?? null
    const dataset = await window.dl.datasets.get()
    datasetId.value = dataset?.id ?? null

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

const pollStatus = async (interval = 1000, maxAttempts = 600) => {
    let attempts = 0

    const checkStatus = async () => {
        attempts++
        const completed = await updateStatus()

        if (completed || attempts >= maxAttempts) {
            buildReady.value = true
            operationRunning.value = false
            if (cleaningItemRef.value) {
                cleaningItemRef.value.reset()
            }
            return true
        }
        return false
    }

    for (; attempts < maxAttempts; attempts++) {
        if (await checkStatus()) break
        await new Promise((resolve) => setTimeout(resolve, interval))
    }

    if (attempts >= maxAttempts) {
        console.log('Max attempts reached, exiting pollStatus')
    }
}

const handleReload = async () => {
    operationRunning.value = true
    progressValue.value = 0
    frameLoadFailed.value = true
    buildReady.value = false

    progressValue.value = 0
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
    fetch(`/api/export/run?datasetId=${datasetId.value}&timezone=${timezone}`)
    await pollStatus()
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
