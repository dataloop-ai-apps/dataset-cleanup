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

            <dl-range
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
        </div>
        <div v-if="loading" class="loading">
            <DlSpinner text="Loading, please wait..." size="60px" />
        </div>
        <div></div>

        <div v-if="!loading && selectedType == 'Similarity'">
            <div v-if="options.length > 0">
                <div class="select-all">
                    <DlCheckbox
                        v-model="SelectAll"
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
                                <DlCheckbox
                                    v-model="allChecked[cluster.key]"
                                    :disabled="!cluster.is_choosed"
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
                                <ItemThumbnailImage
                                    :item-id="cluster.main_item"
                                    :checked="false"
                                    :main-checked="cluster.is_choosed"
                                    @main-item-selected="
                                        MainItemSelected($event)
                                    "
                                />
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="rigth-pannel scroll">
                            <div
                                v-for="(id, index) in visibleImages"
                                :key="index + '-' + id"
                            >
                                <ItemThumbnailImage
                                    :item-id="id"
                                    :checked="selectedIds.includes(id)"
                                    :main-checked="false"
                                    @update:checked="handleCheckedUpdate(id)"
                                    @delete:item="deleteItem(id)"
                                />
                            </div>
                        </div>
                        <DlPagination
                            v-model="page"
                            class="pagination"
                            :total-items="images.length"
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
                    :show-bottom="true"
                    @trigger-refresh="triggerRefresh"
                />
            </div>
        </div>
        <div v-if="!loading && selectedType !== 'Similarity'">
            <div v-if="qualityCount > 0">
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
                    :show-bottom="true"
                    @trigger-refresh="checkMetadata"
                />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, onBeforeMount, onMounted } from 'vue'
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
import {
    reactive,
    ref,
    computed,
    watch,
    nextTick,
    defineExpose,
    defineEmits
} from 'vue-demi'
const options = ref([])
const selected = ref('feature set 1')
const types = ref(['Similarity', 'Darkness', 'Blurriness'])
const selectedType = ref('Similarity')
const similarity = ref(0.01)
const minmax = ref({ min: 0, max: 100 })
const images = ref<string[]>([])
const coruptedImages = ref<string[]>([])
const featureSetDict = ref({})
const datasetItemsCount = ref(0)

const mainItem = ref<string>('')
const loading = ref(false)
const mounted = ref(false)
const qualityCount = ref(0)
type Cluster = {
    key: string
    main_item: string
    is_choosed: boolean
    items: string[] // assuming each item is identified by a string ID
}
const emit = defineEmits(['trigger-refresh'])

type Props = {
    itemId: string
    datasetId: string
}

const coruptedImagesLength = computed(() => {
    return coruptedImages.value.length
})

defineExpose({
    deletedItemsRemove
})

const noEmptyClusters = computed(() => {
    return clusters.value.filter((cluster) => cluster.main_item !== '')
})

const triggerRefresh = () => {
    emit('trigger-refresh')
}

const checkMetadata = async () => {
    const response = await fetch(
        `/api/get_quality_score_exist?datasetId=${props.datasetId}`
    )
    qualityCount.value = await response.json()
}

const props = defineProps<Props>()

const page = ref(1)

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

const allChecked = computed(() => {
    return clusters.value.reduce((acc, cluster) => {
        acc[cluster.key] = cluster.items.every((id) =>
            selectedIds.value.includes(id)
        )
        return acc
    }, {})
})

const SelectAll = computed({
    get: () => {
        if (selectedIds.value.length === 0) {
            return false
        }
        return clustersAll.value.every((cluster) =>
            cluster.items.every((id) => selectedIds.value.includes(id))
        )
    },
    set: (value) => {
        if (value) {
            clustersAll.value.forEach((cluster) => {
                cluster.items.forEach((id) => {
                    if (!selectedIds.value.includes(id)) {
                        selectedIds.value.push(id)
                    }
                    if (!images.value.includes(id)) {
                        images.value.push(id)
                    }
                })
                cluster.is_choosed = true
            })
        } else {
            selectedIds.value = []
            images.value = []
            clustersAll.value.forEach((cluster) => {
                cluster.is_choosed = false
            })
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

const visibleImages = computed(() => {
    const start = (page.value - 1) * rowsPerPage.value
    const end = start + rowsPerPage.value
    return images.value.slice(start, end)
})

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
    images.value = images.value.filter((id) => id !== itemId)
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

const MainItemSelected = async (itemId: string) => {
    mainItem.value = itemId

    const new_images = clustersAll.value.find(
        (cluster) => cluster.main_item === itemId
    )

    new_images.is_choosed = !new_images.is_choosed
    if (new_images.is_choosed) {
        selectedIds.value = Array.from(
            new Set([...selectedIds.value, ...new_images.items])
        )
        images.value = Array.from(
            new Set([...images.value, ...new_images.items])
        )
    } else {
        selectedIds.value = selectedIds.value.filter(
            (id) => !new_images.items.includes(id)
        )
        images.value = images.value.filter(
            (id) => !new_images.items.includes(id)
        )
    }
    page.value = Math.max(
        Math.min(
            Math.ceil(images.value.length / rowsPerPage.value),
            page.value
        ),
        1
    )

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
        page.value = 1

        const response = await fetch(
            `/api/get_items?datasetId=${props.datasetId}&featureSetName=${selected.value}&type=${selectedType.value}&similarity=${similarity.value}`
        )
        clustersAll.value = await response.json()
        clusters.value = clustersAll.value.slice(0, 10)
        images.value = [...clusters.value[0].items]
        selectedIds.value = [...images.value]
        mainItem.value = clusters.value[0].main_item
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
    page.value = 1
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

onBeforeMount(async () => {
    const feature_sets = await fetch(
        `/api/available_feature_sets?datasetId=${props.datasetId}`
    )
    const response = await feature_sets.json()
    featureSetDict.value = response
    options.value = Object.keys(response)
    await checkMetadata()
    selected.value = options.value[0]
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
</script>

<style scoped>
.flex-container {
    display: flex; /* Establishes the flex container */
    justify-content: space-between;
    align-items: center; /* Vertically centers the items in the container */
    margin-top: 5px;
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
.actions {
    display: flex;
    margin-top: 5px;
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

.loading {
    display: grid; /* Use the grid layout */
    place-items: center; /* Center items both horizontally and vertically */
    height: 100vh; /* Full viewport height to ensure centering is relative to the entire screen */
    width: 100vw; /* Full viewport width, necessary if your spinner is absolute or fixed positioned */
}
.left-pannel {
    width: 165px;
    min-width: 165px;
    overflow-y: auto;
}
.rigth-pannel {
    border-left: 2px solid var(--dl-color-disabled);
    display: flex;
    width: calc(100vw - 170px);
    flex-wrap: wrap;
    overflow-y: auto;
    align-content: flex-start;
    justify-content: flex-start;
    border-left: 2px solid var(--dl-color-disabled);
    padding-left: 5px;
    margin-left: 5px;
}
.pagination :deep(.dl-pagination--container) {
    border-left: 2px solid var(--dl-color-disabled);
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
    padding-left: 5px;
    margin-left: 5px;
    height: calc(100vh - 190px); /* Adjust as needed based on your layout */
    overflow-y: auto;
}

.main-image {
    display: flex;
}

.checkbox {
    justify-content: center;
    margin-right: 5px;
    transform: translateY(-15px);
}

.left-pannel {
    height: calc(100vh - 157px); /* Adjust as needed based on your layout */

    overflow-y: auto;
}
.rigth-pannel {
    height: calc(100vh - 190px); /* Adjust as needed based on your layout */
    overflow-y: auto;
}

.invisible {
    display: none;
}

.select-all {
    display: flex;
    justify-content: flex-start;
    min-height: 40px;
    border-bottom: 1px solid var(--dl-color-disabled);
    align-items: center;
}

.checkbox-all {
    padding-right: 15px;
    padding-left: 5px;
}
</style>
