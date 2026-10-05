// Keep the chat composer inside the visible viewport when mobile browser chrome
// or the software keyboard changes its height (including iOS Safari).
(() => {
    const viewport = window.visualViewport;
    function updateViewport() {
        // Do not resize the layout while the user deliberately pinch-zooms.
        if (viewport && viewport.scale !== 1) return;
        const height = viewport ? viewport.height : window.innerHeight;
        const top = viewport ? viewport.offsetTop : 0;
        document.documentElement.style.setProperty('--app-height', `${height}px`);
        document.documentElement.style.setProperty('--app-top', `${top}px`);
    }
    window.addEventListener('resize', updateViewport);
    viewport?.addEventListener('resize', updateViewport);
    viewport?.addEventListener('scroll', updateViewport);
    updateViewport();
})();
