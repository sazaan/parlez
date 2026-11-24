"""Original TEF/TCF practice items, written from published task specifications.

Copyright rule (see docs/SOURCE_REGISTER.md): we never reproduce real or past
exam questions, answer keys, audio or PDFs. Every item here is original Parlez
content; only format facts (timing, counts, word limits, skill descriptors)
come from official sources, with links recorded in `spec_source`.
"""

from dataclasses import dataclass

VERIFIED_ON = "2026-11-24"

SPEC_SOURCES = {
    "tef": "https://www.lefrancaisdesaffaires.fr/candidat/test-evaluation-francais/tef-canada/preparation/",
    "tcf": "https://www.france-education-international.fr/en/test/tcf-canada",
    "ircc": "https://canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-requirements/language-testing.html",
}


@dataclass(frozen=True)
class PracticeItem:
    id: str
    exam: str          # TEF | TCF
    skill: str         # reading | listening
    prompt: str
    passage: str
    options: tuple[str, ...]
    answer_index: int
    explanation: str
    spec_fact: str
    spec_source: str
    item_origin: str = "original"
    verified_on: str = VERIFIED_ON


ITEMS = (
    # ---------------- TEF Canada ----------------
    PracticeItem(
        "TEF-CE-O-001", "TEF", "reading",
        "Le dimanche, la pharmacie est fermée…",
        "PHARMACIE SAINT-ROCH — Service de garde. Du lundi au vendredi : 8 h 30 – 19 h 30. Samedi : 9 h – 17 h. Dimanche et jours fériés : 10 h – 13 h et 15 h – 18 h. En dehors de ces horaires, appelez le 15.",
        ("de 13 h à 15 h.", "de 10 h à 18 h.", "de 9 h à 17 h.", "toute la journée."),
        0, "Le dimanche, le service est ouvert de 10 h à 13 h puis de 15 h à 18 h : la fermeture est donc de 13 h à 15 h.",
        "Reading: 40 multiple-choice questions in 60 minutes (TEF Canada).", SPEC_SOURCES["tef"],
    ),
    PracticeItem(
        "TEF-CE-O-002", "TEF", "reading",
        "Choisissez le mot qui convient : « Le dossier de candidature doit être ______ avant le 30 juin. »",
        "Le dossier de candidature doit être ______ avant le 30 juin, faute de quoi l'inscription sera annulée.",
        ("renvoyé", "renvoyer", "renvoie", "renvoyez"),
        0, "Après « être », on utilise le participe passé : « doit être renvoyé ».",
        "TEF reading includes gapped texts testing lexical and grammatical structures.", SPEC_SOURCES["tef"],
    ),
    PracticeItem(
        "TEF-CE-O-003", "TEF", "reading",
        "Quel est le sujet principal de l'article ?",
        "Depuis l'ouverture de la nouvelle ligne de tramway, les commerçants du centre-ville constatent une hausse de fréquentation de 20 %. Toutefois, plusieurs estiment que la suppression des places de stationnement a fait perdre une clientèle qui venait en voiture des communes voisines. La municipalité annonce une étude sur les habitudes de déplacement d'ici la fin de l'automne.",
        ("Les difficultés financières des commerçants.", "Les effets contrastés d'un nouveau tramway sur les commerces.", "La construction d'un parking souterrain.", "Les horaires des transports en commun."),
        1, "L'article présente à la fois des effets positifs et négatifs du nouveau tramway : c'est le sujet principal.",
        "Reading includes press articles testing main idea and detail.", SPEC_SOURCES["tef"],
    ),
    PracticeItem(
        "TEF-CO-O-001", "TEF", "listening",
        "Où et quand se retrouvent-ils ?",
        "— Tu viens avec nous au marché samedi matin ? — Je voudrais bien, mais j'ai un rendez-vous chez le dentiste à 9 heures. — Alors on t'attend à 10 heures devant l'entrée principale ? — D'accord, à tout à l'heure.",
        ("Devant le marché, samedi à 10 h", "Chez le dentiste, samedi à 9 h", "À la gare, dimanche à 10 h", "Au café, samedi à 9 h"),
        0, "Ils conviennent de se retrouver devant l'entrée principale du marché samedi à 10 h.",
        "Listening: 40 questions in 40 minutes; each recording is played once.", SPEC_SOURCES["tef"],
    ),
    PracticeItem(
        "TEF-CO-O-002", "TEF", "listening",
        "Que doivent faire les usagers aujourd'hui ?",
        "Attention, veuillez noter que la salle de lecture de la bibliothèque fermera à 17 heures aujourd'hui en raison d'un problème technique. Les livres peuvent être rendus au comptoir d'accueil jusqu'à 18 heures.",
        ("Rapporter les livres au comptoir avant 18 h", "Ne plus entrer dans la bibliothèque", "Réserver une salle de lecture", "Revenir demain à 17 h"),
        0, "L'annonce précise que les livres peuvent être rendus au comptoir d'accueil jusqu'à 18 h.",
        "Listening: short announcements and public information messages.", SPEC_SOURCES["tef"],
    ),
    # ---------------- TCF Canada ----------------
    PracticeItem(
        "TCF-CE-O-001", "TCF", "reading",
        "Combien paie un étudiant le mercredi ?",
        "CINÉMA LE RIALTO — Tarifs : plein 9 €, tarif réduit 6 € (moins de 18 ans, étudiants, seniors). Séances du mercredi : 7 € pour tous. Ouverture des portes 30 minutes avant la séance.",
        ("6 €", "7 €", "9 €", "5 €"),
        1, "Le tarif du mercredi s'applique à tous, donc 7 € même pour un étudiant.",
        "TCF reading: 39 multiple-choice questions in 60 minutes, progressive difficulty.", SPEC_SOURCES["tcf"],
    ),
    PracticeItem(
        "TCF-CE-O-002", "TCF", "reading",
        "Que propose Julie à Paul ?",
        "Salut Paul, j'ai réservé une table pour samedi soir à 20 h. J'espère que ça te va. Si tu rentres tard, appelle-moi, je commanderai pour toi. À demain, Julie.",
        ("De choisir un autre restaurant", "De réserver une table pour demain", "De commander son repas s'il est en retard", "De l'appeler samedi matin"),
        2, "Julie dit « je commanderai pour toi » si Paul rentre tard.",
        "TCF reading includes short personal messages.", SPEC_SOURCES["tcf"],
    ),
    PracticeItem(
        "TCF-CE-O-003", "TCF", "reading",
        "Quelle position l'auteur défend-il ?",
        "Faut-il interdire les téléphones portables au lycée ? Une interdiction totale empêche d'apprendre à gérer un usage raisonnable. La solution pourrait être un usage encadré, autorisé uniquement pendant les pauses.",
        ("L'interdiction totale", "L'usage libre à tout moment", "Un usage encadré, limité aux pauses", "La suppression des pauses"),
        2, "L'auteur propose un usage encadré, autorisé seulement pendant les pauses.",
        "Later TCF reading items include opinion texts.", SPEC_SOURCES["tcf"],
    ),
    PracticeItem(
        "TCF-CO-O-001", "TCF", "listening",
        "À quelle heure Marie arrivera-t-elle ?",
        "— Allô, c'est Marie. Je serai en retard au rendez-vous de 14 heures. — Pas de problème, je t'attends au café. — Merci, j'arrive vers 14 h 20.",
        ("14 h", "14 h 20", "13 h 40", "15 h"),
        1, "Marie dit « j'arrive vers 14 h 20 ».",
        "TCF listening: 39 questions in 35 minutes; each recording played once.", SPEC_SOURCES["tcf"],
    ),
    PracticeItem(
        "TCF-CO-O-002", "TCF", "listening",
        "Que doit faire le candidat ?",
        "Bonjour, ici le service des inscriptions. Votre dossier est complet, mais il manque la copie de votre passeport. Vous pouvez l'envoyer par courriel avant vendredi ou la déposer au secrétariat.",
        ("Renvoyer le dossier complet", "Envoyer une copie de passeport avant vendredi", "Appeler le service des inscriptions", "Payer des frais supplémentaires"),
        1, "Il manque la copie du passeport : elle peut être envoyée par courriel avant vendredi.",
        "TCF listening includes administrative announcements.", SPEC_SOURCES["tcf"],
    ),
)


def get_items(exam: str, skill: str) -> list[dict]:
    """Client-safe view: no answer index, no scoring key."""
    exam = exam.upper()
    return [
        {
            "id": item.id, "exam": item.exam, "skill": item.skill,
            "prompt": item.prompt, "passage": item.passage,
            "options": list(item.options),
            "specFact": item.spec_fact, "specSource": item.spec_source,
            "itemOrigin": item.item_origin, "verifiedOn": item.verified_on,
        }
        for item in ITEMS if item.exam == exam and item.skill == skill.lower()
    ]


def grade(exam: str, skill: str, answers: dict) -> dict:
    """Server-side grading; returns practice accuracy only, never a score."""
    exam = exam.upper()
    keys = [i for i in ITEMS if i.exam == exam and i.skill == skill.lower()]
    results = []
    correct = 0
    for item in keys:
        given = answers.get(item.id)
        ok = isinstance(given, int) and given == item.answer_index
        if ok:
            correct += 1
        results.append({
            "id": item.id, "correct": ok, "correctIndex": item.answer_index,
            "explanation": item.explanation, "specSource": item.spec_source,
        })
    total = len(keys)
    return {
        "exam": exam, "skill": skill, "correct": correct, "total": total,
        "accuracyPercent": round((correct / total) * 100) if total else 0,
        "results": results,
        "notice": "Original unofficial practice. This is not an official TEF/TCF score, CEFR/NCLC level, or immigration evidence.",
    }
