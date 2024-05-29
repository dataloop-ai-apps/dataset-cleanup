<template>
    <div>
        <div v-if="!showProgress" class="base-container">
            <DlIcon
                :icon="icon"
                size="50px"
                color="dl-color-darker"
            />
            <DlTypography class="f20" color="dl-color-darker">{{
                props.text1
            }}</DlTypography>

            <DlTypography class="f14" color="dl-color-medium">{{
                props.text2
            }}</DlTypography>
            <DlTypography v-if="props.text3" class="padb-20 f14" color="dl-color-medium">{{
                props.text3
            }}</DlTypography>

            <DlButton v-if="props.text4" class="padb-20" @click="startExecution">{{
                props.text4
            }}</DlButton>

            <DlTypography v-if="props.text5" color="dl-color-medium">{{
                props.text5
            }}</DlTypography>
            <DlTypography v-if="props.text6" color="dl-color-medium">{{
                props.text6
            }}</DlTypography>
        </div>
        <div v-if="showProgress" class="base-container-f14">
            <DlProgressBar
                :label="props.labelText"
                :value="progress"
                v-bind="{
                    width: '100%',
                    showValue: true,
                    showPercentage: true
                }"
            />
            <DlTypography>
                Status: {{ FrontendStatus[latestStatus] }}
            </DlTypography>
        </div>
    </div>
</template>

<script setup lang="ts">
import {
    DlTypography,
    DlButton,
    DlIcon,
    DlProgressBar
} from '@dataloop-ai/components'
import { defineProps, withDefaults } from 'vue'
import {
    ref,
    onMounted,
    computed,
    defineEmits
} from 'vue-demi'

type Props = {
    icon?: string
    execType?: string
    datasetId?: string
    text1: string
    text2: string
    text3?: string
    text4?: string
    text5?: string
    text6?: string
    labelText?: string
}

const FrontendStatus = {
    created: 'Initializing machine',
    failed: 'Failed',
    'in-progress': 'Extracting embeddings',
    success: 'Extraction completed, loading ...',
    waiting: 'Execution Pending'
}

const emit = defineEmits(['trigger-refresh'])

const status = ref<string>('')
const latestStatus = ref<string>('created')
const progress = ref<number>(0)

const props = withDefaults(defineProps<Props>(), {
    icon: 'icon-dl-project-filled',
    execType: '',
    datasetId: '',
    text3: '',
    text4: '',
    text5: '',
    text6: '',
    labelText: ''
})

const showProgress = computed(() => {
    return status.value === 'running'
})

onMounted(async () => {
    if (!props.execType) return;
    const response = await fetch(
        `/api/get_execution_status?datasetId=${props.datasetId}&exec_type=${props.execType}`
    )
    const result = await response.json()
    status.value = result.status
    progress.value = 0
    latestStatus.value = result.full_status
    if (status.value === 'running') {
        await pollStatus()
    }
})

const startExecution = async () => {
    const response = await fetch(
        `/api/start_execution?datasetId=${props.datasetId}&exec_type=${props.execType}`
    )
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
    }
    status.value = 'running'
    latestStatus.value = 'waiting'
    await pollStatus()
}

const pollStatus = async () => {
    const interval = 1000
    const maxAttempts = 600 // max 10 minutes
    let attempts = 0

    return new Promise<boolean>((resolve, reject) => {
        const intervalId = setInterval(async () => {
            attempts++
            const completed = await updateStatus()
            if (completed) {
                clearInterval(intervalId)
                resolve(true)
            } else if (attempts >= maxAttempts) {
                clearInterval(intervalId)
                reject(new Error('Max attempts reached'))
            }
        }, interval)
    })
}

const updateStatus = async () => {
    const exportStatus = await fetch(
        `/api/get_execution_status?datasetId=${props.datasetId}&exec_type=${props.execType}`
    )
    if (!exportStatus.ok) {
        throw new Error(`HTTP error! status: ${exportStatus.status}`)
    }
    const data = await exportStatus.json()
    if (Object.keys(data).length === 0) {
        return false
    }

    progress.value = data.progress / 100
    latestStatus.value = data.full_status

    const completed = data.progress === 100
    if (data.status == 'error') {
        console.error('Error fetching feature vectors')
        status.value = 'error'
        window.dl.sendEvent({
            name: 'app:toastMessage',
            payload: {
                message:
                    'Failed to run the CLIP model - check machine availability and service status. You may try to rerun the execution.',
                type: 'error'
            }
        })
        return true
    }
    if (completed) {
        setInterval(() => {
            status.value = 'completed'
            emit('trigger-refresh')
        }, 1000)
    }
    return completed
}
</script>

<style scoped>
.base-container {
    height: calc(100vh - 105px);
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}

.base-container-f14 {
    height: calc(100vh - 105px);
    display: flex;
    justify-content: center;
    align-items: start;
    flex-direction: column;
    font-size: 14px;
    width: 75%;
    margin: auto;
}
.padb-20 {
    padding-bottom: 20px;
}
.f20 {
    font-size: 20px;
    font-weight: 500;
    margin-top: 10px;
    text-transform: capitalize;
}

.f14 {
    font-size: 14px;
}

.small-text {
    font-size: 14px;
    color: var(--dl-color-darker);
    margin-top: 5px;
}
</style>
