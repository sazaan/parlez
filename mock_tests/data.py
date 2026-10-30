from dataclasses import asdict

from .types import *
from .expanded_data import TEF_EXPANDED, TCF_EXPANDED
from .task_variations import (
    SPEAKING_RUBRIC,
    TEF_TASK_VARIATIONS,
    TCF_TASK_VARIATIONS,
    WRITING_RUBRIC,
)

FULL_LENGTH_SET_NUM = 4
PRACTICE_SETS_COUNT = FULL_LENGTH_SET_NUM  # Sets 1–3 are drills; set 4 is one full-length rehearsal.

TEF_CANADA_FORMAT_NOTE = "TEF Canada format reference; Parlez practice items are original and unofficial. Verify current details with the provider."
TCF_CANADA_FORMAT_NOTE = "TCF Canada format reference; Parlez practice items are original and unofficial. Verify current details with the provider."

tef_format = ExamFormat(
    type='TEF', name='TEF Canada', fullName="Test d'évaluation de français (TEF) — Canada",
    color='#1D4ED8',
    description=TEF_CANADA_FORMAT_NOTE,
    administeredBy='Le français des affaires, CCI Paris Île-de-France',
    usedFor='Canada-specific French-test practice; check current IRCC rules and accepted-test requirements.',
    sections=[
        ExamSection(id='reading', title='Reading Comprehension', titleFr='Compréhension écrite', description='40 questions · 60 minutes', icon='📖', questionCount=40, durationMinutes=60),
        ExamSection(id='listening', title='Listening Comprehension', titleFr='Compréhension orale', description='40 questions · 40 minutes', icon='🎧', questionCount=40, durationMinutes=40),
        ExamSection(id='writing', title='Writing', titleFr='Expression écrite', description='2 tasks · 60 minutes · 25 and 35 minutes', icon='✍️', questionCount=2, durationMinutes=60),
        ExamSection(id='speaking', title='Speaking', titleFr='Expression orale', description='2 tasks · 15 minutes · 5 and 10 minutes', icon='🗣️', questionCount=2, durationMinutes=15),
    ],
    formatSourceUrl='https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/examination/',
    practiceNotice='Original, unofficial practice. This is not an official test or a score prediction.',
)

tcf_format = ExamFormat(
    type='TCF', name='TCF Canada', fullName='Test de connaissance du français — Canada',
    color='#B91C1C',
    description=TCF_CANADA_FORMAT_NOTE,
    administeredBy='France Éducation international (FEI)',
    usedFor='Canada-specific French-test practice; check current IRCC rules and accepted-test requirements.',
    sections=[
        ExamSection(id='listening', title='Listening Comprehension', titleFr='Compréhension orale', description='39 questions · 35 minutes', icon='🎧', questionCount=39, durationMinutes=35),
        ExamSection(id='reading', title='Reading Comprehension', titleFr='Compréhension écrite', description='39 questions · 60 minutes', icon='📖', questionCount=39, durationMinutes=60),
        ExamSection(id='writing', title='Writing', titleFr='Expression écrite', description='3 tasks · 60 minutes · 60–120, 120–150 and 120–180 words', icon='✍️', questionCount=3, durationMinutes=60),
        ExamSection(id='speaking', title='Speaking', titleFr='Expression orale', description='3 tasks · 12 minutes · interview, interaction and opinion', icon='🗣️', questionCount=3, durationMinutes=12),
    ],
    formatSourceUrl='https://www.france-education-international.fr/en/test/tcf-canada',
    practiceNotice='Original, unofficial practice. This is not an official test or a score prediction.',
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

tef_test = MockTest(
    type='TEF', name='TEF Canada', fullName="Test d'évaluation de français (TEF) — Canada",
    description=TEF_CANADA_FORMAT_NOTE,
    administeredBy='Le français des affaires, CCI Paris Île-de-France',
    usedFor='Canada-specific French-test practice; check current IRCC rules and accepted-test requirements.',
    color='#1D4ED8',
    formatSourceUrl='https://www.lefrancaisdesaffaires.fr/en/candidate/test-evaluation-francais/tef-canada/examination/',
    sections=[
        TestSectionData(id='reading', title='Reading Comprehension', titleFr='Compréhension écrite', description='Official format: 40 questions in 60 minutes. Parlez practice sets are shorter.', icon='📖', questionCount=10, durationMinutes=60, questions=tef_reading_questions, officialQuestionCount=40),
        TestSectionData(id='listening', title='Listening Comprehension', titleFr='Compréhension orale', description='Official format: 40 questions in 40 minutes. Parlez practice sets are shorter.', icon='🎧', questionCount=10, durationMinutes=40, questions=tef_listening_questions, officialQuestionCount=40),
        TestSectionData(
            id='writing', title='Writing', titleFr='Expression écrite',
            description='Official format: 2 tasks in 60 minutes. These original prompts are for practice, not official test items.',
            icon='✍️', questionCount=0, durationMinutes=60, officialTaskCount=2,
            tasks=[
                ExamTask(
                    id='tef-writing-task-1', title='Task 1 · Continue a short news item',
                    prompt='A local news site begins a story: « Un objet mystérieux a été découvert hier dans un autobus de la ville… » Continue the report. Explain what was found, who was involved, and what happened next.',
                    instructions='Write at least 80 words. Keep the events clear and connected.', responseMode='written', durationMinutes=25, wordMin=80,
                    selfCheck=['I wrote at least 80 words.', 'My report follows the opening and explains what happened.', 'I checked verb tense, agreement, and punctuation.'],
                ),
                ExamTask(
                    id='tef-writing-task-2', title='Task 2 · Give and support an opinion',
                    prompt='A city is considering making its central streets pedestrian-only on weekends. Do you support the idea? Write a short opinion piece for a local newsletter.',
                    instructions='Write at least 200 words. State your position, support it with reasons and examples, and address a possible counterargument.', responseMode='written', durationMinutes=35, wordMin=200,
                    selfCheck=['I wrote at least 200 words.', 'My position is clear and supported with relevant reasons.', 'My paragraphs and linking words make the argument easy to follow.'],
                ),
            ],
        ),
        TestSectionData(
            id='speaking', title='Speaking', titleFr='Expression orale',
            description='Official format: 2 tasks in 15 minutes (5 and 10 minutes). Practise aloud; Parlez does not score speaking proficiency.',
            icon='🗣️', questionCount=0, durationMinutes=15, officialTaskCount=2,
            tasks=[
                ExamTask(
                    id='tef-speaking-task-1', title='Task 1 · Ask for information',
                    prompt='You see an announcement for a community garden that welcomes new members. Call the coordinator and ask about the schedule, costs, tools, and how to join.',
                    instructions='Practise a natural phone conversation. Ask follow-up questions and note the information you need.', responseMode='spoken', durationMinutes=5,
                    selfCheck=['I opened the conversation politely and explained why I was calling.', 'I asked clear questions about practical details.', 'I used follow-up questions when information was incomplete.'],
                ),
                ExamTask(
                    id='tef-speaking-task-2', title='Task 2 · Persuade and respond',
                    prompt='A friend is unsure about joining a neighbourhood repair café. Encourage them to come with you, explain the benefits, and respond to their concerns.',
                    instructions='Speak continuously with clear reasons and examples. Practise answering a different objection without losing your main point.', responseMode='spoken', durationMinutes=10,
                    selfCheck=['I stated my suggestion clearly.', 'I gave reasons and a concrete example.', 'I acknowledged a concern and responded respectfully.'],
                ),
            ],
        ),
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

tcf_test = MockTest(
    type='TCF', name='TCF Canada', fullName='Test de connaissance du français — Canada',
    description=TCF_CANADA_FORMAT_NOTE,
    administeredBy='France Éducation international (FEI)',
    usedFor='Canada-specific French-test practice; check current IRCC rules and accepted-test requirements.',
    color='#B91C1C',
    formatSourceUrl='https://www.france-education-international.fr/en/test/tcf-canada',
    sections=[
        TestSectionData(id='listening', title='Listening Comprehension', titleFr='Compréhension orale', description='Official format: 39 questions in 35 minutes. Parlez practice sets are shorter.', icon='🎧', questionCount=10, durationMinutes=35, questions=tcf_listening_questions, officialQuestionCount=39),
        TestSectionData(id='reading', title='Reading Comprehension', titleFr='Compréhension écrite', description='Official format: 39 questions in 60 minutes. Parlez practice sets are shorter.', icon='📖', questionCount=10, durationMinutes=60, questions=tcf_reading_questions, officialQuestionCount=39),
        TestSectionData(
            id='writing', title='Writing', titleFr='Expression écrite',
            description='Official format: 3 tasks in 60 minutes. These original prompts are for practice, not official test items.',
            icon='✍️', questionCount=0, durationMinutes=60, officialTaskCount=3,
            tasks=[
                ExamTask(
                    id='tcf-writing-task-1', title='Task 1 · Write a short message',
                    prompt='You spent a weekend in a nearby town. Write a message to a friend describing where you went, what you did, and what you enjoyed most.',
                    instructions='Write 60–120 words. Include enough detail for your friend to picture the weekend.', responseMode='written', durationMinutes=None, wordMin=60, wordMax=120,
                    selfCheck=['I wrote between 60 and 120 words.', 'I included the place, activities, and a personal reaction.', 'I checked past-tense forms and basic agreement.'],
                ),
                ExamTask(
                    id='tcf-writing-task-2', title='Task 2 · Describe an experience',
                    prompt='For a community newsletter, describe a local event you attended recently. Explain what happened and give your opinion of the event.',
                    instructions='Write 120–150 words. Organise the description and your opinion so they are easy to distinguish.', responseMode='written', durationMinutes=None, wordMin=120, wordMax=150,
                    selfCheck=['I wrote between 120 and 150 words.', 'My description includes concrete details.', 'I explained my opinion with at least one reason.'],
                ),
                ExamTask(
                    id='tcf-writing-task-3', title='Task 3 · Compare viewpoints and give your opinion',
                    prompt='Two residents disagree about adding a new bus route: one values faster access to jobs and services; the other is concerned about noise and traffic. Explain both viewpoints, then state and support your own position.',
                    instructions='Write 120–180 words. Present both viewpoints fairly before developing your own.', responseMode='written', durationMinutes=None, wordMin=120, wordMax=180,
                    selfCheck=['I wrote between 120 and 180 words.', 'I represented both viewpoints fairly.', 'I stated and supported my own position.'],
                ),
            ],
        ),
        TestSectionData(
            id='speaking', title='Speaking', titleFr='Expression orale',
            description='Official format: 3 tasks in 12 minutes. The interaction task includes preparation time; practise aloud without treating this as a proficiency score.',
            icon='🗣️', questionCount=0, durationMinutes=12, officialTaskCount=3,
            tasks=[
                ExamTask(
                    id='tcf-speaking-task-1', title='Task 1 · Guided interview',
                    prompt='Introduce yourself to a new colleague. Talk about your background, current activities, interests, and one plan for the coming year.',
                    instructions='Speak for about 2 minutes. Use connected sentences and add a detail when you can.', responseMode='spoken', durationMinutes=2,
                    selfCheck=['I introduced myself and gave relevant details.', 'I connected ideas rather than listing isolated words.', 'I spoke clearly enough to be understood.'],
                ),
                ExamTask(
                    id='tcf-speaking-task-2', title='Task 2 · Obtain information',
                    prompt='You are considering volunteering at a neighbourhood food-sharing project. Ask the coordinator about duties, schedule, training, and what volunteers should bring.',
                    instructions='Complete the information-seeking interaction within about 5.5 minutes total, including up to 2 minutes of preparation. Ask follow-up questions.', responseMode='spoken', durationMinutes=5.5, prepMinutes=2,
                    selfCheck=['I asked relevant questions in a logical order.', 'I used polite forms and follow-up questions.', 'I checked or clarified key details.'],
                ),
                ExamTask(
                    id='tcf-speaking-task-3', title='Task 3 · Express and develop an opinion',
                    prompt='Some people prefer to work from home, while others prefer a shared workplace. Which arrangement do you prefer, and why?',
                    instructions='Speak for about 4.5 minutes. Give reasons and examples, and acknowledge one reasonable alternative view.', responseMode='spoken', durationMinutes=4.5,
                    selfCheck=['I stated my position early.', 'I supported it with reasons and examples.', 'I acknowledged another perspective and concluded clearly.'],
                ),
            ],
        ),
    ],
)

mock_tests = [tef_test, tcf_test]

def get_test(test_type):
    for t in mock_tests:
        if t.type == test_type.upper():
            return t
    return tef_test


def _attach_task_variations():
    for test_type, variations in (("TEF", TEF_TASK_VARIATIONS), ("TCF", TCF_TASK_VARIATIONS)):
        test = get_test(test_type)
        for section in test.sections:
            rubric = WRITING_RUBRIC if section.id == "writing" else SPEAKING_RUBRIC
            for task in section.tasks:
                task.taskFamily = f"{section.id}-{task.id.rsplit('-', 1)[-1]}"
                task.variantNumber = 1
                task.rubric = rubric[:]
            section.tasks.extend(variations.get(section.id, []))


_attach_task_variations()


def _build_full_length_practice_sets():
    """Create one exact-length, no-duplicate rehearsal from the original item bank.

    The simulation deliberately reuses some questions from the shorter skill
    drills. It rehearses pacing and attention; it is not a fresh official mock.
    """
    level_order = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}
    for test_type, bank in (("TEF", TEF_EXPANDED), ("TCF", TCF_EXPANDED)):
        test = next(item for item in mock_tests if item.type == test_type)
        for section_id in ("reading", "listening"):
            section = next(item for item in test.sections if item.id == section_id)
            section_bank = bank.get(section_id, {})
            source = [question for key in sorted(section_bank) for question in section_bank[key]]
            target_count = section.officialQuestionCount or 0
            if len(source) < target_count:
                continue
            # Keep the practice path gradually more challenging without claiming
            # that these author-assigned labels are calibrated exam levels.
            ordered = [
                question for _, question in sorted(
                    enumerate(source),
                    key=lambda item: (level_order.get(item[1].get("level", "A1"), 0), item[0]),
                )
            ]
            section_bank["set4"] = ordered[:target_count]


_build_full_length_practice_sets()


def get_short_practice_question_count(test_type, section_id):
    """Count distinct questions across short drills, excluding the rehearsal reuse."""
    expanded = TEF_EXPANDED if test_type.upper() == 'TEF' else TCF_EXPANDED
    section = expanded.get(section_id, {})
    return sum(len(questions) for key, questions in section.items() if key != "set4")


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
    """Return drills plus an exact-count objective-skill rehearsal."""
    normalized_type = test_type.upper()
    expanded = TEF_EXPANDED if normalized_type == 'TEF' else TCF_EXPANDED
    section_questions = expanded.get(section_id, {})
    test = get_test(normalized_type)
    section_meta = next((item for item in test.sections if item.id == section_id), None)
    sets = []
    for set_num, set_key in enumerate(sorted(section_questions), start=1):
        questions = section_questions[set_key]
        is_full_length = set_key == "set4"
        official_count = section_meta.officialQuestionCount if section_meta else None
        if is_full_length or not official_count:
            time_limit = section_meta.durationMinutes if section_meta else None
        else:
            time_limit = round(section_meta.durationMinutes * len(questions) / official_count, 1)
        sets.append({
            'setNum': set_num,
            'label': 'Full-length rehearsal' if is_full_length else f'Skill drill {set_num}',
            'questionCount': len(questions),
            'timeLimitMinutes': time_limit,
            'fullLengthSimulation': is_full_length,
            'reusesShortPracticeItems': is_full_length,
            'isAI': False,
        })
    return sets

def get_task(test_type, section_id, task_id):
    """Return an original writing/speaking practice task, if it exists."""
    test = get_test(test_type)
    for section in test.sections:
        if section.id != section_id:
            continue
        for task in section.tasks:
            if task.id == task_id:
                return asdict(task)
    return None


def get_all_section_sets(test_type):
    """Get official section metadata and Parlez practice activities."""
    test = get_test(test_type)
    result = {}
    for section in test.sections:
        result[section.id] = {
            'title': section.title,
            'titleFr': section.titleFr,
            'description': section.description,
            'icon': section.icon,
            'questionCount': section.officialQuestionCount,
            'taskCount': section.officialTaskCount,
            'practiceTaskCount': len(section.tasks),
            'practiceQuestionCount': get_short_practice_question_count(test_type, section.id),
            'durationMinutes': section.durationMinutes,
            'tasks': [asdict(task) for task in section.tasks],
            'sets': get_section_sets(test_type, section.id),
        }
    return result
