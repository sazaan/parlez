# Parlez Landing Page Design

## Overview

A new public landing page shown **before** the existing auth screen. It introduces the product, lists key features, and funnels visitors to sign up or log in.

## Goal

Make a beautiful, premium first impression that matches the upgraded in-app visual language and drives visitors to create an account or log in.

## Scope

Sections included:

1. **Navigation bar** — logo, links (Features, Pricing, About), Log In CTA
2. **Hero** — headline, subheadline, primary + secondary CTAs, trust signal, glass phone mockup
3. **Features** — 6 feature cards in a 3-column grid
4. **Bottom CTA strip** — final conversion push
5. **Footer** — logo, copyright, legal links

Out of scope for now: pricing page, testimonials, FAQ, about page, dark mode.

## Visual Design

### Direction

"The Atelier" — a hybrid of editorial elegance, glassmorphism depth, and split-layout conversion focus.

### Color Palette (existing app tokens)

- Background cream: `#f8f7f4`
- Deep burgundy (primary): `#7c2d3f`
- Burgundy light: `#a8455c`
- Burgundy dark: `#5c1f2d`
- Gold (secondary): `#c9a35c`
- Gold light: `#e0be7a`
- Accent green: `#2d6a4f`
- Text: `#18181b`
- Muted text: `#71717a`
- Card white: `#ffffff`

### Typography

- **Headlines**: Playfair Display (serif, italic weight for logo)
- **Body / UI**: Inter (sans-serif)

### Hero

- Full-width gradient: `linear-gradient(135deg, #7c2d3f 0%, #5c1f2d 45%, #c9a35c 100%)`
- Subtle radial lighting overlays
- Oversized rotated "Parlez" watermark (very low opacity)
- Left: tag pill, headline with gold accent word, subheadline, two CTAs, trust avatars + text
- Right: floating frosted-glass phone mockup showing a chat preview

### Navigation

- Transparent over the hero gradient
- Logo on left (P mark + "Parlez")
- Center/right links: Features, Pricing, About
- "Log In" pill button

### Features Section

- Cream background
- Section label (uppercase, small, burgundy)
- Section headline in Playfair Display
- 6 cards in a 3-column responsive grid:
  1. AI Conversations
  2. Adaptive Lessons
  3. Mock Exams
  4. Smart Flashcards
  5. Progress Tracking
  6. Native Audio

### CTA Strip

- White background
- Centered headline, subtext, primary button

### Footer

- Near-black (`#18181b`) background
- Logo + copyright on left
- Privacy / Terms / Contact links on right

## Interactions

- Primary CTA "Start Learning Free" links to `/login?mode=signup`
- Secondary CTA "See How It Works" smooth-scrolls to `#features`
- "Log In" links to `/login`
- Nav links scroll to in-page anchors (`#features`)
- Hover states: buttons lift slightly, feature cards gain shadow
- Entrance animations: fade-in-up for hero text and phone mockup

## Responsiveness

- Desktop: split hero (copy left, phone right), 3-column feature grid
- Tablet: hero stacks vertically, 2-column feature grid
- Mobile: single column, phone below headline, hamburger nav (optional v1: keep nav links inline and wrap)

## Files to Create / Modify

- `static/landing.html` — new landing page markup
- `static/landing.css` — landing page specific styles (reuse CSS variables from `styles.css`)
- `static/app.js` — minor update if needed for nav scroll/CTA behavior
- `main.py` — serve `/` as landing page, serve `/login` as the existing auth screen

## Technical Notes

- Use existing CSS custom properties from `styles.css` for consistency.
- Keep landing CSS in a separate file so the main app CSS stays focused.
- Phone mockup is pure CSS/HTML (no image assets) to avoid asset hosting.
- No external dependencies beyond Inter/Playfair Google Fonts (already loaded).

## Approval

Approved by user on 2026-07-03 after reviewing hybrid direction "The Atelier" in the visual companion.
