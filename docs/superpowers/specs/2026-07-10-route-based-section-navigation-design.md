# Route-Based Section Navigation Design

## Status

Approved — ready for implementation planning.

## Goal

Separate the chat experience from the other learning sections. Selecting **Practice**, **Tests**, **Courses**, **Scenarios**, or **Content Tools** from the sidebar navigates to a dedicated section with its own URL, leaving the chat view intact and independently accessible.

## Decisions from brainstorming

- **View mode:** Hide the chat and show the selected section in the main area (tab/page switching).
- **URLs:** Each section gets a real browser route: `/chat`, `/courses`, `/practice`, `/scenarios`, `/tests`, `/tools`.
- **Top-level sections:** Chat, Courses, Practice, Scenarios, Tests, Content Tools.
- **Cross-section navigation:** Actions started from chat (quick actions, lesson practice, scenarios, etc.) navigate to the dedicated section.
- **Sidebar:** Remains visible as a persistent navigation rail on all sections.
- **State:** Preserve rendered DOM and scroll position when switching sections.
- **Default route:** After login, land on `/chat`. The root `/` remains the public landing page.

## Approach

**Approach A — Route-based SPA views** is selected.

We keep a single `index.html` application shell and add explicit view containers for each section. A lightweight client-side router shows/hides views based on the URL path. The backend serves `index.html` for each app route.

### Why Approach A

- Gives the real URLs and direct-link behavior the user requested.
- Preserves state across section switches without extra storage logic.
- Builds on the existing single-page architecture without creating separate HTML files.
- Simpler than separate pages because the shared shell, sidebar, auth flow, and API layer stay unchanged.

## Architecture

### Routes

| Path | Section | Default landing content |
|---|---|---|
| `/chat` | Chat | Welcome screen or most recent conversation |
| `/courses` | Courses | Course units and lessons for the user’s current level |
| `/practice` | Practice | Quick-practice menu: vocab quiz, conjugation drill, flashcards, word of the day, adaptive analysis |
| `/scenarios` | Scenarios | Conversation practice scenarios list |
| `/tests` | Tests | TEF/TCF mock tests and test history |
| `/tools` | Content Tools | Ingest French content tool |

All routes are authenticated at the API layer; the shell itself is served to unauthenticated users, and the existing `checkAuth()` flow shows the auth screen when needed.

### Server-side changes

- Add FastAPI routes for `/chat`, `/courses`, `/practice`, `/scenarios`, `/tests`, `/tools` that return `static/index.html` with no-cache headers.
- Update `/api/auth/login` and `/api/auth/signup` to redirect the client to `/chat` on success. Because the frontend uses a JSON fetch, this can be done by returning a `redirect_url` field in the response and having the frontend call `navigateTo('/chat')`.

### Frontend structure

`index.html` main content area contains sibling view containers:

```html
<div id="chatView" class="main-view">...</div>
<div id="coursesView" class="main-view" style="display:none">...</div>
<div id="practiceView" class="main-view" style="display:none">...</div>
<div id="scenariosView" class="main-view" style="display:none">...</div>
<div id="testsView" class="main-view" style="display:none">...</div>
<div id="toolsView" class="main-view" style="display:none">...</div>
```

The existing generic `toolView` is removed or converted into these explicit views.

### Sidebar navigation

The sidebar becomes a persistent nav rail. Each top-level section is a clickable item with an icon and label. Selecting a section calls `navigateTo('/<section>')`.

The chat list remains in the sidebar under a collapsible “Chats” group so users can still switch conversations while in any section.

### Router module

A small module in `app.js` (or `router.js`) provides:

- `navigateTo(path)` — push history state, call `renderRoute(path)`.
- `renderRoute(path)` — map path to view ID, call `showView(viewId)`, update sidebar active state, restore scroll position.
- `popstate` listener — re-render on browser back/forward.
- Initial route resolution after successful `checkAuth()`.

### State preservation

Rendered section DOM is kept in memory inside hidden view containers. When a view is shown, its previous `scrollTop` is restored. In-progress quiz/test state variables remain in memory.

Data is loaded lazily: each section calls its loader only when first shown or when explicitly refreshed.

### Cross-section navigation from chat

Actions that today open inside the chat/tool view will navigate to the appropriate section:

- “Take a Quiz” quick action → `/practice`
- Scenario selection / “Café Roleplay” → `/scenarios`
- Lesson “Learn” / “Practice” → `/courses`
- “Ingest French Content” → `/tools`
- Mock test selection → `/tests`

Sections support an optional entry intent so the chat action can open the desired sub-state (e.g., start the vocab quiz, open a specific lesson).

### Header behavior

- Title updates to the current section name.
- A back arrow appears on non-chat sections and navigates to `/chat`.
- On mobile, selecting a section closes the sidebar drawer.

## Testing plan

- Existing `pytest` suite must continue to pass.
- Add backend route tests verifying `/chat`, `/courses`, `/practice`, `/scenarios`, `/tests`, `/tools` return `index.html` and the correct no-cache headers.
- Manual QA checklist:
  - Login lands on `/chat`.
  - Sidebar nav switches sections and updates URL.
  - Chat is preserved when leaving and returning.
  - Courses, Practice, Scenarios, Tests, and Tools each render in their own view.
  - Chat quick actions navigate to the correct section.
  - Back button returns to chat.
  - Mobile sidebar closes on section selection.
  - In-progress quiz/test state survives section switching.

## Out of scope

- Rewriting each section as separate HTML pages.
- Server-side rendering of section content.
- Animated page transitions (can be added later).
- URL sub-routes such as `/practice/vocab-quiz` or `/courses/lesson-id` in this iteration.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| `app.js` grows larger | Keep the router isolated; each section’s render/load logic grouped by comment blocks or small modules. |
| Duplicate event listeners when re-showing views | Use delegated handlers where possible; avoid re-attaching listeners inside show functions. |
| Scroll position lost on mobile | Save/restore `scrollTop` for each view container in the router. |
| Direct refresh on `/practice` 404s | Add FastAPI catch-all routes for app paths. |
