"""Original, task-led TEF Canada and TCF Canada preparation lessons.

These are unofficial learning materials. They teach strategies and provide
small guided drills; they do not predict scores or certify readiness.
"""

from __future__ import annotations

from copy import deepcopy


STUDY_PLAN = [
    {
        "step": "1. Learn the selected test format",
        "actions": [
            "Read the provider-linked format for TEF Canada or TCF Canada; do not mix their task types.",
            "Choose one skill to practise first and note the official section time and task instructions.",
        ],
    },
    {
        "step": "2. Build one skill at a time",
        "actions": [
            "Work through the skill lesson, then complete a short original practice set.",
            "Review why each choice was right or wrong; record the strategy error, not just the score.",
        ],
    },
    {
        "step": "3. Practise open tasks",
        "actions": [
            "Complete writing and speaking prompts using the task-specific checklist and unofficial criteria.",
            "Repeat with a different prompt; change your plan rather than memorizing a sample response.",
        ],
    },
    {
        "step": "4. Rehearse and review",
        "actions": [
            "Take the full-length reading/listening rehearsal under its displayed time limit.",
            "Return to missed item types, then practise the official section sequence using provider materials.",
        ],
    },
]


_PREPARATION = {
    "TEF": {
        "title": "TEF Canada guided preparation",
        "formatNote": "For TEF Canada: reading and listening are multiple-choice; writing has two sections; speaking has information-gathering and persuasion tasks.",
        "modules": [
            {
                "id": "tef-reading-purpose",
                "skill": "Reading",
                "title": "Find the purpose and the exact detail",
                "durationMinutes": 12,
                "objective": "Identify what a short notice asks or announces, then verify details such as dates, conditions, and exceptions.",
                "teach": [
                    "Before reading closely, identify the document type and audience: notice, message, advertisement, or instructions.",
                    "Turn the question into a search target (who, when, where, condition, or next action).",
                    "Check units, negation, and exceptions; a distractor can repeat a word while changing the condition.",
                ],
                "guidedPractice": {
                    "prompt": "Read: « La piscine ouvrira à 7 h du lundi au vendredi. Samedi, ouverture à 9 h. Fermeture exceptionnelle dimanche. Les abonnements restent disponibles en ligne. » What is different on Sunday?",
                    "answer": "The pool is exceptionally closed on Sunday.",
                    "reasoning": "The Sunday exception is explicit. Online subscriptions remain available, but that does not mean the pool is open.",
                },
                "transferTask": "Use one of the reading sets. For every answer, underline the exact phrase that supports it before selecting an option.",
                "selfCheck": ["I identified the text's purpose.", "I checked the exact date, time, and exception.", "I rejected options that add information not stated."],
            },
            {
                "id": "tef-reading-inference",
                "skill": "Reading",
                "title": "Track contrast, opinion, and inference",
                "durationMinutes": 15,
                "objective": "Separate a writer's position from supporting evidence and infer a conclusion without overstating it.",
                "teach": [
                    "Mark contrast and concession words such as pourtant, toutefois, même si, and en revanche.",
                    "Separate facts, reported views, and the writer's own conclusion.",
                    "Choose the narrowest answer supported by the whole passage; avoid absolute options when the text is qualified.",
                ],
                "guidedPractice": {
                    "prompt": "Read: « Le vélo partagé réduit certains trajets en voiture. Toutefois, dans les quartiers mal desservis, il reste difficile de remplacer la voiture pour les déplacements du soir. » Which conclusion is supported?",
                    "answer": "Shared bicycles help with some trips, but access and travel time limit their use in some areas.",
                    "reasoning": "The passage gives a benefit and a limitation. It does not say that shared bicycles replace all car journeys or that the service has failed.",
                },
                "transferTask": "After a B1/B2 reading item, write one sentence stating the author's position and one detail that limits it.",
                "selfCheck": ["I noticed contrast markers.", "I distinguished the author's view from a reported fact.", "My inference did not go beyond the passage."],
            },
            {
                "id": "tef-listening-details",
                "skill": "Listening",
                "title": "Catch names, numbers, and next actions",
                "durationMinutes": 12,
                "objective": "Use a focused listening target to capture practical information from an announcement or short exchange.",
                "teach": [
                    "Preview the question and predict the kind of information needed before listening.",
                    "Listen for the complete number or time, including corrections (e.g. « non, plutôt… »).",
                    "Distinguish an instruction from a suggestion, and confirm who must take the next action.",
                ],
                "guidedPractice": {
                    "audioText": "Votre rendez-vous est déplacé au jeudi 18 juin à 14 h 30, salle 204. Merci de confirmer votre présence avant mardi.",
                    "prompt": "What must the listener do, and by when?",
                    "answer": "Confirm attendance before Tuesday; the appointment itself is Thursday 18 June at 14:30 in room 204.",
                    "reasoning": "Keep the action deadline separate from the appointment date and time.",
                },
                "transferTask": "In a listening set, jot down only the requested categories (for example time + platform); then compare your notes with the explanation.",
                "selfCheck": ["I predicted what to listen for.", "I kept the appointment time separate from the confirmation deadline.", "I did not choose an option based on one familiar word alone."],
            },
            {
                "id": "tef-listening-stance",
                "skill": "Listening",
                "title": "Follow a longer account and the speaker's position",
                "durationMinutes": 15,
                "objective": "Recognize a speaker's main claim, reasons, and reservations in a longer interview or opinion.",
                "teach": [
                    "Listen for the topic first, then note the claim and one reason or example.",
                    "Treat toutefois, en réalité, and à condition que as signals that refine the speaker's position.",
                    "Separate the speaker's opinion from the host's question or an example quoted from someone else.",
                ],
                "guidedPractice": {
                    "audioText": "Les bibliothèques de quartier attirent davantage de familles depuis l'ajout d'ateliers gratuits. Cependant, certaines ouvrent trop peu le soir pour les personnes qui travaillent. Il faudrait donc adapter les horaires selon les besoins locaux.",
                    "prompt": "What is the speaker's overall recommendation?",
                    "answer": "Keep the useful free workshops and adapt opening hours to local needs, especially for working people.",
                    "reasoning": "The speaker recognizes a benefit, identifies an access problem, and recommends locally adapted hours—not closing the libraries or removing workshops.",
                },
                "transferTask": "After listening, summarize the speaker's claim in one sentence and name one qualification or limitation.",
                "selfCheck": ["I identified the main claim.", "I captured at least one reason.", "I noticed the speaker's reservation or qualification."],
            },
            {
                "id": "tef-writing-continuation",
                "skill": "Writing",
                "title": "Continue the short news item (Section A)",
                "durationMinutes": 25,
                "objective": "Continue a supplied opening as a clear, connected report of at least 80 words within the section's 25-minute allocation.",
                "teach": [
                    "Keep the opening's topic and point of view; add events rather than restarting the story.",
                    "Plan who did what, when, and with what result before drafting.",
                    "Use time markers and a consistent past-time frame; check agreement and punctuation at the end.",
                ],
                "guidedPractice": {
                    "prompt": "Opening: « Un colis inattendu a été déposé mardi devant la mairie de Saint-Roch… » Continue the report in at least 80 words.",
                    "modelPlan": ["Identify what was in the parcel without inventing an unsafe detail.", "Explain who contacted whom and how the parcel was handled.", "End with a verified outcome or a clearly attributed next step."],
                },
                "transferTask": "Complete one TEF writing Section A task in 25 minutes, then revise once for task completion, sequence, and language control.",
                "selfCheck": ["I wrote at least 80 words.", "My continuation fits the opening and has a clear sequence.", "I used links between events and checked past forms."],
            },
            {
                "id": "tef-writing-opinion",
                "skill": "Writing",
                "title": "Build a supported opinion (Section B)",
                "durationMinutes": 35,
                "objective": "Write at least 200 words that state and justify a position in a clear argument within 35 minutes.",
                "teach": [
                    "Decide your position and audience before drafting; answer the precise question.",
                    "Build two distinct reasons and support each with a concrete example.",
                    "Acknowledge one reasonable counterpoint, respond to it, and finish with a concise conclusion.",
                ],
                "guidedPractice": {
                    "prompt": "A town is considering making one central street car-free every Saturday. Write an opinion for a community newsletter (at least 200 words).",
                    "modelPlan": ["Opening: state whether the proposal should be tried.", "Reason 1 + example: safety, access, or local activity.", "Reason 2 + example; acknowledge a concern such as deliveries or accessibility.", "Conclusion: propose a practical condition or review period."],
                },
                "transferTask": "Write a second opinion on a different topic. Do not reuse the same examples; keep the argument specific to the prompt.",
                "selfCheck": ["I wrote at least 200 words and answered the question.", "Each reason has support or an example.", "I addressed a counterpoint and concluded clearly."],
            },
            {
                "id": "tef-speaking-information",
                "skill": "Speaking",
                "title": "Gather information through a natural exchange",
                "durationMinutes": 5,
                "objective": "Use the five-minute information-gathering task to ask relevant questions, follow up, clarify, and confirm key details.",
                "teach": [
                    "Open politely and state why you are calling or asking.",
                    "Move from broad to specific questions: availability, cost/conditions, what to bring, and next step.",
                    "Use a follow-up when an answer is incomplete; paraphrase important details to confirm them.",
                ],
                "guidedPractice": {
                    "prompt": "A community centre offers a weekend photography class. Practise asking about dates, level, equipment, registration, and cancellation conditions.",
                    "modelPlan": ["Bonjour, je vous appelle au sujet de…", "Est-ce que le cours convient aux débutants ?", "Quel matériel faut-il apporter ?", "Si je comprends bien, l'inscription doit être faite avant… ?"],
                },
                "transferTask": "Practise aloud for five minutes with a different service or activity. Have a partner answer so you can ask genuine follow-ups.",
                "selfCheck": ["I asked questions that fit the purpose.", "I used polite openings and follow-ups.", "I clarified and confirmed at least one important detail."],
            },
            {
                "id": "tef-speaking-persuasion",
                "skill": "Speaking",
                "title": "Persuade with reasons, examples, and a response",
                "durationMinutes": 10,
                "objective": "Make a clear proposal, support it, respond respectfully to an objection, and close with a concrete next step.",
                "teach": [
                    "State the proposal early; avoid spending the whole time describing the background.",
                    "Link each reason to a practical benefit and a specific example.",
                    "Acknowledge a concern, answer it, and invite the listener to take one next step.",
                ],
                "guidedPractice": {
                    "prompt": "Persuade a colleague to join a Saturday neighbourhood clean-up, while respecting that they are concerned about the time commitment.",
                    "modelPlan": ["Proposal: invite them to the two-hour event.", "Reason + concrete benefit for the neighbourhood.", "Answer the time concern with the stated schedule and a smaller role.", "Close with a clear question or invitation."],
                },
                "transferTask": "Speak for ten minutes on a new invitation or proposal; ask a partner to raise one realistic objection.",
                "selfCheck": ["My proposal was clear.", "I gave reasons and examples.", "I answered an objection without becoming confrontational."],
            },
        ],
    },
    "TCF": {
        "title": "TCF Canada guided preparation",
        "formatNote": "For TCF Canada: listening and reading use progressively challenging multiple-choice items; writing has three tasks; speaking has interview, interaction, and opinion tasks.",
        "modules": [
            {
                "id": "tcf-reading-practical",
                "skill": "Reading",
                "title": "Read short practical documents efficiently",
                "durationMinutes": 12,
                "objective": "Use the question to locate purpose, conditions, and concrete details in short messages, signs, and notices.",
                "teach": [
                    "Identify the genre before reading every word: advertisement, message, schedule, or instruction.",
                    "Scan for names, dates, quantities, and negation, then read the relevant sentence closely.",
                    "Eliminate options that change who must act or turn a possibility into a certainty.",
                ],
                "guidedPractice": {
                    "prompt": "Read: « Atelier vélo : samedi 10 h–12 h, inscription obligatoire avant jeudi. Casque fourni; apporter son vélo. » What should a participant do before Thursday?",
                    "answer": "Register before Thursday.",
                    "reasoning": "The notice explicitly sets the registration deadline. A helmet is provided, while the participant must bring a bicycle.",
                },
                "transferTask": "In a reading set, state the purpose of each short document in three words before answering its question.",
                "selfCheck": ["I recognized the document type.", "I found the deadline or condition requested.", "I checked who provides or brings each item."],
            },
            {
                "id": "tcf-reading-viewpoint",
                "skill": "Reading",
                "title": "Compare viewpoints and read implied meaning",
                "durationMinutes": 15,
                "objective": "Distinguish viewpoints and supporting reasons, then choose an inference that is warranted by the passage.",
                "teach": [
                    "For each viewpoint, note the claim and its reason separately.",
                    "Use contrast words and attribution phrases to track whose opinion is being reported.",
                    "For inference questions, combine two stated clues but avoid adding outside assumptions.",
                ],
                "guidedPractice": {
                    "prompt": "Read: « Pour Amine, les réunions en ligne évitent des déplacements inutiles. Claire apprécie les échanges à distance, mais dit qu'une première rencontre en personne facilite la confiance. » Which statement best reflects both views?",
                    "answer": "Amine emphasizes travel savings; Claire sees value in remote meetings but prefers an in-person first meeting for trust.",
                    "reasoning": "The answer preserves each person's reason and does not claim that either person rejects all online meetings.",
                },
                "transferTask": "After a B1/B2 reading item, write a two-column note: viewpoint A / viewpoint B, with one supporting clue each.",
                "selfCheck": ["I attributed each opinion to the correct person.", "I used evidence from the whole passage.", "I avoided absolute wording unsupported by the text."],
            },
            {
                "id": "tcf-listening-one-play",
                "skill": "Listening",
                "title": "Prepare for one-play listening",
                "durationMinutes": 12,
                "objective": "Use a focused listening plan for the TCF Canada format, where the official provider states that recordings are played once.",
                "teach": [
                    "In learning mode, replay and read the transcript after answering; in the optional simulation, the audio button is limited to one play.",
                    "Before listening, predict whether the question asks for a person, purpose, place, time, or opinion.",
                    "Do not try to write every word: capture the few details that distinguish the options.",
                ],
                "guidedPractice": {
                    "audioText": "Le rendez-vous prévu mercredi est avancé à mardi, à 16 h. Merci d'apporter le formulaire signé; le bureau ferme à 17 h.",
                    "prompt": "When is the appointment, and what should the person bring?",
                    "answer": "Tuesday at 16:00; the signed form.",
                    "reasoning": "The speaker corrects the original day (Wednesday becomes Tuesday). The closing time is not the appointment time.",
                },
                "transferTask": "Listen once without writing a transcript. Note only the answer target; then replay in study mode and identify the word that changed your understanding.",
                "selfCheck": ["I previewed the answer target.", "I caught the correction from Wednesday to Tuesday.", "I separated the appointment time from the office closing time."],
            },
            {
                "id": "tcf-listening-progression",
                "skill": "Listening",
                "title": "Follow increasing complexity and implied stance",
                "durationMinutes": 15,
                "objective": "Move from explicit details to a speaker's purpose, attitude, and qualification in longer audio.",
                "teach": [
                    "First identify the situation and speaker roles; then follow the main point.",
                    "Notice whether a speaker agrees, hesitates, or qualifies a claim rather than relying on tone alone.",
                    "Compare the options after listening and reject any that reverse a cause, contrast, or recommendation.",
                ],
                "guidedPractice": {
                    "audioText": "Le nouveau service de bus réduit le temps de trajet le matin. En revanche, la fréquence reste insuffisante après 20 h. La ville devrait donc tester des départs plus tardifs avant d'étendre le service.",
                    "prompt": "What does the speaker recommend?",
                    "answer": "Test later departures before expanding the service.",
                    "reasoning": "The speaker recognizes a morning benefit but identifies an evening gap and proposes a limited trial.",
                },
                "transferTask": "After one listening item, write the claim, one supporting detail, and one limitation or recommendation.",
                "selfCheck": ["I identified the main point.", "I connected the contrast to the recommendation.", "I did not mistake a proposed trial for a confirmed decision."],
            },
            {
                "id": "tcf-writing-message-account",
                "skill": "Writing",
                "title": "Plan Tasks 1 and 2 without missing the audience",
                "durationMinutes": 20,
                "objective": "Write a short message (60–120 words) and an organized account/opinion (120–150 words) that meet each prompt's purpose.",
                "teach": [
                    "Task 1: identify recipient, purpose, and required details; use an appropriate greeting and closing when the format calls for them.",
                    "Task 2: organize the account in a clear time/place sequence, then mark your reaction or evaluation distinctly.",
                    "Respect each task's word range; leave time to check missing prompt points and basic agreements.",
                ],
                "guidedPractice": {
                    "prompt": "Task 1 practice: write 60–120 words to a friend proposing a study meeting next week. Include two possible times and ask which suits them.",
                    "modelPlan": ["Friendly opening and purpose.", "Two clear options with dates/times.", "A direct question and concise closing."],
                },
                "transferTask": "Complete one Task 1 message and one Task 2 account. Count words separately and check that each audience is clear.",
                "selfCheck": ["I followed the task's audience and purpose.", "I included all requested details.", "I stayed within the correct word range for each task."],
            },
            {
                "id": "tcf-writing-compare",
                "skill": "Writing",
                "title": "Compare two views and give your own (Task 3)",
                "durationMinutes": 20,
                "objective": "Write 120–180 words that represent both supplied viewpoints fairly and then develop your own position.",
                "teach": [
                    "Make it clear which points belong to the two source viewpoints and which are yours.",
                    "Use contrast and comparison language, but do not merely copy or list the views.",
                    "Give one or two reasons for your position and finish with a conclusion that follows from them.",
                ],
                "guidedPractice": {
                    "prompt": "One viewpoint supports a shared community garden for social connection; another worries that it will be hard to maintain. Compare them and give your own view in 120–180 words.",
                    "modelPlan": ["Briefly and fairly present both views.", "State your position.", "Support it with a practical example and address the strongest concern.", "Conclude with a realistic condition or solution."],
                },
                "transferTask": "Use a different two-viewpoint prompt; mark the source viewpoints and your own position in different colours before drafting.",
                "selfCheck": ["I represented both views fairly.", "I clearly marked my own position.", "I supported my view and stayed within 120–180 words."],
            },
            {
                "id": "tcf-speaking-interview-interaction",
                "skill": "Speaking",
                "title": "Handle the interview and information interaction",
                "durationMinutes": 8,
                "objective": "Give connected answers in the short interview, then ask useful follow-up questions in the information-seeking interaction.",
                "teach": [
                    "Interview: answer the question first, then add one relevant detail or example; there is no preparation time for this task.",
                    "Interaction: use the available preparation time to group questions by topic (schedule, conditions, cost, next step).",
                    "Listen to each answer and adapt the next question instead of reciting a fixed list.",
                ],
                "guidedPractice": {
                    "prompt": "Interview: describe a skill you would like to learn. Interaction: ask a community-centre employee about a beginner cooking class.",
                    "modelPlan": ["Interview: direct answer → reason → example or next step.", "Interaction: polite opening → topic groups → one follow-up → confirm the key detail."],
                },
                "transferTask": "Practise Task 1 for about two minutes. Complete Task 2 within about 5.5 minutes total, including its preparation time; use a partner for authentic follow-ups.",
                "selfCheck": ["My interview answers were connected, not one-word replies.", "I grouped my questions and adapted to the answers.", "I clarified a detail and confirmed the next step."],
            },
            {
                "id": "tcf-speaking-opinion",
                "skill": "Speaking",
                "title": "Develop an opinion in the final task",
                "durationMinutes": 12,
                "objective": "Speak for the task's stated duration with a clear position, connected reasons, examples, and a concise conclusion.",
                "teach": [
                    "Use a simple mental outline: position, reason one + example, reason two + example, qualification, conclusion.",
                    "Keep examples relevant and specific; a short example is more useful than several vague claims.",
                    "If you lose a word, paraphrase and continue instead of stopping to translate.",
                ],
                "guidedPractice": {
                    "prompt": "Some people prefer public transport, while others prefer cycling for short journeys. Which do you prefer, and why?",
                    "modelPlan": ["State a preference without dismissing the alternative.", "Give two reasons with one concrete example.", "Acknowledge one limitation and close with a clear summary."],
                },
                "transferTask": "Practise a fresh opinion topic for about 4.5 minutes without notes; then repeat using only three key words as prompts.",
                "selfCheck": ["I answered the question and stated my view early.", "I linked reasons to examples.", "I maintained intelligibility and concluded clearly."],
            },
        ],
    },
}


def get_exam_preparation(test_type: str) -> dict:
    """Return an independent copy of the unofficial preparation content."""
    return deepcopy(_PREPARATION.get((test_type or "").upper(), {}))


def get_exam_study_plan() -> list[dict]:
    return deepcopy(STUDY_PLAN)
