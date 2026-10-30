"""Additional original TEF Canada / TCF Canada writing and speaking prompts."""

from __future__ import annotations

from .types import ExamTask


WRITING_RUBRIC = [
    "Task completion: answer every part of the prompt and respect the stated word range.",
    "Organization: connect ideas in a sequence that is easy to follow.",
    "Language: choose precise vocabulary and a register suited to the reader.",
    "Control: check sentence forms, agreement, spelling, and punctuation.",
]
SPEAKING_RUBRIC = [
    "Task completion: address the purpose and respond to the listener or prompt.",
    "Organization: connect ideas and make the main point easy to follow.",
    "Language: use relevant vocabulary and a register suited to the situation.",
    "Communication: speak intelligibly, clarify when needed, and keep the exchange moving.",
]


def _task(
    task_id: str,
    family: str,
    variant: int,
    title: str,
    prompt: str,
    instructions: str,
    response_mode: str,
    duration: float | None,
    self_check: list[str],
    *,
    word_min: int | None = None,
    word_max: int | None = None,
    prep_minutes: int = 0,
) -> ExamTask:
    return ExamTask(
        id=task_id,
        title=title,
        prompt=prompt,
        instructions=instructions,
        responseMode=response_mode,
        durationMinutes=duration,
        selfCheck=self_check,
        wordMin=word_min,
        wordMax=word_max,
        prepMinutes=prep_minutes,
        taskFamily=family,
        variantNumber=variant,
        rubric=WRITING_RUBRIC[:] if response_mode == "written" else SPEAKING_RUBRIC[:],
    )


TEF_TASK_VARIATIONS = {
    "writing": [
        _task(
            "tef-writing-a-v2", "writing-1", 2,
            "Task 1 · Continue a news item · Variation 2",
            "Opening: « Un vieux carnet a été retrouvé lundi dans le hall de la gare… » Continue the report. Explain how it was found, who helped identify its owner, and what happened next.",
            "Write at least 80 words. Continue the given opening with a clear sequence of events.",
            "written", 25,
            ["I wrote at least 80 words.", "My report continues the opening rather than replacing it.", "The reader can follow how the events unfolded."],
            word_min=80,
        ),
        _task(
            "tef-writing-a-v3", "writing-1", 3,
            "Task 1 · Continue a news item · Variation 3",
            "Opening: « Une panne a interrompu le marché couvert mercredi matin… » Continue the report. Describe the response, its effect on visitors, and the outcome later that day.",
            "Write at least 80 words. Keep the facts connected and make the outcome clear.",
            "written", 25,
            ["I wrote at least 80 words.", "I included a response and a result.", "I used time markers and checked past-tense consistency."],
            word_min=80,
        ),
        _task(
            "tef-writing-b-v2", "writing-2", 2,
            "Task 2 · Give and support an opinion · Variation 2",
            "A public library is considering opening later two evenings a week and closing earlier on Saturday. Write an opinion for the local newsletter. Do you support this change?",
            "Write at least 200 words. State your position, develop reasons and examples, and address a reasonable concern.",
            "written", 35,
            ["I wrote at least 200 words.", "I linked each main reason to a relevant example.", "I considered a concern and reached a clear conclusion."],
            word_min=200,
        ),
        _task(
            "tef-writing-b-v3", "writing-2", 3,
            "Task 2 · Give and support an opinion · Variation 3",
            "A neighbourhood association wants to replace some street parking with trees and benches. Write an opinion for its public consultation. Do you support the proposal?",
            "Write at least 200 words. Explain your position with reasons, examples, and a response to one opposing view.",
            "written", 35,
            ["I wrote at least 200 words.", "I made my position clear early.", "I supported it with examples and addressed an opposing view."],
            word_min=200,
        ),
    ],
    "speaking": [
        _task(
            "tef-speaking-info-v2", "speaking-1", 2,
            "Task 1 · Ask for information · Variation 2",
            "You are interested in a weekend first-aid course at a community centre. Ask about dates, course level, materials, registration, and cancellation conditions.",
            "Practise the information-gathering exchange for about 5 minutes. Ask follow-up questions and confirm key details.",
            "spoken", 5,
            ["I introduced my reason for calling.", "I asked relevant questions and followed up on answers.", "I confirmed a date or condition before closing."],
        ),
        _task(
            "tef-speaking-info-v3", "speaking-1", 3,
            "Task 1 · Ask for information · Variation 3",
            "You saw an announcement for a guided visit to a local museum. Ask about the route, accessibility, group size, price, and how to reserve a place.",
            "Practise the information-gathering exchange for about 5 minutes. Use polite questions and clarify anything unclear.",
            "spoken", 5,
            ["I used a polite opening and stated the topic.", "I asked about practical details in a useful order.", "I clarified accessibility or booking information."],
        ),
        _task(
            "tef-speaking-persuade-v2", "speaking-2", 2,
            "Task 2 · Persuade someone · Variation 2",
            "Persuade a neighbour to join a shared tool library. They worry about keeping track of borrowed items and whether it will save money.",
            "Speak for about 10 minutes. Explain the proposal, support it with examples, respond to the concerns, and invite a next step.",
            "spoken", 10,
            ["I explained how the shared library would work.", "I responded to both concerns respectfully.", "I made a practical invitation or proposal."],
        ),
        _task(
            "tef-speaking-persuade-v3", "speaking-2", 3,
            "Task 2 · Persuade someone · Variation 3",
            "Persuade a colleague to attend a free evening language-exchange group. They are unsure because they feel nervous speaking with strangers.",
            "Speak for about 10 minutes. Give relevant reasons, suggest a manageable first visit, and respond to the concern.",
            "spoken", 10,
            ["I acknowledged the concern rather than dismissing it.", "I gave practical reasons and a low-pressure first step.", "I ended with a clear invitation."],
        ),
    ],
}

TCF_TASK_VARIATIONS = {
    "writing": [
        _task(
            "tcf-writing-1-v2", "writing-1", 2,
            "Task 1 · Write a short message · Variation 2",
            "Write to a friend about a free event you attended. Say where and when it happened, who was there, and whether you recommend it.",
            "Write 60–120 words for a friend. Include the requested details and a clear personal reaction.",
            "written", None,
            ["I wrote 60–120 words.", "I included where, when, and who.", "I made my recommendation clear."],
            word_min=60, word_max=120,
        ),
        _task(
            "tcf-writing-1-v3", "writing-1", 3,
            "Task 1 · Write a short message · Variation 3",
            "A friend is moving to your city. Write a message recommending one practical place or service and explain how to get there.",
            "Write 60–120 words in an appropriate friendly tone. Give the information your friend needs.",
            "written", None,
            ["I wrote 60–120 words.", "I gave a specific recommendation and useful details.", "I used a friendly opening and closing."],
            word_min=60, word_max=120,
        ),
        _task(
            "tcf-writing-2-v2", "writing-2", 2,
            "Task 2 · Describe an experience · Variation 2",
            "For a community newsletter, describe a group activity you took part in recently. Explain what participants did and what you learned from it.",
            "Write 120–150 words. Organize the account clearly and add your reaction or learning.",
            "written", None,
            ["I wrote 120–150 words.", "I described the activity with concrete details.", "I explained what I learned or thought about it."],
            word_min=120, word_max=150,
        ),
        _task(
            "tcf-writing-2-v3", "writing-2", 3,
            "Task 2 · Describe an experience · Variation 3",
            "For a neighbourhood blog, describe a change that improved a public place you use. Explain what changed and how people use it now.",
            "Write 120–150 words. Give a clear description and a brief evaluation.",
            "written", None,
            ["I wrote 120–150 words.", "I described the change and its effect.", "I separated factual details from my evaluation."],
            word_min=120, word_max=150,
        ),
        _task(
            "tcf-writing-3-v2", "writing-3", 2,
            "Task 3 · Compare viewpoints and give your opinion · Variation 2",
            "Some residents want more outdoor seating in the town centre; others worry it will make pedestrian areas crowded. Present both views and give your opinion.",
            "Write 120–180 words. Represent both viewpoints fairly, then support your own position.",
            "written", None,
            ["I wrote 120–180 words.", "I presented both views fairly.", "I supported my own view with a reason or example."],
            word_min=120, word_max=180,
        ),
        _task(
            "tcf-writing-3-v3", "writing-3", 3,
            "Task 3 · Compare viewpoints and give your opinion · Variation 3",
            "One person supports a four-day workweek for better balance; another worries about service availability and workload. Compare their concerns and state your view.",
            "Write 120–180 words. Compare the viewpoints and develop your own position with support.",
            "written", None,
            ["I wrote 120–180 words.", "I distinguished each viewpoint from my own.", "I concluded with a supported position."],
            word_min=120, word_max=180,
        ),
    ],
    "speaking": [
        _task(
            "tcf-speaking-1-v2", "speaking-1", 2,
            "Task 1 · Guided interview · Variation 2",
            "Talk about a skill you learned outside school. Explain why you chose it, how you practised, and how you might use it in the future.",
            "Practise a connected response for about 2 minutes. There is no preparation time in this task format.",
            "spoken", 2,
            ["I answered the topic directly.", "I connected my experience, reason, and future plan.", "I added at least one specific detail."],
        ),
        _task(
            "tcf-speaking-1-v3", "speaking-1", 3,
            "Task 1 · Guided interview · Variation 3",
            "Describe a place in your community where you like to spend time. Say what you do there and why it matters to you.",
            "Practise a connected response for about 2 minutes. There is no preparation time in this task format.",
            "spoken", 2,
            ["I described the place and my activities there.", "I explained why it matters to me.", "I used connected sentences rather than a list."],
        ),
        _task(
            "tcf-speaking-2-v2", "speaking-2", 2,
            "Task 2 · Obtain information · Variation 2",
            "You are considering joining a local sports centre. Ask an employee about beginner sessions, schedule, equipment, fees, and trial visits.",
            "Practise the information-seeking interaction within about 5.5 minutes total, including up to 2 minutes of preparation.",
            "spoken", 5.5,
            ["I grouped questions by topic.", "I asked a follow-up based on an answer.", "I confirmed the fee or next step."],
            prep_minutes=2,
        ),
        _task(
            "tcf-speaking-2-v3", "speaking-2", 3,
            "Task 2 · Obtain information · Variation 3",
            "You are interested in a library's language-exchange sessions. Ask about levels, meeting times, registration, group size, and what to prepare.",
            "Practise the information-seeking interaction within about 5.5 minutes total, including up to 2 minutes of preparation.",
            "spoken", 5.5,
            ["I asked about the purpose and format of the sessions.", "I adapted a follow-up to an answer.", "I confirmed how to register."],
            prep_minutes=2,
        ),
        _task(
            "tcf-speaking-3-v2", "speaking-3", 2,
            "Task 3 · Express an opinion · Variation 2",
            "Some people prefer shopping at local markets, while others prefer larger supermarkets. Which do you prefer, and why?",
            "Practise a developed response for about 4.5 minutes. There is no preparation time in this task format.",
            "spoken", 4.5,
            ["I stated my preference early.", "I developed it with reasons and examples.", "I acknowledged one reasonable alternative."],
        ),
        _task(
            "tcf-speaking-3-v3", "speaking-3", 3,
            "Task 3 · Express an opinion · Variation 3",
            "Some people believe cities should invest more in public transport; others prioritize road maintenance. What should be the priority, and why?",
            "Practise a developed response for about 4.5 minutes. There is no preparation time in this task format.",
            "spoken", 4.5,
            ["I stated a position on the priority.", "I supported it with relevant reasons.", "I addressed a possible trade-off and concluded."],
        ),
    ],
}
