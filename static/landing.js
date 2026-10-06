// ============================================================
// Parlez — landing page behaviour
// Progressive enhancement: the page is fully readable without JS.
// ============================================================

(() => {
    'use strict';

    // Add the animation class only from this CSP-approved external script.
    // If JS is unavailable or blocked, reveal content remains visible.
    document.documentElement.classList.add('js');

    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

    // ---------------- Mobile navigation ----------------

    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');

    function setNavOpen(open) {
        if (!navLinks || !navToggle) return;
        navLinks.classList.toggle('is-open', open);
        navToggle.setAttribute('aria-expanded', String(open));
    }

    function isNavOpen() {
        return Boolean(navLinks && navLinks.classList.contains('is-open'));
    }

    navToggle?.addEventListener('click', () => setNavOpen(!isNavOpen()));

    // Close the menu after choosing a destination on mobile.
    navLinks?.addEventListener('click', (event) => {
        if (event.target.closest('a')) setNavOpen(false);
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && isNavOpen()) {
            setNavOpen(false);
            navToggle?.focus();
        }
    });

    document.addEventListener('click', (event) => {
        if (!isNavOpen()) return;
        if (event.target.closest('#navLinks') || event.target.closest('#navToggle')) return;
        setNavOpen(false);
    });

    // ---------------- Smooth anchor scrolling ----------------
    // Close the menu first so the destination is not scrolled under an open panel.

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', (event) => {
            const href = anchor.getAttribute('href');
            if (!href || href === '#') return;
            const target = document.querySelector(href);
            if (!target) return;
            event.preventDefault();
            setNavOpen(false);
            target.scrollIntoView({
                behavior: prefersReducedMotion ? 'auto' : 'smooth',
                block: 'start'
            });
            // Move focus for keyboard and screen-reader users.
            target.setAttribute('tabindex', '-1');
            target.focus({ preventScroll: true });
        });
    });

    // ---------------- Navbar elevation on scroll ----------------

    const navbar = document.getElementById('navbar');
    if (navbar) {
        const syncNavbar = () => navbar.classList.toggle('is-stuck', window.scrollY > 8);
        syncNavbar();
        window.addEventListener('scroll', syncNavbar, { passive: true });
    }

    // ---------------- Scroll reveal ----------------

    const revealTargets = document.querySelectorAll('.reveal');

    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
        revealTargets.forEach((el) => el.classList.add('is-visible'));
    } else {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });

        revealTargets.forEach((el) => observer.observe(el));
    }
})();
