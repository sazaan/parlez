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

    # The three short drills contain 45 unique original items; the timed rehearsal reuses them.
    assert tef_sections["reading"]["practiceQuestionCount"] == 45
    assert tcf_sections["listening"]["practiceQuestionCount"] == 45

    # Each test has its own original four-skill teaching path and study sequence.
    assert len(tef["preparation"]["modules"]) == 8
    assert len(tcf["preparation"]["modules"]) == 8
    assert {module["skill"] for module in tef["preparation"]["modules"]} == {"Reading", "Listening", "Writing", "Speaking"}
    assert {module["skill"] for module in tcf["preparation"]["modules"]} == {"Reading", "Listening", "Writing", "Speaking"}
    assert len(tef["studyPlan"]) == len(tcf["studyPlan"]) == 4
    assert "TEF Canada" in tef["preparation"]["title"]
    assert "TCF Canada" in tcf["preparation"]["title"]
    for preparation in (tef["preparation"], tcf["preparation"]):
        modules = preparation["modules"]
        assert len({module["id"] for module in modules}) == 8
        assert all(module["objective"] and module["teach"] and module["guidedPractice"] and module["transferTask"] and module["selfCheck"] for module in modules)
        assert all(any(module["skill"] == skill for module in modules) for skill in ("Reading", "Listening", "Writing", "Speaking"))
        listening_modules = [module for module in modules if module["skill"] == "Listening"]
        assert all(module["guidedPractice"].get("audioText") for module in listening_modules)


def test_full_length_rehearsals_match_official_objective_section_counts(client):
    for test_type, counts, durations in [
        ("TEF", {"reading": 40, "listening": 40}, {"reading": 60, "listening": 40}),
        ("TCF", {"reading": 39, "listening": 39}, {"reading": 60, "listening": 35}),
    ]:
        sets = client.get(f"/api/exam/sets/{test_type}").json()["sections"]
        for skill in ("reading", "listening"):
            drills = sets[skill]["sets"]
            assert [item["setNum"] for item in drills] == [1, 2, 3, 4]
            assert all(item["questionCount"] == 15 for item in drills[:3])
            assert all(item["timeLimitMinutes"] == round(durations[skill] * 15 / counts[skill], 1) for item in drills[:3])
            assert all(item["timeLimitMinutes"] < durations[skill] for item in drills[:3])
            assert drills[3]["fullLengthSimulation"] is True
            assert drills[3]["reusesShortPracticeItems"] is True
            assert drills[3]["questionCount"] == counts[skill]
            assert drills[3]["timeLimitMinutes"] == durations[skill]

            response = client.get(f"/api/exam/questions/{test_type}/{skill}/4")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == counts[skill]
            assert data["fullLengthSimulation"] is True
            assert data["timeLimitMinutes"] == durations[skill]
            assert data["reusesShortPracticeItems"] is True
            assert all("answer" not in q and "explanation" not in q for q in data["questions"])
            assert len({q["id"] for q in data["questions"]}) == counts[skill]

    assert client.get("/api/exam/questions/TCF/listening/4").json()["singlePlayAudio"] is True
    assert client.get("/api/exam/questions/TCF/listening/1").json()["singlePlayAudio"] is False
    assert client.get("/api/exam/questions/TEF/listening/4").json()["singlePlayAudio"] is False


def test_original_writing_and_speaking_practice_tasks_are_exposed(client):
    tef = client.get("/api/exam/sets/TEF").json()
    tcf = client.get("/api/exam/sets/TCF").json()
    tef_writing = tef["sections"]["writing"]["tasks"]
    tcf_writing = tcf["sections"]["writing"]["tasks"]
    assert len(tef_writing) == 6
    assert [task["wordMin"] for task in tef_writing[:2]] == [80, 200]
    assert [task["durationMinutes"] for task in tef_writing[:2]] == [25, 35]
    assert len(tcf_writing) == 9
    assert [(task["wordMin"], task["wordMax"]) for task in tcf_writing[:3]] == [(60, 120), (120, 150), (120, 180)]
    assert all(task["durationMinutes"] is None for task in tcf_writing[:3])
    tef_speaking = tef["sections"]["speaking"]["tasks"]
    tcf_speaking = tcf["sections"]["speaking"]["tasks"]
    assert len(tef_speaking) == 6
    assert len(tcf_speaking) == 9
    assert tcf_speaking[1]["prepMinutes"] == 2
    all_tasks = tef_writing + tcf_writing + tef_speaking + tcf_speaking
    assert all(task["selfCheck"] and task["rubric"] for task in all_tasks)
    assert len({task["id"] for task in all_tasks}) == len(all_tasks)
    for tasks, official_slots in ((tef_writing, 2), (tef_speaking, 2), (tcf_writing, 3), (tcf_speaking, 3)):
        families = {task["taskFamily"] for task in tasks}
        assert len(families) == official_slots
        for family in families:
            assert {task["variantNumber"] for task in tasks if task["taskFamily"] == family} == {1, 2, 3}

    task_response = client.get("/api/exam/tasks/TEF/writing/tef-writing-task-1")
    assert task_response.status_code == 200
    task = task_response.json()
    assert task["task"]["responseMode"] == "written"
    assert "mystérieux" in task["task"]["prompt"]
    assert task["task"]["rubric"]
    assert task["formatSourceUrl"].endswith("/tef-canada/examination/")

    variation = client.get("/api/exam/tasks/TCF/speaking/tcf-speaking-3-v3")
    assert variation.status_code == 200
    assert variation.json()["task"]["variantNumber"] == 3
    assert variation.json()["task"]["responseMode"] == "spoken"

    for test_type, expected_count in (("TEF", 6), ("TCF", 9)):
        writing_section = client.get(f"/api/exam/sets/{test_type}/writing")
        assert writing_section.status_code == 200
        assert writing_section.json()["durationMinutes"] == 60
        assert len(writing_section.json()["tasks"]) == expected_count


def test_exam_practice_accuracy_is_not_reported_as_a_level(auth_client):
    response = auth_client.post("/api/exam/submit/TEF/reading/1", json={"answers": {}})
    assert response.status_code == 200
    result = response.json()
    assert result["total"] > 0
    assert result["score"] == 0
    assert "level" not in result
    assert "levelBreakdown" not in result
    assert "not an official" in result["scoreNote"].lower()

    rehearsal = auth_client.post("/api/exam/submit/TCF/listening/4", json={"answers": {}})
    assert rehearsal.status_code == 200
    assert rehearsal.json()["total"] == 39
    assert rehearsal.json()["fullLengthSimulation"] is True
    assert "not an official" in rehearsal.json()["scoreNote"].lower()

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
