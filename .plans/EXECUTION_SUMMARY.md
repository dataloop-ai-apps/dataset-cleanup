## What was done

Created `CleanupLoadingAnimation.vue` from the provided HTML/CSS/JS, implementing the file icon carousel animation (4 icons, dots-visibility sync, optional parallax). Replaced `DlSpinner` in `CleaningItem.vue` (lines 70-72) with this component when `loading` is true. Added `DlProgressBar` below the animation per parent story DAT-129549. Implemented responsive sizing: max 480×480px, min 120×120px, 24px margin above, aspect ratio preserved. The animation loops continuously during the clustering process (`getImages`) and other loading states.

## Root cause

N/A

## Test results

Vite build succeeded. No unit tests exist for this component.

## Notes

- vue-tsc fails with "sys is not defined" (pre-existing); Vite build works.
- Parallax CSS variables are scoped to the component container.
