from .types import *
from .a1_course import a1_course
from .a2_course import a2_course
from .b1_course import b1_course
from .b2_course import b2_course
import json
import os

# ============================================================
# C1 Course — Advanced French
# ============================================================

c1_course = Course(
    level='C1', title='C1 — Avancé supérieur', book='Parlez C1',
    description="Master advanced French. Understand implicit meaning, express yourself fluently, produce clear, well-structured text on complex topics, and use French flexibly for social, academic, and professional purposes.",
    cefrDescription='Can understand a wide range of demanding, longer texts, and recognise implicit meaning. Can express himself fluently and spontaneously without much obvious searching for expressions. Can use language flexibly and effectively for social, academic and professional purposes.',
    color='#4A1942',
    units=[
        Unit(
            id='c1-u1', title='Advanced Argumentation', titleFr='Argumentation avancée',
            theme='Sophisticated argumentation & rhetoric', description='Master complex argumentation, rhetoric, and persuasive techniques.',
            lessons=[
                Lesson(id='c1-u1-l1', title='Rhetoric and Persuasion', titleFr='Rhétorique et persuasion',
                    description='Master rhetorical devices and persuasive techniques in French.',
                    objectives=['Use rhetorical questions effectively', 'Apply anaphora and repetition', 'Construct a persuasive argument', 'Identify logical fallacies in French'],
                    vocabulary=[
                        VocabItem(fr='la rhétorique', en='rhetoric', category='advanced'),
                        VocabItem(fr='l\'anaphore', en='anaphora (repetition)', category='rhetoric'),
                        VocabItem(fr='l\'antithèse', en='antithesis', category='rhetoric'),
                        VocabItem(fr='la gradation', en='gradation (escalation)', category='rhetoric'),
                        VocabItem(fr='l\'ironie', en='irony', category='rhetoric'),
                        VocabItem(fr='la litote', en='understatement (litote)', category='rhetoric'),
                        VocabItem(fr='la métaphore', en='metaphor', category='rhetoric'),
                        VocabItem(fr='le syllogisme', en='syllogism', category='logic'),
                        VocabItem(fr='le sophisme', en='fallacy', category='logic'),
                        VocabItem(fr='convaincre', en='to convince', category='verbs'),
                        VocabItem(fr='persuader', en='to persuade', category='verbs'),
                        VocabItem(fr='discourir', en='to discourse/argue', category='verbs'),
                    ],
                    grammar=[
                        GrammarRule(title='Advanced argumentation structures', explanation='Use complex argumentation with concession, refutation, and synthesis.', examples=[
                            GrammarExample(fr='Non seulement..., mais en plus...', en='Not only..., but also...'),
                            GrammarExample(fr='Quoi qu\'on en dise, il reste que...', en='Whatever one may say, it remains that...'),
                            GrammarExample(fr='Il n\'en demeure pas moins que...', en='It nonetheless remains that...'),
                        ]),
                    ],
                    dialogue=[
                        DialogueLine(speaker='A', name='Modérateur', fr='Quel est votre avis sur cette réforme ?', en='What is your opinion on this reform?'),
                        DialogueLine(speaker='B', name='Député', fr='À mon avis, cette réforme est nécessaire. Non seulement elle permettra de réduire le déficit, mais en plus elle encouragera l\'investissement. Certes, elle sera douloureuse à court terme, mais il n\'en demeure pas moins qu\'elle est indispensable pour l\'avenir de notre pays.', en='In my opinion, this reform is necessary. Not only will it reduce the deficit, but it will also encourage investment. Admittedly, it will be painful in the short term, but it nonetheless remains indispensable for the future of our country.'),
                    ],
                    exercises=[
                        Exercise(id='c1-u1-l1-e1', type='multiple_choice', prompt='What rhetorical device involves repeating the same word or phrase at the beginning of successive clauses?', options=['Antithesis', 'Anaphora', 'Litote', 'Metaphor'], answer=1),
                        Exercise(id='c1-u1-l1-e2', type='multiple_choice', prompt='What does "Il n\'en demeure pas moins que" express?', options=['Addition', 'Concession', 'Opposition', 'Conclusion'], answer=1),
                        Exercise(id='c1-u1-l1-e3', type='translate_to_fr', prompt='Translate: "Not only is he intelligent, but he is also hardworking."', answer='Non seulement il est intelligent, mais en plus il est travailleur', acceptable=['non seulement il est intelligent mais en plus il est travailleur']),
                    ],
                    estimatedMinutes=45),
                Lesson(id='c1-u1-l2', title='Nuanced Expression', titleFr='Expression nuancée',
                    description='Express subtle differences, hesitation, and nuance in French.',
                    objectives=['Express probability and uncertainty', 'Use hedging language', 'Distinguish registers in argumentation'],
                    vocabulary=[
                        VocabItem(fr='il est probable que', en='it is probable that', category='nuance'),
                        VocabItem(fr='il se pourrait que', en='it could be that', category='nuance'),
                        VocabItem(fr='il est vraisemblable que', en='it is likely that', category='nuance'),
                        VocabItem(fr='force est de constater que', en='one must note that', category='formal'),
                        VocabItem(fr='il convient de souligner que', en='it is appropriate to note that', category='formal'),
                        VocabItem(fr='en tout état de cause', en='in any case', category='conclusion'),
                        VocabItem(fr='pour autant', en='nevertheless/yet', category='concession'),
                        VocabItem(fr='en l\'occurrence', en='in this instance', category='precision'),
                        VocabItem(fr='à titre d\'exemple', en='for example', category='illustration'),
                        VocabItem(fr='en revanche', en='on the other hand', category='contrast'),
                    ],
                    grammar=[
                        GrammarRule(title='Hedging and probability', explanation='Express uncertainty with conditional and subjunctive.', examples=[
                            GrammarExample(fr='Il pourrait être intéressant de...', en='It could be interesting to...'),
                            GrammarExample(fr='Il semble qu\'il ait raison.', en='It seems that he is right. (subjunctive)'),
                            GrammarExample(fr='Il est possible qu\'ils viennent.', en='It is possible that they come. (subjunctive)'),
                        ]),
                    ],
                    dialogue=[
                        DialogueLine(speaker='A', name='Journaliste', fr='Pensez-vous que la réforme sera acceptée ?', en='Do you think the reform will be accepted?'),
                        DialogueLine(speaker='B', name='Expert', fr='Force est de constater que les opinions sont divisées. Il est probable que le gouvernement devra faire des compromis. En tout état de cause, il convient de noter que le processus législatif est long.', en='One must note that opinions are divided. It is likely that the government will have to make compromises. In any case, it should be noted that the legislative process is long.'),
                    ],
                    exercises=[
                        Exercise(id='c1-u1-l2-e1', type='multiple_choice', prompt='Which expression means "in any case"?', options=['En l\'occurrence', 'En tout état de cause', 'À titre d\'exemple', 'En revanche'], answer=1),
                        Exercise(id='c1-u1-l2-e2', type='fill_blank', prompt='Complete: "Il est _____ qu\'il vienne." (probable)', answer='probable', acceptable=['probable', 'vraisemblable']),
                    ],
                    estimatedMinutes=40),
            ]),
        Unit(
            id='c1-u2', title='Literary and journalistic French', titleFr='Français littéraire et journalistique',
            theme='Reading complex texts & media analysis', description='Understand and produce literary and journalistic French.',
            lessons=[
                Lesson(id='c1-u2-l1', title='Journalistic Style', titleFr='Le style journalistique',
                    description='Read and understand French newspaper articles, editorials, and reports.',
                    objectives=['Identify journalistic registers', 'Understand headline structures', 'Analyze editorial argumentation', 'Summarize articles in French'],
                    vocabulary=[
                        VocabItem(fr='l\'éditorial', en='editorial', category='journalism'),
                        VocabItem(fr='le reportage', en='reportage', category='journalism'),
                        VocabItem(fr='la une', en='front page', category='journalism'),
                        VocabItem(fr='le journaliste', en='journalist', category='journalism'),
                        VocabItem(fr='la source', en='source', category='journalism'),
                        VocabItem(fr='le journaliste d\'investigation', en='investigative journalist', category='journalism'),
                        VocabItem(fr='relater', en='to report', category='verbs'),
                        VocabItem(fr='dénoncer', en='to denounce', category='verbs'),
                        VocabItem(fr='analyser', en='to analyze', category='verbs'),
                        VocabItem(fr='synthétiser', en='to synthesize', category='verbs'),
                    ],
                    grammar=[
                        GrammarRule(title='Journalistic present tense', explanation='Journalists use the present tense for historical facts and the conditional for unconfirmed reports.', examples=[
                            GrammarExample(fr='Le président announce une réforme. (present = historical)', en='The president announces a reform.'),
                            GrammarExample(fr='Le gouvernement annoncerait une réforme. (conditional = unconfirmed)', en='The government would announce a reform.'),
                        ]),
                    ],
                    dialogue=[
                        DialogueLine(speaker='A', name='Rédacteur', fr='Qu\'est-ce que les sources disent ?', en='What do the sources say?'),
                        DialogueLine(speaker='B', name='Journaliste', fr='Selon nos informations, le gouvernement annoncerait une réforme la semaine prochaine. Cependant, les syndicats dénoncent déjà cette mesure.', en='According to our information, the government would announce a reform next week. However, unions already denounce this measure.'),
                    ],
                    exercises=[
                        Exercise(id='c1-u2-l1-e1', type='multiple_choice', prompt='Why do journalists use the conditional?', options=['To express politeness', 'To report unconfirmed information', 'To describe the future', 'To give orders'], answer=1),
                        Exercise(id='c1-u2-l1-e2', type='translate_to_en', prompt='Translate: "Selon nos informations, le projet serait annulé."', answer='According to our information, the project would be canceled'),
                    ],
                    estimatedMinutes=45),
            ]),
        Unit(
            id='c1-u3', title='Academic and professional French', titleFr='Français académique et professionnel',
            theme='Writing & professional communication', description='Write formal emails, reports, and academic texts.',
            lessons=[
                Lesson(id='c1-u3-l1', title='Formal Writing', titleFr='L\'écriture formelle',
                    description='Write formal emails, reports, and academic texts in French.',
                    objectives=['Write professional emails', 'Structure an academic essay', 'Use formal connectors', 'Produce well-organized texts'],
                    vocabulary=[
                        VocabItem(fr='Madame, Monsieur,', en='Dear Sir/Madam, (formal salutation)', category='writing'),
                        VocabItem(fr='Je vous prie d\'agréer...', en='Please accept... (formal closing)', category='writing'),
                        VocabItem(fr='je vous serais reconnaissant(e) de', en='I would be grateful if you could', category='writing'),
                        VocabItem(fr='en réponse à votre courrier', en='in response to your letter', category='writing'),
                        VocabItem(fr='je me permets de vous écrire', en='I take the liberty of writing to you', category='writing'),
                        VocabItem(fr='dans le cadre de', en='in the context of', category='writing'),
                        VocabItem(fr='en ce qui concerne', en='concerning', category='writing'),
                        VocabItem(fr='il convient de noter que', en='it should be noted that', category='writing'),
                        VocabItem(fr='je vous envoie ci-joint', en='I am sending you attached', category='writing'),
                        VocabItem(fr='je reste à votre disposition', en='I remain at your disposal', category='writing'),
                    ],
                    grammar=[
                        GrammarRule(title='Formal email structure', explanation='Formal French emails follow a specific structure: greeting, context, request, closing.', examples=[
                            GrammarExample(fr='Madame, Monsieur,', en='Dear Sir/Madam, (opening)'),
                            GrammarExample(fr='Je vous prie d\'agréer, Madame, l\'expression de mes salutations distinguées.', en='Yours sincerely, (formal closing)'),
                        ]),
                    ],
                    dialogue=[
                        DialogueLine(speaker='A', name='Assistant', fr='Voici le brouillet de l\'email pour le client.', en='Here is the draft email for the client.'),
                        DialogueLine(speaker='B', name='Directeur', fr='Très bien. Commencez par "Madame, Monsieur" et terminez par "Je vous prie d\'agréer...". Utilisez un ton formel mais courtois.', en='Very well. Start with "Dear Sir/Madam" and end with "Please accept...". Use a formal but courteous tone.'),
                    ],
                    exercises=[
                        Exercise(id='c1-u3-l1-e1', type='multiple_choice', prompt='What is the correct formal closing for a French email?', options=['Cordialement', 'Je vous prie d\'agréer, Madame, l\'expression de mes salutations distinguées.', 'Salut', 'Bisous'], answer=1),
                        Exercise(id='c1-u3-l1-e2', type='fill_blank', prompt='Complete: "_____ vous prie d\'agréer..."', answer='Je', acceptable=['je']),
                    ],
                    estimatedMinutes=45),
            ]),
        Unit(
            id='c1-u4', title='Cultural mastery', titleFr='Maîtrise culturelle',
            theme='French culture, history & society', description='Understand French culture, history, and society at a deep level.',
            lessons=[
                Lesson(id='c1-u4-l1', title='French History and Society', titleFr='Histoire et société françaises',
                    description='Discuss French history, politics, and social issues in depth.',
                    objectives=['Discuss French historical events', 'Analyze social issues', 'Express nuanced opinions on current affairs', 'Use historical vocabulary'],
                    vocabulary=[
                        VocabItem(fr='la Révolution', en='the Revolution', category='history'),
                        VocabItem(fr='les Lumières', en='the Enlightenment', category='history'),
                        VocabItem(fr='la Résistance', en='the Resistance (WWII)', category='history'),
                        VocabItem(fr='la laïcité', en='secularism', category='society'),
                        VocabItem(fr='le multiculturalisme', en='multiculturalism', category='society'),
                        VocabItem(fr='l\'intégration', en='integration', category='society'),
                        VocabItem(fr='le débat public', en='public debate', category='society'),
                        VocabItem(fr='la tradition', en='tradition', category='culture'),
                        VocabItem(fr='le patrimoine', en='heritage', category='culture'),
                        VocabItem(fr='l\'identité nationale', en='national identity', category='society'),
                    ],
                    grammar=[
                        GrammarRule(title='Discussing history in French', explanation='Use imparfait for background, passé composé for events, and plus-que-parfait for earlier events.', examples=[
                            GrammarExample(fr='En 1789, le peuple français se révolta.', en='In 1789, the French people revolted.'),
                            GrammarExample(fr='La Révolution avait déjà commencé quand le roi fut arrêté.', en='The Revolution had already started when the king was arrested.'),
                        ]),
                    ],
                    dialogue=[
                        DialogueLine(speaker='A', name='Professeur', fr='Qu\'est-ce que vous savez sur la laïcité en France ?', en='What do you know about secularism in France?'),
                        DialogueLine(speaker='B', name='Étudiant', fr='La laïcité est un principe fondamental de la République française. Elle garantit la liberté de conscience et sépare l\'Église de l\'État. Cependant, elle est souvent débattue, notamment en ce qui concerne le port de signes religieux dans les écoles publiques.', en='Secularism is a fundamental principle of the French Republic. It guarantees freedom of conscience and separates church and state. However, it is often debated, particularly regarding the wearing of religious signs in public schools.'),
                    ],
                    exercises=[
                        Exercise(id='c1-u4-l1-e1', type='multiple_choice', prompt='What year did the French Revolution begin?', options=['1776', '1789', '1804', '1815'], answer=1),
                        Exercise(id='c1-u4-l1-e2', type='translate_to_fr', prompt='Translate: "Secularism is a fundamental principle."', answer='La laïcité est un principe fondamental', acceptable=['la laïcité est un principe fondamental']),
                    ],
                    estimatedMinutes=50),
            ]),
        Unit(
            id='c1-u5', title='Spoken fluency', titleFr='Fluidité à l\'oral',
            theme='Speaking fluently and naturally', description='Develop oral fluency, handle spontaneous conversations, and express complex ideas spontaneously.',
            lessons=[
                Lesson(id='c1-u5-l1', title='Spontaneous Discussion', titleFr='Discussion spontanée',
                    description='Handle spontaneous, unprepared discussions on complex topics.',
                    objectives=['Express opinions spontaneously', 'Handle interruptions gracefully', 'Use fillers and discourse markers naturally', 'Maintain a conversation on abstract topics'],
                    vocabulary=[
                        VocabItem(fr='pour ainsi dire', en='so to speak', category='fillers'),
                        VocabItem(fr='en d\'autres termes', en='in other words', category='fillers'),
                        VocabItem(fr='il va sans dire que', en='it goes without saying that', category='fillers'),
                        VocabItem(fr='je dirais même que', en='I would even say that', category='fillers'),
                        VocabItem(fr='pour être tout à fait honnête', en='to be completely honest', category='fillers'),
                        VocabItem(fr='c\'est exactement ce que je pensais', en='that\'s exactly what I was thinking', category='agreement'),
                        VocabItem(fr='je ne suis pas tout à fait d\'accord', en='I don\'t entirely agree', category='disagreement'),
                        VocabItem(fr='tu as un point', en='you have a point', category='concession'),
                        VocabItem(fr='mais tu ne crois pas que', en='but don\'t you think that', category='questioning'),
                        VocabItem(fr='comment tu expliquerais ça ?', en='how would you explain that?', category='questioning'),
                    ],
                    grammar=[
                        GrammarRule(title='Spoken French discourse markers', explanation='Native speakers use discourse markers to manage conversation flow.', examples=[
                            GrammarExample(fr='Bon, alors... (starting a topic)', en='Well, so...'),
                            GrammarExample(fr='Tu vois ce que je veux dire ? (checking understanding)', en='You see what I mean?'),
                            GrammarExample(fr='C\'est pas faux. (understatement for "c\'est vrai")', en='It\'s not wrong. (= It\'s true)'),
                        ]),
                    ],
                    dialogue=[
                        DialogueLine(speaker='A', name='Ami', fr='Tu crois que le télétravail va devenir la norme ?', en='Do you think remote work will become the norm?'),
                        DialogueLine(speaker='B', name='Ami', fr='Bon, c\'est une bonne question. Pour être tout à fait honnête, je dirais que ça dépend du secteur. Tu vois, dans certains métiers, le présentiel reste indispensable pour la créativité. Mais pour d\'autres, c\'est pas faux de dire que le télétravail a ses avantages.', en='Well, that\'s a good question. To be completely honest, I would say it depends on the sector. You see, in some jobs, in-person remains essential for creativity. But for others, it\'s not wrong to say remote work has its advantages.'),
                    ],
                    exercises=[
                        Exercise(id='c1-u5-l1-e1', type='multiple_choice', prompt='What does "c\'est pas faux" mean?', options=['It\'s wrong', 'It\'s not wrong (= it\'s true)', 'I don\'t know', 'Maybe'], answer=1),
                        Exercise(id='c1-u5-l1-e2', type='fill_blank', prompt='Complete: "_____ ce que je veux dire ?" (Do you see what I mean?)', answer='Tu vois', acceptable=['tu vois', 'Tu vois']),
                    ],
                    estimatedMinutes=40),
            ]),
        ],
)

# ============================================================
# Conversation scenarios
# ============================================================

conversation_scenarios = [
    ScenarioTopic(id='cafe', label='At the Café', labelFr='Au café', description='Order a coffee and a pastry', icon='☕'),
    ScenarioTopic(id='restaurant', label='At the Restaurant', labelFr='Au restaurant', description='Order a meal and chat with the waiter', icon='🍽️'),
    ScenarioTopic(id='market', label='At the Market', labelFr='Au marché', description='Buy fruits and vegetables', icon='🍎'),
    ScenarioTopic(id='train', label='Train Station', labelFr='À la gare', description='Buy a ticket and find your platform', icon='🚆'),
    ScenarioTopic(id='hotel', label='At the Hotel', labelFr="À l'hôtel", description='Check in and ask about services', icon='🏨'),
    ScenarioTopic(id='doctor', label='At the Doctor', labelFr='Chez le médecin', description='Describe symptoms and get advice', icon='⚕️'),
    ScenarioTopic(id='interview', label='Job Interview', labelFr="Entretien d'embauche", description='Practice a professional interview', icon='💼'),
    ScenarioTopic(id='friends', label='Meeting Friends', labelFr='Entre amis', description='Casual conversation with friends', icon='👋'),
    ScenarioTopic(id='shopping', label='Shopping', labelFr='Au magasin', description='Buy clothes and ask for sizes', icon='🛍️'),
    ScenarioTopic(id='directions', label='Asking Directions', labelFr='Demander son chemin', description='Ask for and give directions', icon='🗺️'),
    ScenarioTopic(id='travel', label='Travel & Tourism', labelFr='Voyage et tourisme', description='Plan a trip and visit sights', icon='✈️'),
    ScenarioTopic(id='family', label='Family & Life', labelFr='Famille et vie', description='Talk about your family and life', icon='👨‍👩‍👧'),
]

# ============================================================
# Course registry
# ============================================================

courses = [a1_course, a2_course, b1_course, b2_course, c1_course]

course_levels = [
    {'level': 'A1', 'color': '#2D6A4F', 'book': 'Parlez A1', 'title': 'Débutant', 'description': 'Complete beginner — greetings, basics, daily life'},
    {'level': 'A2', 'color': '#C19A4B', 'book': 'Parlez A2', 'title': 'Élémentaire', 'description': 'Elementary — past tenses, opinions, social life'},
    {'level': 'B1', 'color': '#B45309', 'book': 'Parlez B1', 'title': 'Intermédiaire', 'description': 'Intermediate — arguments, subjunctive, media'},
    {'level': 'B2', 'color': '#7C2D3F', 'book': 'Parlez B2', 'title': 'Avancé', 'description': 'Upper-intermediate — debate, nuance, literature'},
    {'level': 'C1', 'color': '#4A1942', 'book': 'Parlez C1', 'title': 'Avancé supérieur', 'description': 'Advanced — rhetoric, journalism, academic writing'},
]

def get_course(level):
    for c in courses:
        if c.level == level:
            return c
    return courses[0]

def get_course_summary(level):
    c = get_course(level)
    return {
        'level': c.level, 'title': c.title, 'book': c.book,
        'description': c.description, 'cefrDescription': c.cefrDescription,
        'color': c.color, 'unitCount': len(c.units),
        'lessonCount': sum(len(u.lessons) for u in c.units),
        'units': [{'id': u.id, 'title': u.title, 'titleFr': u.titleFr, 'theme': u.theme,
                    'lessons': [{'id': l.id, 'title': l.title, 'titleFr': l.titleFr, 'minutes': l.estimatedMinutes} for l in u.lessons]}
                   for u in c.units],
    }
