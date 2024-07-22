<!-- Cleaning.vue -->
<template>
    <div class="thumb-im" role="button" @click="handleClick">
        <div class="image-thumb" :class="{ 'no-annotation': annotated }">
            <DlCheckbox :model-value="props.checked" class="checkbox" />
            <img
                :class="{ checked: props.checked }"
                loading="lazy"
                :src="thumbnail"
                :width="size"
                :height="size"
                @load="fetchItem"
                @error="error_thumbnail"
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
import { DlTypography, DlCheckbox, DlTooltip } from '@dataloop-ai/components'
import { getItem, Item } from './items'
import { defineExpose, defineProps, withDefaults } from 'vue'
import { ref, computed, defineEmits, onUnmounted } from 'vue-demi'
import debounce from './debounce'

const emit = defineEmits(['update:checked', 'main-item-selected', 'delete:item'])

type Props = {
    itemId: string
    checked: boolean
    autoLoad?: boolean
    size?: number
}
const props = withDefaults(defineProps<Props>(), {
    autoLoad: false,
    size: 128
})

const item = ref<Item>(null)
const inView = ref<boolean>(false)
const fetchItem = async () => {
    if ((props.autoLoad || inView.value) && props.itemId !== item.value?.id) {
        const data = getItem(props.itemId)
        if (!data || Object.keys(data).length === 0) {
            emit('delete:item', props.itemId)
        }
        item.value = data
    }
}

const error_thumbnail = () => {
    emit('delete:item', props.itemId)
}

const thumbnail = computed(() => {
    return item.value
        ? item.value.thumbnail
        : props.autoLoad
        ? 'data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==#' +
          Math.random()
        : null
})

const annotated = computed(() => !item.value?.annotated)

const truncateNameWithExtension = (name: string, maxWidth: number) => {
    const extensionMatch = name.match(/\.[^/.]+$/)
    const extension = extensionMatch ? extensionMatch[0] : ''
    const basename = extension ? name.slice(0, -extension.length) : name
    const maxChars = maxWidth / 6

    if (basename && basename.length + extension.length > maxChars) {
        return basename.substring(0, maxChars - extension.length - 3) + '...' + extension
    }
    return name
}

const name = computed(() => {
    if (!item.value?.name) return '\xa0'
    return truncateNameWithExtension(item.value.name, props.size)
})

const fullname = computed(() => item.value?.name)

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

defineExpose({
    inView,
    fetchItem: debounce(fetchItem, 300)
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

.thumb-im img:not([src]) {
    visibility: hidden;
}

.checkbox {
    position: absolute;
    top: 5%;
    left: 5%;
    pointer-events: none;
}

.thumb-im img.checked {
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
