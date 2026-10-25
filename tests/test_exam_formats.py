"""Canada-specific exam format and practice-pathway regression tests."""

import main


def test_tef_canada_and_tcf_canada_are_distinct_paths(client):
    tef_response = client.get("/api/exam/sets/TEF")
    tcf_response = client.get("/api/exam/sets/TCF")
    assert tef_response.status_code == tcf_response.status_code == 200
    tef, tcf = tef_response.json(), tcf_response.json()

    assert tef["name"] == "TEF Canada"
    assert tcf["name"] == "TCF Canada"
    assert tef["formatSourceUrl"].endswith("/tef-canada/examination/")
    assert tcf["formatSourceUrl"].endswith("/test/tcf-canada")
    assert "unofficial" in tef["practiceNotice"].lower()
    assert "unofficial" in tcf["practiceNotice"].lower()

    tef_sections = tef["sections"]
    tcf_sections = tcf["sections"]
    assert set(tef_sections) == {"reading", "listening", "writing", "speaking"}
    assert set(tcf_sections) == {"reading", "listening", "writing", "speaking"}
    assert tef_sections["reading"]["questionCount"] == 40
    assert tef_sections["reading"]["durationMinutes"] == 60
    assert tef_sections["listening"]["questionCount"] == 40
    assert tef_sections["listening"]["durationMinutes"] == 40
    assert tcf_sections["reading"]["questionCount"] == 39
    assert tcf_sections["reading"]["durationMinutes"] == 60
    assert tcf_sections["listening"]["questionCount"] == 39
    assert tcf_sections["listening"]["durationMinutes"] == 35
    assert tef_sections["writing"]["taskCount"] == 2
    assert tef_sections["writing"]["durationMinutes"] == 60
    assert tcf_sections["writing"]["taskCount"] == 3
    assert tcf_sections["writing"]["durationMinutes"] == 60
    assert tef_sections["speaking"]["taskCount"] == 2
    assert tef_sections["speaking"]["durationMinutes"] == 15
    assert tcf_sections["speaking"]["taskCount"] == 3
    assert tcf_sections["speaking"]["durationMinutes"] == 12
    assert "vocabulary_grammar" not in tef_sections
    assert "language_structures" not in tcf_sections

    # Official counts are separate from the intentionally shorter practice sets.
    assert tef_sections["reading"]["practiceQuestionCount"] < tef_sections["reading"]["questionCount"]
    assert tcf_sections["listening"]["practiceQuestionCount"] < tcf_sections["listening"]["questionCount"]


def test_original_writing_and_speaking_practice_tasks_are_exposed(client):
    tef = client.get("/api/exam/sets/TEF").json()
    tcf = client.get("/api/exam/sets/TCF").json()
    tef_writing = tef["sections"]["writing"]["tasks"]
    tcf_writing = tcf["sections"]["writing"]["tasks"]
    assert len(tef_writing) == 2
    assert [task["wordMin"] for task in tef_writing] == [80, 200]
    assert len(tcf_writing) == 3
    assert [(task["wordMin"], task["wordMax"]) for task in tcf_writing] == [(60, 120), (120, 150), (120, 180)]
    assert all(task["durationMinutes"] is None for task in tcf_writing)
    assert len(tef["sections"]["speaking"]["tasks"]) == 2
    assert len(tcf["sections"]["speaking"]["tasks"]) == 3
    assert tcf["sections"]["speaking"]["tasks"][1]["prepMinutes"] == 2
    assert all(task["selfCheck"] for task in tef_writing + tcf_writing)

    task_response = client.get("/api/exam/tasks/TEF/writing/tef-writing-task-1")
    assert task_response.status_code == 200
    task = task_response.json()
    assert task["task"]["responseMode"] == "written"
    assert "mystérieux" in task["task"]["prompt"]
    assert task["formatSourceUrl"].endswith("/tef-canada/examination/")


def test_exam_practice_accuracy_is_not_reported_as_a_level(auth_client):
    response = auth_client.post("/api/exam/submit/TEF/reading/1", json={"answers": {}})
    assert response.status_code == 200
    result = response.json()
    assert result["total"] > 0
    assert result["score"] == 0
    assert "level" not in result
    assert "levelBreakdown" not in result
    assert "not an official" in result["scoreNote"].lower()

    stats = auth_client.get("/api/exam/stats/TEF").json()
    assert "by_level" not in stats
    assert "not an official" in stats["scoreNote"].lower()

    # Old stored results can still have threshold-based level labels; public
    # history APIs must not repeat those unsupported legacy claims.
    legacy_user = main.storage.get_user_by_username("testuser")
    legacy_user.setdefault("test_results", []).append({
        "testType": "TEF", "section": "reading", "score": 99,
        "level": "C1", "levelBreakdown": {"B2": {"correct": 9, "total": 10}},
    })
    main.storage.save_user(legacy_user)
    for result in auth_client.get("/api/exam/history/TEF").json() + auth_client.get("/api/test-results").json():
        assert "level" not in result
        assert "levelBreakdown" not in result
