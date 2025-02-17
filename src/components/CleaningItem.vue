<!-- Cleaning.vue -->
<template>
    <div v-if="mounted">
        <div class="flex-container">
            <DlSelect
                v-model="selected"
                :options="options"
                :disabled="['Darkness/Brightness', 'Blurriness/Sharpness'].includes(selectedType)"
                width="25%"
                @change="SelectedChange"
            />
            <DlSelect
                v-model="selectedType"
                :options="types"
                width="25%"
                @change="SelectedTypeChange"
            />

            <div v-if="selectedType == 'Similarity'" class="range-all">
                <DlSlider
                    v-model="similarity"
                    class="slider w-100-120px"
                    text="Similarity"
                    :min="0.001"
                    :max="0.3"
                    :step="0.001"
                />

                <DlSelect
                    v-model="minClusterSize"
                    class="select-s"
                    :options="clusterSizes"
                    size="m"
                    title="Size"
                    tooltip="Minimal Cluster size"
                    width="80px"
                />
            </div>

            <DlSlider
                v-model="anomality"
                :class="{ invisible: selectedType !== 'Anomalies' }"
                class="slider w-20"
                text="Minimal Distance"
                :min="0.5"
                :max="1"
                :step="0.001"
            />

            <DlRange
                v-model="minmax"
                class="range"
                :class="{
                    invisible: selectedType == 'Similarity' || selectedType == 'Anomalies'
                }"
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

        <div
            v-if="
                !loading && showMainContent && selectedType == 'Similarity' && props.progress == 1
            "
        >
            <EmptyState
                v-if="options.length > 0 && noEmptyClusters.length === 0"
                icon="icon-dl-item-filled"
                text1="No results were found for the selected filters"
                text2="Try to filter different options to find what you're looking for"
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
                    >Sort by: similarities</DlChip
                    >
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
                        :label="AllItemsCount + ' item' + (AllItemsCount > 1 ? 's' : '')"
                    />
                    <DlIcon v-if="selectedIds.size > 0" icon="icon-dl-right-chevron" size="20px" />

                    <DlChip
                        v-if="selectedIds.size > 0"
                        color="#32766E"
                        max-width="250px"
                        :removable="true"
                        :label="
                            'Selected ' +
                                selectedIds.size +
                                ' item' +
                                (selectedIds.size > 1 ? 's' : '')
                        "
                        @remove="removeSelected"
                    />
                </div>
                <div class="actions">
                    <div class="left-pannel scroll" @scrollend="handleLeftSideScroll">
                        <div
                            v-for="cluster in noEmptyClusters"
                            :key="cluster.key"
                            class="main-image"
                            :data-main="cluster.main_item"
                        >
                            <ItemThumbnailImage
                                ref="leftSideThumbs"
                                :item-id="cluster.main_item"
                                :checked="false"
                                :size="72"
                                @main-item-selected="
                                    handleLeftSideClick(cluster.key, cluster.main_item)
                                "
                            />
                            <DlCheckbox
                                v-model="allChecked[cluster.key]"
                                true-value="all"
                                false-value="none"
                                indeterminate-value="some"
                                class="checkbox"
                                @checked="handleCheckedUpdateMain(cluster.key, 'check')"
                                @unchecked="handleCheckedUpdateMain(cluster.key, 'uncheck')"
                            />
                        </div>
                    </div>
                    <div class="right-pannel">
                        <div class="right-pannel-inner scroll" @scrollend="handleRightSideScroll">
                            <ItemThumbnailImage
                                v-for="id in images"
                                ref="rightSideThumbs"
                                :key="id"
                                :data-main="first2main[id]"
                                :item-id="id"
                                :checked="selectedIds.has(id)"
                                :size="thumbSize"
                                @update:checked="handleCheckedUpdate(id)"
                                @delete:item="deleteItem(id)"
                            />
                        </div>
                        <div class="pagination-controls">
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

                            <DlPagination
                                v-model="similarityPage"
                                class="paginatio-whole"
                                :total-items="AllItemsCount"
                                :rows-per-page="similarityRowsPerPage"
                                :boundary-links="true"
                                :boundary-numbers="true"
                                :direction-links="true"
                                :with-quick-navigation="true"
                                @update:model-value="rightPannelScrollToTop"
                            />
                        </div>
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
        <div
            v-if="
                !loading && showMainContent && selectedType !== 'Similarity' && props.progress == 1
            "
        >
            <EmptyState
                v-if="qualityCount > 0 && coruptedImagesLength === 0"
                icon="icon-dl-item-filled"
                text1="No results were found for the selected filters"
                text2="Try to filter different options to find what you're looking for"
            />
            <div
                v-else-if="qualityCount > 0 || (selectedType == 'Anomalies' && options.length > 0)"
            >
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
                            AllItemsCountCorupted + ' item' + (AllItemsCountCorupted > 1 ? 's' : '')
                        "
                    />
                    <DlIcon v-if="selectedIds.size > 0" icon="icon-dl-right-chevron" size="20px" />

                    <DlChip
                        v-if="selectedIds.size > 0"
                        color="#32766E"
                        max-width="250px"
                        :removable="true"
                        :label="
                            'Selected ' +
                                selectedIds.size +
                                ' item' +
                                (selectedIds.size > 1 ? 's' : '')
                        "
                        @remove="removeSelected"
                    />
                </div>
                <div class="whole-pannel scroll">
                    <ItemThumbnailImage
                        v-for="id in visibleCoruptedImages"
                        :key="id"
                        auto-load
                        :item-id="id"
                        :checked="selectedIds.has(id)"
                        @update:checked="handleCheckedUpdate(id)"
                        @delete:item="deleteItemCorupted(id)"
                    />
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
                    v-if="
                        selectedType == 'Darkness/Brightness' ||
                            selectedType == 'Blurriness/Sharpness'
                    "
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
import { ref, computed, nextTick, defineExpose, defineEmits } from 'vue-demi'
import debounce from './debounce'
import { addItems } from './items'

const options = ref([])
const selected = ref('feature set 1')
const types = ref(['Similarity', 'Anomalies', 'Darkness/Brightness', 'Blurriness/Sharpness'])
const selectedType = ref('Similarity')
const similarity = ref(0.01)
const anomality = ref(0.3)
const minmax = ref({ min: 0, max: 0.1 })
const coruptedImages = ref<string[]>([])
const featureSetDict = ref({})
const datasetItemsCount = ref(0)
const minClusterSize = ref(2)
const clusterSizes = ref([2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 40, 50, 100])

const loading = ref(false)
const mounted = ref(false)
const qualityCount = ref(0)
type Cluster = {
    key: string
    main_item: string
    items: string[]
    is_choosed: boolean
    page: number
}
const emit = defineEmits(['trigger-reload', 'trigger-refresh'])

type Props = {
    datasetId: string
    lastUpdated: string
    progress: number
}

const showMainContent = computed(() => {
    return props.lastUpdated !== 'Never' && props.lastUpdated !== 'Error' && props.progress === 1
})

const coruptedImagesLength = computed(() => {
    return coruptedImages.value.length
})

defineExpose({
    deletedItemsRemove,
    reset
})

const noEmptyClusters = computed(() => {
    return clustersAll.value.filter(
        (cluster) => cluster.main_item !== '' && cluster.page === similarityPage.value
    )
})

const rightPannelScrollToTop = async () => {
    const right_pannel = document.querySelector(`.actions .right-pannel-inner`)
    // scroll smoothly to the top
    right_pannel.scrollTo({ top: 0, behavior: 'smooth' })
    loadLeftAndRightThumbs()
}

const triggerRefresh = () => {
    emit('trigger-refresh')
}

const triggerReload = () => {
    emit('trigger-reload')
}

const checkMetadata = async () => {
    const response = await fetch(`/api/get_quality_score_exist?datasetId=${props.datasetId}`)
    qualityCount.value = await response.json()
}

const props = defineProps<Props>()

const thumbSize = ref(128)

const coruptPage = ref(1)

const rowsPerPage = ref(25)

const similarityPage = ref(1)
const similarityRowsPerPage = computed(() => {
    // get page from last cluster
    const lastCluster = clustersAll.value[clustersAll.value.length - 1]
    const page = lastCluster.page
    return Math.ceil(AllItemsCount.value / page)
})

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
            (selectedType.value === 'Similarity' || selectedType.value === 'Anomalies')) ||
        (qualityCount.value === 0 &&
            selectedType.value !== 'Similarity' &&
            selectedType.value !== 'Anomalies') ||
        props.progress != 1 ||
        props.lastUpdated === 'Error'
    )
})

const clustersAll = ref<Cluster[]>([])

const selectedIds = ref(new Set<string>())

const images = computed(() => {
    const ids: string[] = []
    for (const cluster of noEmptyClusters.value) {
        ids.push.apply(ids, cluster.items)
    }
    return ids
})

const first2main = computed(() => {
    const main: { [id: string]: string } = {}
    for (const cluster of noEmptyClusters.value) {
        main[cluster.items[0]] = cluster.main_item
    }
    return main
})

const allChecked = computed({
    get() {
        const checkboxes: { [key: string]: string } = {}
        const isSelected = function (id: string) {
            return selectedIds.value.has(id)
        }
        for (const cluster of clustersAll.value) {
            checkboxes[cluster.key] = cluster.items.every(isSelected)
                ? 'all'
                : cluster.items.some(isSelected)
                ? 'some'
                : 'none'
        }
        return checkboxes
    },
    set() {}
})

const SelectAll = computed({
    get: () => {
        if (selectedIds.value.size === 0) {
            return 'none'
        }
        return clustersAll.value.every((cluster) =>
            cluster.items.every((id) => selectedIds.value.has(id))
        )
            ? 'all'
            : 'some'
    },
    set: (value) => {
        if (value === 'all') {
            clustersAll.value.forEach((cluster) => {
                cluster.items.forEach((id) => {
                    if (!selectedIds.value.has(id)) {
                        selectedIds.value.add(id)
                    }
                })
            })
        } else {
            selectedIds.value.clear()
        }
        updateSelection()
    }
})

const SelectAllCorupted = computed({
    get: () => {
        if (selectedIds.value.size === 0) {
            return false
        }
        return coruptedImages.value.every((id) => selectedIds.value.has(id))
    },
    set: (value) => {
        if (value) {
            coruptedImages.value.forEach((id) => {
                if (!selectedIds.value.has(id)) {
                    selectedIds.value.add(id)
                }
            })
        } else {
            selectedIds.value.clear()
        }
        updateSelection()
    }
})

let scrollingIntoView: boolean = false
const scrollIntoView = function (element: Element) {
    scrollingIntoView = true
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
        inline: 'nearest'
    })
    setTimeout(function () {
        scrollingIntoView = false
    }, 900)
}

const handleLeftSideClick = function (key: string, id: string) {
    const firstImage = document.querySelector(`.actions .right-pannel-inner [data-main="${id}"]`)
    if (firstImage) {
        scrollIntoView(firstImage)
    }

    handleCheckedUpdateMain(key, allChecked.value[key] === 'all' ? 'uncheck' : 'check')
}

const leftSideThumbs = ref<InstanceType<typeof ItemThumbnailImage>[]>([])
const rightSideThumbs = ref<InstanceType<typeof ItemThumbnailImage>[]>([])

const loadThumbs = (thumbs: InstanceType<typeof ItemThumbnailImage>[]) => {
    if (!thumbs.length) return

    const container = thumbs[0]?.$el.closest('.scroll')
    if (!container) return

    const containerTop = container.scrollTop
    const containerBottom = containerTop + container.offsetHeight

    thumbs.forEach((thumb) => {
        const el = thumb.$el.closest('.main-image') || thumb.$el
        const elTop = el.offsetTop - thumbSize.value
        const elBottom = elTop + el.offsetHeight

        // Determine if the element is within the visible area of the container
        const inView = elBottom > containerTop && elTop < containerBottom
        thumb.inView = inView
        if (inView) {
            thumb.fetchItem()
        }
    })
}

const handleLeftSideScroll = () => {
    loadThumbs(leftSideThumbs.value)
}

const handleRightSideScroll = (event: Event) => {
    loadThumbs(rightSideThumbs.value)

    const target = event.target as HTMLElement

    if (scrollingIntoView) return

    const mains = [...target.querySelectorAll('[data-main]')]
    const distanceToTop = function (div: HTMLElement) {
        const top = div.offsetTop - div.parentElement.offsetTop
        return Math.abs(top - target.scrollTop)
    }

    mains.sort(function (a, b) {
        return distanceToTop(a as HTMLElement) - distanceToTop(b as HTMLElement)
    })

    const div = mains[0] as HTMLElement
    const divInLeft = target
        .closest('.actions')
        .querySelector(`.left-pannel [data-main="${div.dataset.main}"]`)
    if (divInLeft) {
        scrollIntoView(divInLeft)
    }
}

const loadLeftAndRightThumbs = () => {
    setTimeout(function () {
        loadThumbs(leftSideThumbs.value)
        loadThumbs(rightSideThumbs.value)
    }, 100)
}

const SelectedTypeChange = async (typo) => {
    clear_all()
    if (typo === 'Similarity') {
        loading.value = true
        await nextTick()
        await new Promise((resolve) => setTimeout(resolve, 10))
        loading.value = false
    }

    selectedIds.value.clear()
    coruptedImages.value = []
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
    if (selectedType.value === 'Similarity') {
        loadLeftAndRightThumbs()
    }
}

const visibleCoruptedImages = computed(() => {
    const start = (coruptPage.value - 1) * rowsPerPage.value
    const end = start + rowsPerPage.value
    return coruptedImages.value.slice(start, end)
})

const removeSelected = () => {
    selectedIds.value.clear()
    updateSelection()
}
const deleteItem = (itemId: string) => {
    selectedIds.value.delete(itemId)
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
    selectedIds.value.delete(itemId)
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
            if (!selectedIds.value.has(id)) {
                selectedIds.value.add(id)
            }
        })
    } else {
        clustersAll.value[index].items.forEach((id) => {
            selectedIds.value.delete(id)
        })
    }
    await nextTick()
    updateSelection()
}

const handleCheckedUpdate = async (itemId: string) => {
    if (selectedIds.value.has(itemId)) {
        selectedIds.value.delete(itemId)
    } else {
        selectedIds.value.add(itemId)
    }
    await nextTick()
    updateSelection()
}

const updateSelection = () => {
    window.dl.sendEvent({
        name: 'dl:items:update:selection',
        payload: Array.from(selectedIds.value)
    })
}

const getImages = debounce(async () => {
    clear_all()
    if (loading.value) return // Prevent function from running if it's already loading
    loading.value = true
    if (selectedType.value === 'Similarity') {
        const response = await fetch(
            `/api/get_items?datasetId=${props.datasetId}&featureSetName=${selected.value}&type=${selectedType.value}&similarity=${similarity.value}&clusterSize=${minClusterSize.value}`
        )
        const clusters = await response.json()
        for (const cluster of clusters) {
            cluster.items = addItems(cluster.items)
            cluster.main_item = addItems([cluster.main_item])[0]
        }
        clustersAll.value = clusters
        selectedIds.value.clear()
        if (clustersAll.value.length > 0) {
            clustersAll.value[0].items.forEach((id) => {
                selectedIds.value.add(id)
            })
        }
        await nextTick()
        loadLeftAndRightThumbs()
    } else {
        coruptPage.value = 1
        await fetchCoruptedImages()
        selectedIds.value.clear()
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
        `/api/get_items?datasetId=${props.datasetId}&featureSetName=${selected.value}&type=${
            selectedType.value
        }&similarity=${anomality.value}&pagination=${coruptPage.value - 1}&limit=${
            rowsPerPage.value
        }&min_v=${minmax.value.min}&max_v=${minmax.value.max}`
    )
    const result = await response.json()
    coruptedImages.value = addItems(result.items)
}

async function reset() {
    coruptPage.value = 1
    clustersAll.value = []
    selectedIds.value.clear()
    similarityPage.value = 1

    const feature_sets = await fetch(`/api/available_feature_sets?datasetId=${props.datasetId}`)
    const response = await feature_sets.json()
    featureSetDict.value = response
    options.value = Object.keys(response)
    await checkMetadata()
    selected.value = options.value[0]

    if (options.value.length > 0) {
        await getImages()
    }
}

onBeforeMount(async () => {
    await reset()
    mounted.value = true
    const query_item = {
        filter: {
            $and: [
                {
                    $or: [
                        {
                            'metadata.system.mimetype': 'image/*'
                        },
                        {
                            'metadata.system.mimetype': 'text/*'
                        }
                    ]
                },
                {
                    hidden: false
                },
                {
                    type: 'file'
                }
            ]
        },
        resource: 'items'
    }

    datasetItemsCount.value = await window.dl.items.countByQuery(query_item)
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

const clear_all = () => {
    rightSideThumbs.value = []
    leftSideThumbs.value = []
    selectedIds.value.clear()
    similarityPage.value = 1
    updateSelection()
}

const SelectedChange = () => {
    clear_all()
    clustersAll.value = []
    if (datasetItemsCount.value != featureSetDict.value[selected.value]) {
        sendToastMassage(
            'For selected feature set, number of items in dataset is not equal to number of items in feature set. Please rerun the feature vector extraction',
            'warning'
        )
    }
}

const sortDirection = ref<boolean>(false)

const sortFunction = function (a: Cluster, b: Cluster): number {
    const direction = sortDirection.value ? 1 : -1
    if (a.items.length > b.items.length) return direction
    if (a.items.length < b.items.length) return -direction
    return 0
}

const toggleSortDirection = () => {
    sortDirection.value = !sortDirection.value
    clustersAll.value.sort(sortFunction)
    for (const div of document.querySelectorAll('.scroll')) {
        div.scrollTop = 0
    }
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

.w-20 {
    width: 20%;
}

.slider {
    display: block;
}
.slider :deep(#slider-input) {
    width: 50px;
}
/* undo bootstrap style */
.slider :deep(.header .row.text) {
    margin-left: 0;
}

.select-s {
    display: flex;
    align-items: center;
}
.select-s :deep(.dl-select__title-container) {
    margin-bottom: 0px !important;
    margin-right: 5px !important;
}

.actions {
    display: flex;
}

.range-all {
    width: 20%;
    display: flex;
    justify-content: space-between;
}
.range {
    width: 20%;
    flex-direction: column;
}

.w-100-120px {
    width: calc(100% - 120px);
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
    display: flex;
    flex-direction: column;
    flex-grow: 1;
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
    height: calc(100vh - 80px - 35px); /* 35px for thumbs slider */
}

.right-pannel .thumb-size {
    width: 200px;
    padding-left: 30px;
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

.non-visible {
    opacity: 0;
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

.pagination-controls {
    display: flex;
    gap: 20px;
    justify-content: center;
    align-items: center;
}
</style>
