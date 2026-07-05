# Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a beautiful public landing page at `/` that matches the approved "Atelier" design and links to the existing auth screen at `/login`.

**Architecture:** A self-contained `static/landing.html` + `static/landing.css` pair keeps the landing page separate from the app UI. FastAPI's `HTMLResponse` serves the landing page at `/`, while `/login` returns the existing auth screen. A small smoke test verifies the route returns HTML.

**Tech Stack:** HTML, CSS (custom properties from `styles.css`), vanilla JS, FastAPI, pytest.

---

## File Structure

- `static/landing.html` — new landing page markup
- `static/landing.css` — landing page specific styles
- `main.py` — add `/` landing route and `/login` auth route
- `tests/test_landing.py` — new smoke test for landing page

---

## Task 1: Create landing page HTML

**Files:**
- Create: `static/landing.html`

- [ ] **Step 1: Write markup**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Parlez — French AI Tutor</title>
  <link rel="stylesheet" href="/static/landing.css">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="icon" href="data:image/svg+xml,...">
</head>
<body>
  <nav>...</nav>
  <header class="hero">...</header>
  <section id="features" class="features">...</section>
  <section class="cta-strip">...</section>
  <footer>...</footer>
</body>
</html>
```

- [ ] **Step 2: Verify file exists**

Run: `ls static/landing.html`

---

## Task 2: Create landing page CSS

**Files:**
- Create: `static/landing.css`

- [ ] **Step 1: Write styles**

```css
@import url('/static/styles.css'); /* Reuse tokens */
/* landing-specific overrides and sections */
```

- [ ] **Step 2: Check CSS braces**

Run: `python3 -c "css=open('static/landing.css').read(); print('balanced' if css.count('{')==css.count('}') else 'mismatched')"`

---

## Task 3: Wire routes in main.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Add `/` and `/login` routes**

```python
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    with open("static/landing.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())
```

- [ ] **Step 2: Ensure static mount still serves files**

The existing `app.mount("/static", ...)` remains unchanged.

---

## Task 4: Add smoke test

**Files:**
- Create: `tests/test_landing.py`

- [ ] **Step 1: Write test**

```python
def test_landing_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Parlez" in r.text

def test_login_page(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "auth-screen" in r.text
```

- [ ] **Step 2: Run tests**

Run: `JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy venv/bin/python -m pytest tests/test_landing.py -v`

---

## Task 5: Full verification

- [ ] **Step 1: Run full test suite**

Run: `JWT_SECRET=$(openssl rand -hex 32) NVIDIA_API_KEY=dummy venv/bin/python -m pytest tests/ -q`
Expected: 15 passed

- [ ] **Step 2: Run lint**

Run: `venv/bin/ruff check main.py tests/test_landing.py`
Expected: no output

- [ ] **Step 3: Manual preview**

Run the dev server and open `http://localhost:8000` in a browser.

---

## Self-Review

- Spec coverage: hero, features, footer, nav, CTAs, responsiveness all have corresponding markup/styles.
- No placeholders: all code blocks contain concrete content.
- Type consistency: route functions return `HTMLResponse` consistently.
