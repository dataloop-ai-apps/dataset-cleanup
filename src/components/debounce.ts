export default function debounce(func: Function, wait: number) {
    let timeoutId = 0
    return function (...args: any[]) {
        window.clearTimeout(timeoutId)
        timeoutId = window.setTimeout(function () {
            func(...args)
        }, wait)
    }
}
