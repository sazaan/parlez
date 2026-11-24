"""Phase D: 32 attributed mission units / 96 lessons exposed to the Learn shell."""

from courses.attributed_content import ATTRIBUTED_CATALOG
from courses.validation import validate_catalog


def test_catalog_shape_and_validation():
    assert set(ATTRIBUTED_CATALOG) == {"A1", "A2", "B1", "B2"}
    for course in ATTRIBUTED_CATALOG.values():
        assert len(course.units) == 8
        assert all(len(unit.lessons) == 3 for unit in course.units)
        assert course.framework == "mission-v2"
        assert course.provenance.review_state == "practice"
    assert validate_catalog(ATTRIBUTED_CATALOG) == {}


def test_levels_endpoint(client):
    r = client.get("/api/learn/courses")
    assert r.status_code == 200
    data = r.json()
    assert [x["level"] for x in data["levels"]] == ["A1", "A2", "B1", "B2"]
    assert all(x["lessonCount"] == 24 for x in data["levels"])
    assert "Not CEFR/NCLC certification" in data["notice"]


def test_course_endpoint_returns_units_and_lessons(client):
    r = client.get("/api/learn/courses/A2")
    assert r.status_code == 200
    data = r.json()
    assert len(data["units"]) == 8
    assert len(data["units"][0]["lessons"]) == 3
    assert data["units"][0]["capstone"]


def test_lesson_endpoint_includes_attribution(client):
    r = client.get("/api/learn/courses/A1/lessons/a1-greetings-l1")
    assert r.status_code == 200
    data = r.json()
    assert data["vocabulary"]
    assert data["provenance"]["reviewState"] == "practice"
    assert data["provenance"]["attribution"]
    assert "descriptorIds" in data


def test_checkpoint_hides_answers_and_grades_on_server(auth_client):
    lesson_id = "a1-greetings-l1"
    r = auth_client.get(f"/api/learn/courses/A1/lessons/{lesson_id}/checkpoint")
    assert r.status_code == 200
    data = r.json()
    assert data["questions"]
    assert all("answer" not in q and "answerIndex" not in q for q in data["questions"])
    assert data["passPercent"] == 70

    from courses.attributed_content import ATTRIBUTED_CATALOG
    from courses.checkpoints import _answers
    course = ATTRIBUTED_CATALOG["A1"]
    unit = course.units[0]
    lesson = unit.lessons[0]
    answers = {key: index for key, (index, _) in _answers(course, unit, lesson).items()}
    submitted = auth_client.post(
        f"/api/learn/courses/A1/lessons/{lesson_id}/checkpoint/submit",
        json={"answers": answers},
    )
    assert submitted.status_code == 200
    result = submitted.json()
    assert result["passed"] is True
    assert result["percent"] == 100

    progress = auth_client.get("/api/progress").json()
    assert progress["lesson_results"][lesson_id]["passed"] is True


def test_checkpoint_fails_below_threshold(auth_client):
    r = auth_client.post(
        "/api/learn/courses/A1/lessons/a1-greetings-l1/checkpoint/submit",
        json={"answers": {}},
    )
    assert r.status_code == 200
    assert r.json()["passed"] is False


def test_unknown_lesson_returns_404(client):
    assert client.get("/api/learn/courses/A1/lessons/does-not-exist").status_code == 404
