"""Landing page route tests."""


def test_landing_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Parlez" in r.text
    assert "landing.css" in r.text
    assert "Speak French" in r.text
    # Removed elements
    assert "Trusted by" not in r.text
    assert 'id="pricing"' in r.text  # honest "Free now / Plus planned" pricing
    assert "10,000+" not in r.text
    # Added About section
    assert 'id="about"' in r.text
    assert "Your personal path to French fluency" in r.text
    assert "AI-powered French tutor" in r.text


def test_landing_page_describes_course_library_and_preserves_disclosures(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "A1–B2 practice paths" in response.text
    assert 'id="course-path"' in response.text
    assert "saves your learner level and keeps Settings and the sidebar in sync" in response.text
    assert "not CEFR or NCLC certification and not validated estimates of proficiency" in response.text
    assert "no reviewer name or qualification" in response.text
    assert "not official scores and do not establish exam readiness" in response.text
    assert "Course and feature availability and prices may change" in response.text
    assert "does not determine immigration eligibility" in response.text
    assert "Future course levels" not in response.text
    assert "Next stage · planned" not in response.text


def test_legal_page(client):
    r = client.get("/legal")
    assert r.status_code == 200
    assert "Terms of Service" in r.text
    assert "Privacy Policy" in r.text
    assert "Refund" in r.text
    assert "not legal advice" in r.text
    assert "not affiliated" in r.text
    assert 'href="/legal"' in client.get("/").text


def test_french_for_canada_guide(client):
    r = client.get("/learn/french-for-canada")
    assert r.status_code == 200
    assert "NCLC 7" in r.text
    assert "Équivalence ancien score" in r.text
    assert "Educational content only" in r.text


def test_signup_page_and_legacy_redirect(client):
    signup = client.get("/signup")
    assert signup.status_code == 200
    assert 'rel="canonical" href="http://testserver/signup"' in signup.text
    legacy = client.get("/login?mode=signup", follow_redirects=False)
    assert legacy.status_code == 308
    assert legacy.headers["location"] == "/signup"


def test_app_shell_route(client):
    r = client.get("/app")
    assert r.status_code == 200
    assert 'rel="canonical" href="http://testserver/app"' in r.text


def test_landing_canonical_is_absolute(client):
    r = client.get("/")
    assert 'rel="canonical" href="http://testserver/"' in r.text
    assert 'og:url" content="http://testserver/"' in r.text


def test_login_page(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "auth-screen" in r.text
    assert "auth.css" not in r.text  # styles are inlined in index.html
