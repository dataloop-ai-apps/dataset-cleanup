import { SDKItem } from '@dataloop-ai/jssdk'

const items: { [key: string]: Promise<SDKItem> } = {}

function delay(ms: number) {
    return new Promise(function (resolve) {
        setTimeout(resolve, ms)
    })
}

export async function fetchSDKItem(itemId: string, attempts = 3) {
    try {
        const promise = items[itemId] ?? window.dl.items.get(itemId)
        items[itemId] = promise
        return await promise
    } catch (error) {
        if (attempts > 1) {
            await delay(400)
            return await fetchSDKItem(itemId, attempts - 1)
        } else {
            console.error('Error fetching item ' + itemId, error)
        }
    }
}
