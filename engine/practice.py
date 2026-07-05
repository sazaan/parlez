"""
Vocabulary and Conjugation practice engine.
Generates drills, quizzes, and practice sessions from course data.
"""
import random
from .exercises import normalize_answer


def generate_vocab_quiz(vocabulary, n=5):
    """Generate a multiple-choice vocabulary quiz from a vocab list."""
    if not vocabulary or len(vocabulary) < 2:
        return None
    
    questions = []
    sample = random.sample(vocabulary, min(n, len(vocabulary)))
    
    for word in sample:
        # Randomly choose direction: French→English or English→French
        fr_to_en = random.choice([True, False])
        
        if fr_to_en:
            question = f'What does "{word["fr"]}" mean in English?'
            correct = word['en']
            # Generate wrong options from other words
            others = [w['en'] for w in vocabulary if w['en'] != word['en']]
            wrong = random.sample(others, min(3, len(others)))
            options = [correct] + wrong
        else:
            question = f'How do you say "{word["en"]}" in French?'
            correct = word['fr']
            others = [w['fr'] for w in vocabulary if w['fr'] != word['fr']]
            wrong = random.sample(others, min(3, len(others)))
            options = [correct] + wrong
        
        random.shuffle(options)
        correct_idx = options.index(correct)
        
        q = {
            'question': question,
            'options': options,
            'correct': correct_idx,
        }
        if word.get('ipa'):
            q['hint'] = f'IPA: {word["ipa"]}'
        if word.get('example'):
            q['explanation'] = f'{word["example"]} — {word.get("exampleEn", "")}'
        
        questions.append(q)
    
    return {
        'title': f'Vocabulary Quiz ({len(questions)} words)',
        'questions': questions,
    }


def generate_conj_quiz(conjugation_data, n=5):
    """Generate a conjugation quiz from conjugation data."""
    if not conjugation_data or not conjugation_data.get('verbs'):
        return None
    
    questions = []
    
    for verb in conjugation_data['verbs']:
        for conj in verb.get('conjugations', []):
            pronoun = conj['pronoun']
            form = conj['form']
            
            # Generate wrong options
            all_forms = [c['form'] for v in conjugation_data['verbs'] for c in v.get('conjugations', [])]
            wrong_forms = [f for f in all_forms if f != form]
            wrong = random.sample(wrong_forms, min(3, len(wrong_forms))) if wrong_forms else ['(none)']
            
            options = [form] + wrong
            random.shuffle(options)
            correct_idx = options.index(form)
            
            questions.append({
                'question': f'What is the {verb["tense"]} form of "{verb["infinitive"]}" for "{pronoun}"?',
                'options': options,
                'correct': correct_idx,
                'explanation': f'{pronoun} {form} ({verb["infinitive"]} — {verb["translation"]})',
            })
    
    random.shuffle(questions)
    return {
        'title': f'Conjugation Quiz ({len(questions)} questions)',
        'questions': questions[:n],
    }


def generate_fill_blank_vocab(vocabulary, n=5):
    """Generate fill-in-the-blank vocabulary exercises."""
    if not vocabulary:
        return None
    
    exercises = []
    sample = random.sample(vocabulary, min(n, len(vocabulary)))
    
    for word in sample:
        exercises.append({
            'type': 'fill_blank',
            'prompt': f'What is the French word for "{word["en"]}"?',
            'answer': word['fr'],
            'acceptable': [word['fr'].lower(), normalize_answer(word['fr'])],
            'explanation': f'{word["fr"]} = {word["en"]}',
        })
    
    return exercises


def generate_matching_pairs(vocabulary, n=5):
    """Generate a matching exercise from vocabulary."""
    if not vocabulary:
        return None
    
    sample = random.sample(vocabulary, min(n, len(vocabulary)))
    pairs = [{'left': w['fr'], 'right': w['en']} for w in sample]
    
    return {
        'type': 'matching',
        'prompt': 'Match each French word to its English meaning:',
        'pairs': pairs,
    }


def get_word_of_day(vocabulary_pool):
    """Pick a word of the day based on the day of the year."""
    import datetime
    day = datetime.date.today().timetuple().tm_yday
    if vocabulary_pool:
        idx = day % len(vocabulary_pool)
        return vocabulary_pool[idx]
    return None


def categorize_vocabulary(vocabulary):
    """Group vocabulary by category."""
    categories = {}
    for word in vocabulary:
        cat = word.get('category', 'general')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(word)
    return categories
