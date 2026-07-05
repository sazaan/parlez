from .types import *
from .expanded_data import TEF_EXPANDED, TCF_EXPANDED

PRACTICE_SETS_COUNT = 6  # 5 pre-built + 1 AI-generated

tef_format = ExamFormat(
    type='TEF', name='TEF', fullName="Test d'Évaluation de Français",
    color='#1D4ED8',
    description="The TEF is an international reference test for French proficiency.",
    administeredBy='Paris Île-de-France CCI (CCIP)',
    usedFor='Canada immigration, French citizenship, university admission',
    sections=[
        ExamSection(id='reading', title='Reading Comprehension', titleFr='Compréhension écrite', description='50 questions in 3 sections. 60 minutes.', icon='📖', questionCount=50, durationMinutes=60),
        ExamSection(id='listening', title='Listening Comprehension', titleFr='Compréhension orale', description='60 questions. 40 minutes.', icon='🎧', questionCount=60, durationMinutes=40),
        ExamSection(id='vocabulary_grammar', title='Vocabulary & Grammar', titleFr='Lexique et structure', description='40 questions. 30 minutes.', icon='✏️', questionCount=40, durationMinutes=30),
    ],
)

tcf_format = ExamFormat(
    type='TCF', name='TCF', fullName='Test de Connaissance du Français',
    color='#B91C1C',
    description="The TCF is the French Ministry of Education's test.",
    administeredBy='France Éducation International (FEI)',
    usedFor='French nationality, residency, Quebec CSQ, university admission',
    sections=[
        ExamSection(id='listening', title='Listening Comprehension', titleFr='Compréhension orale', description='29 questions progressive difficulty. 25 minutes.', icon='🎧', questionCount=29, durationMinutes=25),
        ExamSection(id='language_structures', title='Language Structures', titleFr='Maîtrise des structures', description='18 questions grammar/vocab. 15 minutes.', icon='✏️', questionCount=18, durationMinutes=15),
        ExamSection(id='reading', title='Reading Comprehension', titleFr='Compréhension écrite', description='29 questions progressive difficulty. 45 minutes.', icon='📖', questionCount=29, durationMinutes=45),
    ],
)

exam_formats = {'TEF': tef_format, 'TCF': tcf_format}

tef_reading_questions = [
    TestQuestion(id='tef-r-1', level='A1', prompt="Read the message:\n\n\"Chère Marie, je ne pourrai pas venir dîner ce soir. J'ai trop de travail. On se voit samedi ? Bisous, Sophie.\"", options=['Sophie viendra dîner ce soir.', 'Sophie ne viendra pas dîner ce soir.', 'Marie ne veut pas dîner avec Sophie.', 'Sophie dîne samedi soir avec Marie.'], answer=1, explanation="Sophie says she will NOT come."),
    TestQuestion(id='tef-r-2', level='A2', prompt='Read the sign:\n\n"FERMÉ LE LUNDI. Ouvert mardi au samedi : 9h - 19h. Dimanche : 9h - 13h."', options=['Le magasin est ouvert le lundi.', 'Le magasin ferme à 19h le dimanche.', 'Le magasin est ouvert le dimanche matin.', 'Le magasin ferme à 13h le samedi.'], answer=2, explanation='Dimanche: 9h-13h means Sunday morning.'),
    TestQuestion(id='tef-r-3', level='A2', prompt='Read:\n\n"RECHERCHE : Appartement 2 pièces à Lyon, max 800€/mois."', options=['Paul vend un appartement.', 'Paul cherche un appartement à Lyon.', 'Paul a un appartement à louer.', 'Paul habite à Lyon.'], answer=1, explanation='RECHERCHE means looking for.'),
    TestQuestion(id='tef-r-4', level='B1', prompt='Read:\n\n"Le télétravail a augmenté de 30% depuis 2020. Cependant, 45% des employés regrettent le manque de contacts sociaux."', options=['Le télétravail a baissé.', 'Tous les employés aiment le télétravail.', 'Le télétravail a augmenté mais pose des problèmes sociaux.', 'Le télétravail a baissé de 45%.'], answer=2, explanation='Increased 30% but 45% regret social lack.'),
    TestQuestion(id='tef-r-5', level='B1', prompt='Read:\n\n"Votre colis sera livré le 15 mars entre 14h et 17h. Veuillez être présent."', options=['Le colis sera livré le matin.', 'Le colis sera perdu si absent.', 'Le client doit être présent l\'après-midi.', 'Le colis sera livré sans rendez-vous.'], answer=2, explanation='Livré entre 14h et 17h = afternoon.'),
    TestQuestion(id='tef-r-6', level='B2', prompt='Read:\n\n"Malgré les critiques, la réforme des retraites a été adoptée. Le gouvernement affirme qu\'elle est nécessaire, les syndicats dénoncent une injustice."', options=['Tout le monde est d\'accord.', 'Le gouvernement et les syndicats ont des opinions opposées.', 'Les syndicats soutiennent la réforme.', 'La réforme a été rejetée.'], answer=1, explanation='Government supports, unions oppose.'),
    TestQuestion(id='tef-r-7', level='B2', prompt='Read:\n\n"L\'IA s\'infiltre dans notre quotidien. Si elle facilite certaines tâches, elle soulève aussi des questions éthiques."', options=['L\'IA reste dans les laboratoires.', 'L\'IA ne pose aucun problème.', 'L\'IA a des avantages et des inconvénients.', 'L\'IA est rejetée.'], answer=2, explanation='Benefits + ethical questions.'),
    TestQuestion(id='tef-r-8', level='A1', prompt='Read:\n\n"Bonjour, je m\'appelle Lucas. J\'ai 25 ans. Je suis étudiant à l\'université de Lyon."', options=['Lucas a 20 ans.', 'Lucas travaille à Lyon.', 'Lucas est étudiant.', 'Lucas habite avec un chien.'], answer=2, explanation='"Je suis étudiant" = Lucas is a student.'),
    TestQuestion(id='tef-r-9', level='A2', prompt='Read:\n\n"MÉTÉO : Demain, temps nuageux le matin. L\'après-midi, le soleil. 15°C matin, 22°C après-midi."', options=['Il pleuvra toute la journée.', 'Il fera beau toute la journée.', 'Le soleil apparaîtra l\'après-midi.', 'Les températures seront négatives.'], answer=2, explanation='"L\'après-midi, le soleil"'),
    TestQuestion(id='tef-r-10', level='B1', prompt='Read:\n\n"Pour louer un vélo : 1) Téléchargez l\'app. 2) Créez un compte. 3) Scannez le QR code. Le premier quart d\'heure est gratuit."', options=['Payant dès la 1ère minute.', 'Il faut créer un compte.', 'Les 30 premières minutes sont gratuites.', 'Pas d\'application.'], answer=1, explanation='Step 2: create account first.'),
]

tef_listening_questions = [
    TestQuestion(id='tef-l-1', level='A1', prompt='What does the person want?', audioText="Bonjour, je voudrais un café et un croissant, s'il vous plaît.", options=['A tea and a cake', 'A coffee and a croissant', 'A glass of water', 'A sandwich'], answer=1, explanation='un café et un croissant.'),
    TestQuestion(id='tef-l-2', level='A1', prompt='What time is it?', audioText="Excusez-moi, vous avez l'heure ? Il est exactement quinze heures trente.", options=['3:30 AM', '3:30 PM', '5:30 PM', '15:00'], answer=1, explanation='15h30 = 3:30 PM.'),
    TestQuestion(id='tef-l-3', level='A2', prompt='Where is the train station?', audioText="Pour aller à la gare, allez tout droit, puis tournez à droite. C'est à cinq minutes à pied.", options=['La gare est très loin.', 'La gare est à cinq minutes à pied.', 'La gare est à gauche.', 'La gare est en face.'], answer=1, explanation='cinq minutes à pied.'),
    TestQuestion(id='tef-l-4', level='A2', prompt='Listen to the announcement:', audioText="Le train à destination de Lyon Part-Dieu va partir en voie 5. Veuillez embarquer immédiatement.", options=['Train arriving from Lyon.', 'Train to Lyon leaving from platform 5.', 'Train is delayed.', 'Train goes to Paris.'], answer=1, explanation='Train to Lyon, platform 5.'),
    TestQuestion(id='tef-l-5', level='B1', prompt='What did they do this weekend?', audioText="Tu as passé un bon week-end ? — Oui, je suis allée au cinéma. Et toi ? — Moi, je suis resté à la maison, j'ai lu un livre.", options=['Both went out.', 'One person went to cinema.', 'Both saw a film.', 'No one enjoyed.'], answer=1, explanation='One cinema, one stayed home.'),
    TestQuestion(id='tef-l-6', level='B1', prompt='What does the survey say?', audioText="60% des Français considèrent que le télétravail améliore leur qualité de vie. Cependant, 30% se sentent parfois isolés.", options=['Most hate remote work.', '60% think it improves quality of life.', '30% prefer office always.', 'No one feels isolated.'], answer=1, explanation='60% say improves quality of life.'),
    TestQuestion(id='tef-l-7', level='B2', prompt='Speaker\'s position on AI?', audioText="D'une part, l'IA nous fait gagner du temps. D'autre part, elle pose des questions éthiques. Il faudrait donc réguler.", options=['Opposes AI completely.', 'Sees both advantages and disadvantages.', 'AI should not be regulated.', 'AI is perfect.'], answer=1, explanation='Both sides presented.'),
    TestQuestion(id='tef-l-8', level='A2', prompt='Weather forecast?', audioText="Demain, temps ensoleillé dans le sud, nuages dans le nord. 25°C à Marseille.", options=['Beau partout.', 'Pluie dans le sud.', '25°C à Marseille.', 'Froid dans le nord.'], answer=2, explanation='25 degrees in Marseille.'),
    TestQuestion(id='tef-l-9', level='A1', prompt='How many children does Marie have?', audioText="Bonjour, je m'appelle Marie. J'habite à Bordeaux et je suis professeure. J'ai deux enfants.", options=['Marie is a doctor.', 'Marie has two children.', 'Marie lives in Paris.', 'Marie has no children.'], answer=1, explanation='J\'ai deux enfants.'),
    TestQuestion(id='tef-l-10', level='A1', prompt='What does the person want to buy?', audioText="Excusez-moi, je cherche une robe pour une soirée. Vous avez quelque chose de bleu ?", options=['A blue dress for a party.', 'A red skirt.', 'A white shirt.', 'Black shoes.'], answer=0, explanation='A blue dress for a party.'),
]

tef_vocab_grammar_questions = [
    TestQuestion(id='tef-vg-1', level='A1', prompt='Complete: "Je _____ étudiant."', options=['es', 'est', 'suis', 'sommes'], answer=2, explanation='Je suis = I am.'),
    TestQuestion(id='tef-vg-2', level='A1', prompt='"Bonsoir" is used in the:', options=['Morning', 'Afternoon', 'Evening', 'At bedtime'], answer=2, explanation='Bonsoir = evening.'),
    TestQuestion(id='tef-vg-3', level='A2', prompt='Complete: "Hier, j\'ai mangé au restaurant."', options=['ai', 'étais', 'avais', 'suis'], answer=0, explanation='J\'ai mangé = passé composé with avoir.'),
    TestQuestion(id='tef-vg-4', level='A2', prompt='Which preposition? "Je vais _____ Italie."', options=['au', 'en', 'aux', 'à la'], answer=1, explanation='Italie is feminine → en.'),
    TestQuestion(id='tef-vg-5', level='B1', prompt='Complete: "Il faut que tu _____."', options=['viens', 'viennes', 'venir', 'venirs'], answer=1, explanation='Subjunctive after il faut que.'),
    TestQuestion(id='tef-vg-6', level='B1', prompt='Which means "however"?', options=['De plus', 'Ensuite', 'Cependant', 'Donc'], answer=2, explanation='Cependant = however.'),
    TestQuestion(id='tef-vg-7', level='B2', prompt='"Verlan" of "femme" is:', options=['famme', 'meuf', 'femme', 'feume'], answer=1, explanation='Verlan reverses syllables.'),
    TestQuestion(id='tef-vg-8', level='B2', prompt='Formal way to say "I don\'t know":', options=['J\'en sais rien', 'Je ne sais pas', 'Je l\'ignore', 'No idea'], answer=2, explanation='Je l\'ignore is formal.'),
    TestQuestion(id='tef-vg-9', level='A1', prompt='What is "15" in French?', options=['quatorze', 'quinze', 'seize', 'treize'], answer=1, explanation='15 = quinze.'),
    TestQuestion(id='tef-vg-10', level='A2', prompt='Past participle of "prendre":', options=['prendu', 'pris', 'prendi', 'prendre'], answer=1, explanation='Prendre → pris.'),
]

tef_test = MockTest(
    type='TEF', name='TEF', fullName="Test d'Évaluation de Français",
    description="International French proficiency test for immigration and citizenship.",
    administeredBy='Paris Île-de-France CCI (CCIP)',
    usedFor='Canada immigration, French citizenship, university admission',
    color='#1D4ED8',
    sections=[
        TestSectionData(id='reading', title='Reading Comprehension', titleFr='Compréhension écrite', description='Read texts and answer. Practice: 10 questions.', icon='📖', questionCount=10, durationMinutes=12, questions=tef_reading_questions),
        TestSectionData(id='listening', title='Listening Comprehension', titleFr='Compréhension orale', description='Listen to audio and answer. Practice: 10 questions.', icon='🎧', questionCount=10, durationMinutes=10, questions=tef_listening_questions),
        TestSectionData(id='vocabulary_grammar', title='Vocabulary & Grammar', titleFr='Lexique et structure', description='Vocabulary and grammar. Practice: 10 questions.', icon='✏️', questionCount=10, durationMinutes=8, questions=tef_vocab_grammar_questions),
    ],
)

tcf_reading_questions = [
    TestQuestion(id='tcf-r-1', level='A1', prompt='Read:\n\n"Salut Léa, c\'est Tom. Je suis à la boulangerie. Tu veux quelque chose ?"', options=['Tom is at home.', 'Tom is at the bakery.', 'Tom is at the bank.', 'Tom is at school.'], answer=1, explanation='Je suis à la boulangerie.'),
    TestQuestion(id='tcf-r-2', level='A1', prompt='Read:\n\n"HORAIRES: Lundi-Vendredi: 9h-18h. Samedi: 10h-16h. Dimanche: Fermé"', options=['Open Sunday 10-16.', 'Open Saturday 10-16.', 'Open Monday 8-18.', 'Closed Saturday.'], answer=1, explanation='Samedi: 10h-16h.'),
    TestQuestion(id='tcf-r-3', level='A2', prompt='Read:\n\n"Une fuite d\'eau aura lieu demain 9h-11h dans le bâtiment B. L\'eau sera coupée."', options=['Water cut 2h in building B.', 'Water cut all day.', 'Leak happening now.', 'Water is fine.'], answer=0, explanation='Coupée pendant deux heures.'),
    TestQuestion(id='tcf-r-4', level='A2', prompt='Read the recipe:\n\n"Omelette: cassez 3 œufs, battez-les, ajoutez sel et poivre. Faites chauffer beurre, versez, cuire 3 minutes."', options=['Need 5 eggs.', 'No butter needed.', 'Cooking takes 3 minutes.', 'No salt needed.'], answer=2, explanation='Laissez cuire 3 minutes.'),
    TestQuestion(id='tcf-r-5', level='B1', prompt='Read:\n\n"Nous avons le plaisir de vous convier à un entretien le 15 mars à 14h."', options=['Candidate rejected.', 'Invited to interview March 15.', 'Interview online.', 'Candidate hired.'], answer=1, explanation='Convier à un entretien le 15 mars.'),
    TestQuestion(id='tcf-r-6', level='B1', prompt='Read:\n\n"Le festival de Nice attire 50 000 visiteurs. L\'édition met à l\'honneur les artistes méditerranéens du 12 au 15 juillet."', options=['Festival in June.', '50,000 live in Nice.', 'Features Mediterranean artists.', 'Festival is free.'], answer=2, explanation='Artistes méditerranéens.'),
    TestQuestion(id='tcf-r-7', level='B2', prompt='Read:\n\n"La réforme permettrait d\'économiser 12 milliards d\'euros par an."', options=['Cost 12 billion.', 'Save 12 billion per year.', 'Reform rejected.', 'Affects only teachers.'], answer=1, explanation='Économiser = save.'),
    TestQuestion(id='tcf-r-8', level='A1', prompt='Read:\n\n"MENU: Entrée: Salade verte. Plat: Poulet frites. Dessert: Fromage."', options=['4 courses.', 'No dessert.', 'Main course is chicken with fries.', 'Starter is soup.'], answer=2, explanation='Plat: Poulet frites.'),
    TestQuestion(id='tcf-r-9', level='A2', prompt='Read:\n\n"Recherche colocataire pour T3 à Bordeaux. Loyeur: 450€/mois."', options=['Selling apartment.', 'Looking for flatmate.', 'Apartment costs 450€ total.', 'In Paris.'], answer=1, explanation='Recherche colocataire.'),
    TestQuestion(id='tcf-r-10', level='B2', prompt='Read:\n\n"Les températures pourraient augmenter de 2,7°C d\'ici 2100 si aucune mesure n\'est prise."', options=['Will definitely rise 2.7°C.', 'Could rise 2.7°C if nothing is done.', 'About ocean levels.', 'GIEC is weather service.'], answer=1, explanation='Pourraient si aucune mesure.'),
]

tcf_listening_questions = [
    TestQuestion(id='tcf-l-1', level='A1', prompt='Where is Tom?', audioText="Salut Léa, c'est Tom. Je suis à la boulangerie.", options=['At home.', 'At the bakery.', 'At the bank.', 'At school.'], answer=1, explanation='À la boulangerie.'),
    TestQuestion(id='tcf-l-2', level='A1', prompt='What time does the store close?', audioText="Le magasin ferme à dix-huit heures.", options=['6 AM', '6 PM', '8 PM', 'Noon'], answer=1, explanation='18h = 6 PM.'),
    TestQuestion(id='tcf-l-3', level='A2', prompt='Where are they going?', audioText="On va au cinéma ce soir ?", options=['Restaurant.', 'Cinema.', 'Park.', 'Gym.'], answer=1, explanation='Au cinéma.'),
    TestQuestion(id='tcf-l-4', level='A2', prompt='What does the person need?', audioText="J'ai mal à la tête. J'ai besoin d'un médicament.", options=['A doctor.', 'A dentist.', 'Medicine for headache.', 'Glasses.'], answer=2, explanation='Médicament for headache.'),
    TestQuestion(id='tcf-l-5', level='B1', prompt='What happened to the train?', audioText="Le train de 14h est retardé de trente minutes.", options=['Cancelled.', '30 minutes late.', 'Left early.', 'Goes to Paris.'], answer=1, explanation='Retardé de trente minutes.'),
    TestQuestion(id='tcf-l-6', level='B1', prompt='What is the news about?', audioText="Le nombre de touristes à Paris a augmenté de 15% ce trimestre.", options=['Tourism decreased.', 'Louvre most visited.', 'Tourism increased 15%.', 'Museums closing.'], answer=2, explanation='Augmenté de 15%.'),
    TestQuestion(id='tcf-l-7', level='B2', prompt='Speaker\'s opinion?', audioText="Le télétravail offre une flexibilité appréciable, mais un modèle hybride serait idéal.", options=['Prefers full remote.', 'Prefers full office.', 'Recommends hybrid model.', 'Opposes remote work.'], answer=2, explanation='Modèle hybride serait idéal.'),
    TestQuestion(id='tcf-l-8', level='A1', prompt='What does the person want to eat?', audioText="Je voudrais une pizza margherita.", options=['A burger.', 'A pizza margherita.', 'A salad.', 'A steak.'], answer=1, explanation='Une pizza margherita.'),
    TestQuestion(id='tcf-l-9', level='A2', prompt='How is the weather?', audioText="Il fait beau et chaud. 30 degrés.", options=['Cold and rainy.', 'Hot and sunny.', 'Cloudy.', 'Snowing.'], answer=1, explanation='Beau et chaud, 30 degrés.'),
    TestQuestion(id='tcf-l-10', level='B2', prompt='Main topic?', audioText="L'IA devrait être un outil complémentaire, pas un remplacement du professeur.", options=['AI should replace teachers.', 'AI is dangerous.', 'AI should complement teachers.', 'Academy opposes tech.'], answer=2, explanation='Complémentaire, pas remplacement.'),
]

tcf_language_questions = [
    TestQuestion(id='tcf-ls-1', level='A1', prompt='Complete: "Je _____ français."', options=['es', 'est', 'suis', 'sommes'], answer=2, explanation='Je suis.'),
    TestQuestion(id='tcf-ls-2', level='A1', prompt='Correct: "Elle _____ à Paris."', options=['habite', 'habites', 'habitent', 'habiter'], answer=0, explanation='Elle habite.'),
    TestQuestion(id='tcf-ls-3', level='A2', prompt='Complete: "Nous _____ mangé."', options=['avons', 'ai', 'as', 'a'], answer=0, explanation='Nous avons mangé.'),
    TestQuestion(id='tcf-ls-4', level='A2', prompt='"Avoir" in "J\'ai vingt ans" means:', options=['To eat', 'To have', 'To be (age)', 'To go'], answer=2, explanation='Avoir + age = to be.'),
    TestQuestion(id='tcf-ls-5', level='B1', prompt='Subjunctive of "être" for "que je":', options=['sois', 'suis', 'étais', 'serais'], answer=0, explanation='Que je sois.'),
    TestQuestion(id='tcf-ls-6', level='B1', prompt='"Si j\'avais le temps, je _____ voyager."', options=['vais', 'irais', 'allais', 'irai'], answer=1, explanation='Si + imparfait → conditionnel.'),
    TestQuestion(id='tcf-ls-7', level='B2', prompt='Passé simple of "aimer" (il):', options=['aimait', 'aima', 'aimera', 'aimerait'], answer=1, explanation='Il aima.'),
    TestQuestion(id='tcf-ls-8', level='B2', prompt='"Je vous saurais gré de..." means:', options=['I would be grateful if...', 'I don\'t care...', 'I am angry...', 'I thank you...'], answer=0, explanation='Very formal gratitude.'),
    TestQuestion(id='tcf-ls-9', level='A1', prompt='"Mange" is the form for:', options=['je', 'tu', 'il', 'nous'], answer=1, explanation='Tu manges.'),
    TestQuestion(id='tcf-ls-10', level='A2', prompt='Passé composé of "aller" (elle):', options=['elle a allé', 'elle est allée', 'elle allait', 'elle ira'], answer=1, explanation='Aller uses être.'),
]

tcf_test = MockTest(
    type='TCF', name='TCF', fullName='Test de Connaissance du Français',
    description="French Ministry of Education's test. Evaluates A1 to C2.",
    administeredBy='France Éducation International (FEI)',
    usedFor='French nationality (B1), residency (A2), Quebec CSQ, university',
    color='#B91C1C',
    sections=[
        TestSectionData(id='reading', title='Reading Comprehension', titleFr='Compréhension écrite', description='Read texts. Practice: 10 questions.', icon='📖', questionCount=10, durationMinutes=10, questions=tcf_reading_questions),
        TestSectionData(id='listening', title='Listening Comprehension', titleFr='Compréhension orale', description='Listen to audio. Practice: 10 questions.', icon='🎧', questionCount=10, durationMinutes=10, questions=tcf_listening_questions),
        TestSectionData(id='language_structures', title='Language Structures', titleFr='Maîtrise des structures', description='Grammar and vocabulary. Practice: 10 questions.', icon='✏️', questionCount=10, durationMinutes=8, questions=tcf_language_questions),
    ],
)

mock_tests = [tef_test, tcf_test]

def get_test(test_type):
    for t in mock_tests:
        if t.type == test_type.upper():
            return t
    return tef_test

def get_practice_set_questions(test_type, section_id, set_num):
    """Get questions for a specific practice set.
    set_num: 1-based index into the section's sets.
    Returns list of question dicts.
    """
    expanded = TEF_EXPANDED if test_type.upper() == 'TEF' else TCF_EXPANDED
    section = expanded.get(section_id, {})
    sorted_keys = sorted(section.keys())
    if set_num < 1 or set_num > len(sorted_keys):
        return []
    set_key = sorted_keys[set_num - 1]
    return section.get(set_key, [])

def get_section_sets(test_type, section_id):
    """Get available practice sets for a section."""
    expanded = TEF_EXPANDED if test_type.upper() == 'TEF' else TCF_EXPANDED
    section = expanded.get(section_id, {})
    sets = []
    set_num = 1
    for set_key in sorted(section.keys()):
        questions = section[set_key]
        sets.append({
            'setNum': set_num,
            'questionCount': len(questions),
            'isAI': False,
        })
        set_num += 1
    return sets

def get_all_section_sets(test_type):
    """Get all practice sets for all sections of a test."""
    test = get_test(test_type)
    result = {}
    for section in test.sections:
        result[section.id] = {
            'title': section.title,
            'titleFr': section.titleFr,
            'icon': section.icon,
            'durationMinutes': section.durationMinutes,
            'sets': get_section_sets(test_type, section.id),
        }
    return result
