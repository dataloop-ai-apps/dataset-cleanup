<!-- Cleaning.vue -->
<template>
    <div class="thumb-im" role="button" @click="handleClick">
        <div class="image-thumb" :class="{ 'no-annotation': !item?.annotated }">
            <DlCheckbox
                v-if="checked"
                :model-value="props.checked"
                class="checkbox"
            />
            <img
                :class="{ checked: checked, mainchecked: props.mainChecked }"
                :src="thumbnail"
                loading="lazy"
                :width="128"
                :height="128"
            />
        </div>

        <div>
            <DlTypography :variant="'h6'"
            >{{ name }}
                <DlTooltip> {{ fullname }} </DlTooltip>
            </DlTypography>
        </div>
    </div>
</template>

<script setup lang="ts">
import {
    DlSelect,
    DlTypography,
    DlSlider,
    DlButton,
    DlCheckbox,
    DlTooltip
} from '@dataloop-ai/components'
import { SDKItem } from '@dataloop-ai/jssdk'
import { defineProps, withDefaults, watch } from 'vue'
import {
    ref,
    onMounted,
    computed,
    nextTick,
    defineEmits,
    onUnmounted
} from 'vue-demi'

const emit = defineEmits([
    'update:checked',
    'main-item-selected',
    'delete:item'
])

type Props = {
    itemId: string
    checked: boolean
    mainChecked: boolean
}
const props = withDefaults(defineProps<Props>(), {
    mainChecked: false
})

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const item = ref<SDKItem | null>(null)
const thumbnail = computed(() => item.value?.thumbnail)

const truncateNameWithExtension = (name: string, maxWidth: number) => {
    const extensionMatch = name.match(/\.[^/.]+$/)
    const extension = extensionMatch ? extensionMatch[0] : ''
    const basename = extension ? name.slice(0, -extension.length) : name
    const maxChars = maxWidth / 6

    if (basename.length + extension.length > maxChars) {
        return (
            basename.substring(0, maxChars - extension.length - 3) +
            '...' +
            extension
        )
    }
    return name
}

const name = computed(() => {
    if (!item.value?.name) return ''
    return truncateNameWithExtension(item.value.name, 128)
})

const fullname = computed(() => item.value?.name)

const fetchSDKItem = async (itemId: string, attempts = 3) => {
    try {
        const data = await window.dl.items.get(itemId)
        if (Object.keys(data).length === 0) {
            emit('delete:item', itemId)
        }
        item.value = data
    } catch (error) {
        if (attempts > 1) {
            await delay(400)
            await fetchSDKItem(itemId, attempts - 1)
        } else {
            console.error('Error fetching item', error)
        }
    }
}

// Watch for changes in itemId and refetch the item data
watch(
    () => props.itemId,
    async (newItemId) => {
        await fetchSDKItem(newItemId)
    },
    { immediate: true }
)

const clickTimer = ref<number | null>(null)
const clickCount = ref(0)

const handleClick = () => {
    clickCount.value += 1

    if (clickTimer.value === null) {
        clickTimer.value = setTimeout(() => {
            if (clickCount.value === 1) {
                // Single Click Action
                emit('update:checked', !props.checked)
                emit('main-item-selected', props.itemId)
            } else if (clickCount.value === 2) {
                window.dl.navigator.studio(
                    { itemId: props.itemId, datasetId: item.value?.datasetId },
                    { newTab: true }
                )
            }
            clickCount.value = 0
            if (clickTimer.value !== null) {
                clearTimeout(clickTimer.value)
                clickTimer.value = null
            }
        }, 200) as unknown as number
    }
}

onUnmounted(() => {
    if (clickTimer.value !== null) {
        clearTimeout(clickTimer.value)
        clickTimer.value = null
    }
})
</script>

<style scoped>
.thumb-im {
    position: relative;
    margin-right: 20px;
    margin-bottom: 20px;
}

.thumb-im div {
    text-align: center;
}
.thumb-im img:hover {
    border: 2px solid var(--dl-color-secondary);
}

.thumb-im img {
    border: 2px solid var(--dl-color-separator);
}

.checkbox {
    position: absolute;
    top: 5%;
    left: 5%;
}

.thumb-im img.checked {
    border: 2px solid var(--dl-color-secondary);
}

.thumb-im img.mainchecked {
    border: 2px solid var(--dl-color-secondary);
}
.image-thumb {
    position: relative;
    display: inline-block;
}

.image-thumb::after {
    content: '';
    position: absolute;
    left: 2px;
    right: 2px;
    bottom: 2px;
    height: 6px;
    background-color: var(--dl-color-positive);
}

.image-thumb.no-annotation::after {
    display: none;
}
</style>
