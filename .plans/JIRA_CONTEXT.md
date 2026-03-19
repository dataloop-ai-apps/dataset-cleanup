# Jira Context for DAT-129554

## Main Ticket
**DAT-129554** — Cleanup tab | SVG loading animation
Type: Sub-task | Status: In Progress | Priority: Medium
Labels: Design

Implement a tab-specific SVG loading animation in the *Cleanup* tab.
The animation should run in a loop while the clustering process is loading.

*Cleanup SVG Code:*

{code:html}<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Loading File Animation</title>
<style>
    body {
        margin: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        background-color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        overflow: hidden; /* Prevent scrolling during parallax */
    }

    .loader-container {
        width: 100%;
        max-width: 600px;
        padding: 20px;
    }

    .icon {
        animation: carousel 8s infinite cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Assigning a CSS variable --delay so inner elements can sync with the parent's loop */
    .icon-1 { animation-delay: 0s; --delay: 0s; }
    .icon-2 { animation-delay: -2s; --delay: -2s; }
    .icon-3 { animation-delay: -4s; --delay: -4s; }
    .icon-4 { animation-delay: -6s; --delay: -6s; }

    @keyframes carousel {
        0%, 18.75% { transform: translate(80px, 160px) scale(0); opacity: 0; }
        25%, 43.75% { transform: translate(190px, 160px) scale(0.6); opacity: 0.25; }
        50%, 68.75% { transform: translate(300px, 160px) scale(1); opacity: 1; }
        75%, 93.75% { transform: translate(410px, 160px) scale(0.6); opacity: 0.25; }
        100% { transform: translate(520px, 160px) scale(0); opacity: 0; }
    }

    /* Fades the inner dots in ONLY when the icon reaches the center */
    .dots-wrapper {
        animation: dots-visibility 8s infinite cubic-bezier(0.4, 0, 0.2, 1);
        animation-delay: var(--delay, 0s);
    }

    @keyframes dots-visibility {
        0%, 43.75% { opacity: 0; }
        50%, 68.75% { opacity: 1; } /* Center Phase */
        75%, 100% { opacity: 0; }
    }

    /* Parallax transforms driven by JS CSS variables */
    .parallax-layer-1 {
        /* Background Layer (Gray Dots) - Moves slowly */
        transform: translate(calc(var(--mouseX, 0) * -5px), calc(var(--mouseY, 0) * -5px));
        will-change: transform;
    }

    .parallax-layer-2 {
        /* Foreground Layer (Blue Dots) - Moves quickly to create depth */
        transform: translate(calc(var(--mouseX, 0) * -16px), calc(var(--mouseY, 0) * -16px));
        will-change: transform;
    }
</style>
</head>
<body>

    <div class="loader-container">
        <svg viewBox="0 0 600 400" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <clipPath id="file-clip">
                    <path d="M -45 -65 L 15 -65 L 45 -35 L 45 65 L -45 65 Z" />
                </clipPath>

                <g id="file-icon">
                    <!-- Solid white background -->
                    <path d="M -45 -65 L 15 -65 L 45 -35 L 45 

**Comments** (4):
> **Otto**: Otto started working on this ticket. Triage: Implement a tab-specific SVG loading animation in the Cleanup tab.
> **Otto**: Otto task failed: 1/1 subtasks failed
> **Otto**: Otto task failed: 1/1 subtasks failed
> **Otto**: Otto task failed: 1/1 subtasks failed

## Parent Issue: DAT-129549
**DAT-129549** — Add SVG loading animations to Dataset Browser tabs
Type: Story | Status: New | Priority: Medium
Labels: Design

Add dedicated SVG loading animations to the following Dataset Browser tabs: Clustering, Insights, and Cleanup
Each tab should display a different SVG animation while loading.

*Requirements:*

* Add a unique SVG animation for each tab:
** Clustering [https://dataloop.atlassian.net/browse/DAT-129552|https://dataloop.atlassian.net/browse/DAT-129552|smart-link] 
** Insights [https://dataloop.atlassian.net/browse/DAT-129553|https://dataloop.atlassian.net/browse/DAT-129553|smart-link] 
** Cleanup [https://dataloop.atlassian.net/browse/DAT-129554|https://dataloop.atlassian.net/browse/DAT-129554|smart-link] 
* Each animation must loop continuously while the relevant process is loading
* Display a Dell progress bar below each animation


*Responsive Behavior*

* The loading animation and progress bar must respond to container size changes.
* When the user resizes the window or narrows the docked tab, both elements scale accordingly.
* *Loading Animation*
** Maximum size: *480 × 480 px*
** Minimum size: *120 × 120 px*
** The animation scales proportionally with the container.
** *Aspect ratio must always be preserved.*
** Margin above the animation: *24 px*
* *Progress Bar*
** Maximum width: *520 px*
** Minimum width: *240 px*
** The progress bar width scales with the tab width.
** Maintain *16 px margin on each side* of the container at all times.

!Screen Recording 2026-03-11 at 17.28.33.mov|width=320,alt="Screen Recording 2026-03-11 at 17.28.33.mov"!

**Attachments:**
- Screen Recording 2026-03-11 at 17.28.33.mov (video/quicktime, 9128 KB)