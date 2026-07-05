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
    assert "#pricing" not in r.text
    assert "10,000+" not in r.text
    # Added About section
    assert 'id="about"' in r.text
    assert "Your personal path to French fluency" in r.text
    assert "AI-powered French tutor" in r.text


def test_login_page(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "auth-screen" in r.text
    assert "auth.css" not in r.text  # styles are inlined in index.html
