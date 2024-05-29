<!-- Cleaning.vue -->
<template>
    <div v-if="mounted">
        <div class="flex-container">
            <DlSelect
                v-model="selected"
                :options="options"
                :disabled="selectedType !== 'Similarity'"
                width="25%"
                @change="SelectedChange"
            />
            <DlSelect
                v-model="selectedType"
                :options="types"
                width="25%"
                @change="SelectedTypeChange"
            />
            <DlSlider
                v-model="similarity"
                :class="{ invisible: selectedType !== 'Similarity' }"
                class="slider"
                text="Similarity"
                :min="0.001"
                :max="0.15"
                :step="0.001"
            />

            <DlRange
                v-model="minmax"
                class="range"
                :class="{ invisible: selectedType == 'Similarity' }"
                :text="selectedType"
                :min="0"
                :max="1"
                :step="0.01"
                width="100%"
            />

            <DlButton :disabled="isDisabled" @click="getImages">Apply</DlButton>

            <ReloadProgress
                :last-updated="lastUpdated"
                :progress="progress"
                @reload="triggerReload"
            />
        </div>
        <div v-if="loading" class="loading">
            <DlSpinner text="Loading, please wait..." size="60px" />
        </div>

        <div v-if="!loading && showMainContent && selectedType == 'Similarity'">
            <EmptyState v-if="(options.length > 0) && (noEmptyClusters.length === 0)"
                icon="icon-dl-item-filled"
                text1="No results were found for the selected filters"
                text2="Try to filter different options to find what you’re looking for"
            />
            <div v-else-if="options.length > 0">
                <div class="select-all">
                    <DlChip
                        class="sorting-chip"
                        clickable
                        color="dl-color-bg"
                        :icon="sortDirection ? 'icon-dl-arrow-up' : 'icon-dl-arrow-down'"
                        max-width="110px"
                        text-color="dl-color-medium"
                        @click="toggleSortDirection"
                    >Sort by: similarities</DlChip>
                    <DlCheckbox
                        v-model="SelectAll"
                        true-value="all"
                        false-value="none"
                        indeterminate-value="some"
                        class="checkbox-all"
                        label="Select All"
                    />
                    <DlChip
                        color="dl-color-bg"
                        text-color="dl-color-medium"
                        max-width="250px"
                        :label="
                            AllItemsCount +
                                ' item' +
                                (AllItemsCount > 1 ? 's' : '')
                        "
                    />
                    <DlIcon
                        v-if="selectedIds.length > 0"
                        icon="icon-dl-right-chevron"
                        size="20px"
                    />

                    <DlChip
                        v-if="selectedIds.length > 0"
                        color="#32766E"
                        max-width="250px"
                        :removable="true"
                        :label="
                            'Selected ' +
                                selectedIds.length +
                                ' item' +
                                (selectedIds.length > 1 ? 's' : '')
                        "
                        @remove="removeSelected"
                    />
                </div>
                <div class="actions">
                    <div class="left-pannel scroll" @scroll="handleScroll">
                        <div
                            v-for="cluster in noEmptyClusters"
                            :key="cluster.key"
                        >
                            <div class="main-image">
                                <ItemThumbnailImage
                                    :item-id="cluster.main_item"
                                    :checked="false"
                                    :size="72"
                                    @main-item-selected="
                                        handleCheckedUpdateMain(
                                            cluster.key,
                                            allChecked[cluster.key] === 'all'
                                                ? 'uncheck'
                                                : 'check'
                                        )
                                    "
                                />
                                <DlCheckbox
                                    v-model="allChecked[cluster.key]"
                                    true-value="all"
                                    false-value="none"
                                    indeterminate-value="some"
                                    class="checkbox"
                                    @checked="
                                        handleCheckedUpdateMain(
                                            cluster.key,
                                            'check'
                                        )
                                    "
                                    @unchecked="
                                        handleCheckedUpdateMain(
                                            cluster.key,
                                            'uncheck'
                                        )
                                    "
                                />
                            </div>
                        </div>
                    </div>
                    <div class="right-pannel">
                        <div class="right-pannel-inner scroll">
                            <div
                                v-for="(id, index) in images"
                                :key="index + '-' + id"
                            >
                                <ItemThumbnailImage
                                    :item-id="id"
                                    :checked="selectedIds.includes(id)"
                                    :main-checked="false"
                                    :size="thumbSize"
                                    @update:checked="handleCheckedUpdate(id)"
                                    @delete:item="deleteItem(id)"
                                />
                            </div>
                        </div>
                        <dl-slider
                            v-model="thumbSize"
                            class="thumb-size"
                            :min="72"
                            :max="268"
                            :step="28"
                            style="white-space: nowrap"
                            text="Thumb size"
                            slim
                        />
                    </div>
                </div>
            </div>
            <div v-if="options.length == 0">
                <EmptyState
                    :dataset-id="props.datasetId"
                    exec-type="clip"
                    text1="No Embeddings In Dataset"
                    text2="Install one or more models to create a feature-set and populate with embeddings data."
                    text3="The models need to have a trigger on every item-created event to allow full coverage."
                    text4="Add CLIP Embeddings"
                    text5="This will spin up a high-memory machine to execute CLIP model for extracting embeddings from all items in the dataset."
                    text6="Ensure the high-memory machine is available in your project's catalogue."
                    label-text="Adding Embeddings..."
                    @trigger-refresh="triggerRefresh"
                />
            </div>
        </div>
        <div v-if="!loading && showMainContent && selectedType !== 'Similarity'">
            <EmptyState v-if="(qualityCount > 0) && (coruptedImagesLength === 0)"
                icon="icon-dl-item-filled"
                text1="No results were found for the selected filters"
                text2="Try to filter different options to find what you’re looking for"
            />
            <div v-else-if="qualityCount > 0">
                <div class="select-all">
                    <DlCheckbox
                        v-model="SelectAllCorupted"
                        class="checkbox-all"
                        label="Select All"
                    />
                    <DlChip
                        color="dl-color-bg"
                        text-color="dl-color-medium"
                        max-width="250px"
                        :label="
                            AllItemsCountCorupted +
                                ' item' +
                                (AllItemsCountCorupted > 1 ? 's' : '')
                        "
                    />
                    <DlIcon
                        v-if="selectedIds.length > 0"
                        icon="icon-dl-right-chevron"
                        size="20px"
                    />

                    <DlChip
                        v-if="selectedIds.length > 0"
                        color="#32766E"
                        max-width="250px"
                        :removable="true"
                        :label="
                            'Selected ' +
                                selectedIds.length +
                                ' item' +
                                (selectedIds.length > 1 ? 's' : '')
                        "
                        @remove="removeSelected"
                    />
                </div>
                <div class="whole-pannel scroll">
                    <div
                        v-for="(id, index) in visibleCoruptedImages"
                        :key="index + '-' + id"
                    >
                        <ItemThumbnailImage
                            :item-id="id"
                            :checked="selectedIds.includes(id)"
                            :main-checked="false"
                            @update:checked="handleCheckedUpdate(id)"
                            @delete:item="deleteItemCorupted(id)"
                        />
                    </div>
                </div>
                <DlPagination
                    v-model="coruptPage"
                    class="paginatio-whole"
                    :total-items="coruptedImagesLength"
                    :rows-per-page="rowsPerPage"
                    :boundary-links="true"
                    :boundary-numbers="true"
                    :direction-links="true"
                    :with-quick-navigation="true"
                    :with-rows-per-page="true"
                    :with-legend="true"
                    @update:rows-per-page="updateRowsPerPage"
                />
            </div>
            <div v-if="qualityCount == 0">
                <EmptyState
                    :dataset-id="props.datasetId"
                    exec-type="quality-score-generator"
                    text1="No Quality Score In Dataset"
                    text2="Install app to add a quality score into metadata."
                    text3="The app need to have a trigger on every item-created event to allow full coverage."
                    text4="Add Quality Scores Generator"
                    text5="This will spin up a high-memory machine to execute Quality Scores Generator for all items in the dataset."
                    text6="Ensure the high-memory machine is available in your project's catalogue."
                    label-text="Adding Metadata..."
                    @trigger-refresh="checkMetadata"
                />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, onBeforeMount } from 'vue'
import {
    DlSelect,
    DlSpinner,
    DlSlider,
    DlButton,
    DlCheckbox,
    DlPagination,
    DlRange,
    DlChip,
    DlIcon
} from '@dataloop-ai/components'
import ItemThumbnailImage from './ItemThumbnailImage.vue'
import EmptyState from './EmptyState.vue'
import ReloadProgress from './ReloadProgress.vue'
import {
    ref,
    computed,
    nextTick,
    defineExpose,
    defineEmits
} from 'vue-demi'
const options = ref([])
const selected = ref('feature set 1')
const types = ref(['Similarity', 'Darkness', 'Blurriness'])
const selectedType = ref('Similarity')
const similarity = ref(0.01)
const minmax = ref({ min: 0, max: 0.1 })
const coruptedImages = ref<string[]>([])
const featureSetDict = ref({})
const datasetItemsCount = ref(0)

const loading = ref(false)
const mounted = ref(false)
const qualityCount = ref(0)
type Cluster = {
    key: string
    main_item: string
    items: string[] // assuming each item is identified by a string ID
}
const emit = defineEmits(['trigger-reload', 'trigger-refresh'])

type Props = {
    datasetId: string
    lastUpdated: string
    progress: number
}

const showMainContent = computed(() => {
    return (props.lastUpdated !== 'Never') && (props.lastUpdated !== 'Error') && (props.progress === 1)
})

const coruptedImagesLength = computed(() => {
    return coruptedImages.value.length
})

defineExpose({
    deletedItemsRemove,
    reset
})

const noEmptyClusters = computed(() => {
    return clusters.value.filter((cluster) => cluster.main_item !== '')
})

const triggerRefresh = () => {
    emit('trigger-refresh')
}

const triggerReload = () => {
    emit('trigger-reload')
}

const checkMetadata = async () => {
    const response = await fetch(
        `/api/get_quality_score_exist?datasetId=${props.datasetId}`
    )
    qualityCount.value = await response.json()
}

const props = defineProps<Props>()

const thumbSize = ref(128)

const coruptPage = ref(1)

const rowsPerPage = ref(25)

const AllItemsCount = computed(() => {
    return clustersAll.value.reduce((acc, cluster) => {
        acc += cluster.items.length
        return acc
    }, 0)
})

const AllItemsCountCorupted = computed(() => {
    return coruptedImages.value.length
})

const isDisabled = computed(() => {
    return (
        ((options.value.length === 0 || loading.value) &&
            selectedType.value === 'Similarity') ||
        (qualityCount.value === 0 && selectedType.value !== 'Similarity')
    )
})

const clusters = ref<Cluster[]>([])

const clustersAll = ref<Cluster[]>([])

const selectedIds = ref<string[]>([])

const images = computed(() => {
    const ids: string[] = []
    for (const cluster of clusters.value) {
        ids.push.apply(ids, cluster.items)
    }
    return ids
})

const allChecked = computed({
    get: function() {
        const checkboxes: { [key: string]: string } = {}
        const isSelected = function (id: string) { return selectedIds.value.includes(id) }
        for (const cluster of clusters.value) {
            checkboxes[cluster.key] = cluster.items.every(isSelected) ? 'all' : (
                cluster.items.some(isSelected) ? 'some' : 'none'
            )
        }
        return checkboxes
    },
    set: function() {}
})

const SelectAll = computed({
    get: () => {
        if (selectedIds.value.length === 0) {
            return 'none'
        }
        return clustersAll.value.every((cluster) =>
            cluster.items.every((id) => selectedIds.value.includes(id))
        ) ? 'all' : 'some'
    },
    set: (value) => {
        if (value === 'all') {
            clustersAll.value.forEach((cluster) => {
                cluster.items.forEach((id) => {
                    if (!selectedIds.value.includes(id)) {
                        selectedIds.value.push(id)
                    }
                })
            })
        } else {
            selectedIds.value = []
        }
        updateSelection()
    }
})

const SelectAllCorupted = computed({
    get: () => {
        if (selectedIds.value.length === 0) {
            return false
        }
        return coruptedImages.value.every((id) =>
            selectedIds.value.includes(id)
        )
    },
    set: (value) => {
        if (value) {
            coruptedImages.value.forEach((id) => {
                if (!selectedIds.value.includes(id)) {
                    selectedIds.value.push(id)
                }
            })
        } else {
            selectedIds.value = []
        }
        updateSelection()
    }
})

const handleScroll = (event: Event) => {
    const { scrollTop, clientHeight, scrollHeight } = event.target
    const nearBottom = scrollHeight - (scrollTop + clientHeight) < 25
    if (nearBottom && clusters.value.length < clustersAll.value.length) {
        clusters.value = clustersAll.value.slice(0, clusters.value.length + 10)
    }
}

const SelectedTypeChange = async () => {
    selectedIds.value = []
    coruptedImages.value = []
    await nextTick()
    updateSelection()
    if (
        selectedType.value !== 'Similarity' &&
        qualityCount.value !== datasetItemsCount.value &&
        qualityCount.value !== 0
    ) {
        sendToastMassage(
            'Not all items have quality score. Please add quality score to all items for better results',
            'warning'
        )
    }
}

const timeoutId = ref<number | null>(null)

function debounce(func, wait) {
    return function (...args: any[]) {
        if (timeoutId.value) {
            clearTimeout(timeoutId.value) // Clear the existing timeout
        }
        timeoutId.value = setTimeout(() => {
            func(...args)
            timeoutId.value = null // Reset the timeoutId after execution
        }, wait) as unknown as number
    }
}

const visibleCoruptedImages = computed(() => {
    const start = (coruptPage.value - 1) * rowsPerPage.value
    const end = start + rowsPerPage.value
    return coruptedImages.value.slice(start, end)
})

const removeSelected = () => {
    selectedIds.value = []
    updateSelection()
}
const deleteItem = (itemId: string) => {
    const index = selectedIds.value.indexOf(itemId)
    if (index !== -1) {
        selectedIds.value.splice(index, 1)
    }
    // delete from clusters
    clustersAll.value.forEach((cluster) => {
        const index = cluster.items.indexOf(itemId)
        if (index !== -1) {
            cluster.items.splice(index, 1)
        }
    })
    updateSelection()
}

const deleteItemCorupted = (itemId: string) => {
    const index = selectedIds.value.indexOf(itemId)
    if (index !== -1) {
        selectedIds.value.splice(index, 1)
    }
    coruptedImages.value = coruptedImages.value.filter((id) => id !== itemId)
    updateSelection()
}

function deletedItemsRemove(data: any) {
    data.itemIds.forEach((itemId) => {
        deleteItem(itemId)
        deleteItemCorupted(itemId)
    })
}

const handleCheckedUpdateMain = async (key: string, action: string) => {
    const index = clustersAll.value.findIndex((cluster) => cluster.key === key)
    if (index === -1) return
    if (action === 'check') {
        clustersAll.value[index].items.forEach((id) => {
            if (!selectedIds.value.includes(id)) {
                selectedIds.value.push(id)
            }
        })
    } else {
        clustersAll.value[index].items.forEach((id) => {
            const index = selectedIds.value.indexOf(id)
            if (index !== -1) {
                selectedIds.value.splice(index, 1)
            }
        })
    }
    await nextTick()
    updateSelection()
}

const handleCheckedUpdate = async (itemId: string) => {
    const index = selectedIds.value.indexOf(itemId)
    if (index === -1) {
        selectedIds.value.push(itemId)
    } else {
        selectedIds.value.splice(index, 1)
    }
    await nextTick()
    updateSelection()
}

const updateSelection = () => {
    window.dl.sendEvent({
        name: 'dl:items:update:selection',
        payload: selectedIds.value
    })
}

const getImages = debounce(async () => {
    if (loading.value) return // Prevent function from running if it's already loading
    loading.value = true
    if (selectedType.value === 'Similarity') {
        const response = await fetch(
            `/api/get_items?datasetId=${props.datasetId}&featureSetName=${selected.value}&type=${selectedType.value}&similarity=${similarity.value}`
        )
        clustersAll.value = await response.json()
        clusters.value = clustersAll.value.slice(0, 10)
        selectedIds.value = [...clusters.value[0].items]
        await nextTick()
    } else {
        coruptPage.value = 1
        await fetchCoruptedImages()
        selectedIds.value = []
    }
    updateSelection()
    loading.value = false
}, 300)

const updateRowsPerPage = (value: number) => {
    rowsPerPage.value = value
    coruptPage.value = 1
}

const fetchCoruptedImages = async () => {
    const response = await fetch(
        `/api/get_items?datasetId=${props.datasetId}&featureSetName=${
            selected.value
        }&type=${selectedType.value}&similarity=${
            similarity.value
        }&pagination=${coruptPage.value - 1}&limit=${rowsPerPage.value}&min_v=${
            minmax.value.min
        }&max_v=${minmax.value.max}`
    )
    const result = await response.json()
    coruptedImages.value = result.items
}

async function reset() {
    coruptPage.value = 1
    clustersAll.value = []
    clusters.value = []
    selectedIds.value = []

    const feature_sets = await fetch(
        `/api/available_feature_sets?datasetId=${props.datasetId}`
    )
    const response = await feature_sets.json()
    featureSetDict.value = response
    options.value = Object.keys(response)
    await checkMetadata()
    selected.value = options.value[0]
}

onBeforeMount(async () => {
    await reset()
    mounted.value = true
    datasetItemsCount.value = (await window.dl.datasets.get()).itemsCount
    if (
        datasetItemsCount.value != featureSetDict.value[selected.value] &&
        options.value.length > 0
    ) {
        sendToastMassage(
            'For selected feature set, number of items in dataset is not equal to number of items in feature set. Please rerun the feature vector extraction',
            'warning'
        )
    }
})

const sendToastMassage = (message_text: string, type_text: string) => {
    window.dl.sendEvent({
        name: 'app:toastMessage',
        payload: {
            message: message_text,
            type: type_text
        }
    })
}

const SelectedChange = () => {
    if (datasetItemsCount.value != featureSetDict.value[selected.value]) {
        sendToastMassage(
            'For selected feature set, number of items in dataset is not equal to number of items in feature set. Please rerun the feature vector extraction',
            'warning'
        )
    }
}


const sortDirection = ref<boolean>(false)

const sortFunction = function (a: Cluster, b: Cluster):number {
    const direction = sortDirection.value ? 1 : -1;
    if (a.items.length > b.items.length) return direction;
    if (a.items.length < b.items.length) return -direction;
    return 0;
}

const toggleSortDirection = () => {
    sortDirection.value = !sortDirection.value
    clustersAll.value.sort(sortFunction)
    clusters.value = clustersAll.value.slice(0, clusters.value.length)
}

</script>

<style scoped>
.flex-container {
    display: flex; /* Establishes the flex container */
    justify-content: space-between;
    align-items: center; /* Vertically centers the items in the container */
    padding-bottom: 10px;
    border-bottom: 1px solid var(--dl-color-disabled);
}

.slider {
    width: 20%;
    display: block;
}
.slider :deep(#slider-input) {
    width: 50px;
}
/* undo bootstrap style */
.slider :deep(.header .row.text) {
    margin-left: 0;
}
.actions {
    display: flex;
}

.range {
    width: 20%;
    flex-direction: column;
}

.range :deep(.header) {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    height: 20px;
}

.range :deep(.header .right-container) {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.range :deep(.header .right-container .value-container) {
    padding-left: 10px;
    padding-top: 3px;
    min-width: 38px;
    text-align: right;
}
/* override hardcoded button text size in dl-range */
.range :deep(.dl-button-container) {
    --dl-button-font-size: 12px !important;
}


.loading {
    display: grid; /* Use the grid layout */
    place-items: center; /* Center items both horizontally and vertically */
    height: 100vh; /* Full viewport height to ensure centering is relative to the entire screen */
    width: 100vw; /* Full viewport width, necessary if your spinner is absolute or fixed positioned */
}
.left-pannel {
    min-width: 110px;
    overflow-y: auto;
    height: calc(100vh - 80px);
}
.right-pannel {
    border-left: 1px solid var(--dl-color-disabled);
    display: flex; flex-direction: column; flex-grow: 1;
}
.right-pannel-inner {
    display: flex;
    width: 100%;
    flex-wrap: wrap;
    overflow-y: auto;
    align-content: flex-start;
    justify-content: flex-start;
    padding-left: 30px;
    padding-top: 12px;
    height: calc(100vh - 80px - 20px); /* 20px for thumbs slider */
}

.right-pannel .thumb-size {
    width: 200px; padding-left: 30px;
}

.pagination :deep(.dl-pagination--container) {
    border-left: 1px solid var(--dl-color-disabled);
    padding-left: 5px;
    padding-right: 10px;
    margin-left: 5px;
}

.pagination-whole :deep(.dl-pagination--container) {
    padding-left: 5px;
    padding-right: 10px;
    margin-left: 5px;
}

.whole-pannel {
    margin-top: 10px;
    display: flex;
    flex-wrap: wrap;
    overflow-y: auto;
    align-content: flex-start;
    justify-content: flex-start;
    height: calc(100vh - 80px - 40px); /* 40px for pagination */
    overflow-y: auto;
}

.main-image {
    display: flex;
    padding-top: 12px;
}
/*
.main-image:hover {
    background-color: var(--dl-color-fill);
}
*/
.main-image :deep(.thumb-im) {
    margin-right: 8px;
}


.checkbox {
    justify-content: center;
    margin-right: 5px;
    transform: translateY(-15px);
}

.invisible {
    display: none;
}

.select-all {
    display: flex;
    justify-content: flex-start;
    min-height: 28px;
    border-bottom: 1px solid var(--dl-color-disabled);
    align-items: center;
}
.select-all .sorting-chip {
    font-size: 10px;
    min-width: 110px;
    flex-direction: row-reverse;
    user-select: none;
}
.select-all .sorting-chip :deep(.dl-chip-left-icon-container) {
    position: inherit;
}

.checkbox-all {
    padding-right: 15px;
    padding-left: 5px;
}
</style>
