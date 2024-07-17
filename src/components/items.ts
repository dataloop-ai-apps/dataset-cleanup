export type Item = {
    itemId: string
    name: string
    thumbnail: string
}
const itemsData: { [key: string]: Item } = {}

export function addItems(items: Item[]): string[] {
    for(let i = 0; i < items.length; i++) {
        itemsData[items[i].itemId] = items[i]
    }
    return items.map(item => item.itemId)
}

export function getItem(id: string): Item {
    return itemsData[id]
}
