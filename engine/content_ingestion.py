"""
French Content Ingestion — processes French text to extract vocabulary,
generate flashcards, and create comprehension quizzes.
"""
import random


def extract_vocabulary_from_text(text, level='A1'):
    """
    Extract vocabulary items from French text.
    Returns a list of vocabulary dicts with fr, en, context.
    """
    # Common French words by level
    level_words = {
        'A1': {
            'bonjour': 'Hello', 'merci': 'Thank you', 'oui': 'Yes', 'non': 'No',
            's\'il vous plaît': 'Please', 'au revoir': 'Goodbye', 'comment': 'how',
            'je': 'I', 'tu': 'you', 'il': 'he', 'elle': 'she', 'nous': 'we',
            'être': 'to be', 'avoir': 'to have', 'faire': 'to do/make',
            'aller': 'to go', 'manger': 'to eat', 'boire': 'to drink',
            'maison': 'house', 'chat': 'cat', 'chien': 'dog', 'livre': 'book',
        },
        'A2': {
            'hier': 'yesterday', 'aujourd\'hui': 'today', 'demain': 'tomorrow',
            'peut-être': 'maybe', 'beaucoup': 'a lot', 'toujours': 'always',
            'jamais': 'never', 'parfois': 'sometimes', 'souvent': 'often',
            'aimer': 'to like', 'croire': 'to believe', 'penser': 'to think',
            'voyager': 'to travel', 'travailler': 'to work', 'étudier': 'to study',
        },
        'B1': {
            'cependant': 'however', 'néanmoins': 'nevertheless', 'en revanche': 'on the other hand',
            'par conséquent': 'consequently', 'il semble que': 'it seems that',
            'je pense que': 'I think that', 'à mon avis': 'in my opinion',
            'bien que': 'although', 'pour que': 'so that', 'avant que': 'before',
        },
        'B2': {
            'd\'une part': 'on one hand', 'd\'autre part': 'on the other hand',
            'non seulement': 'not only', 'toutefois': 'however',
            'quoique': 'although', 'lorsque': 'when', 'puisque': 'since',
            'force est de constater que': 'one must note that',
            'il convient de': 'it is appropriate to',
        },
    }
    
    words = level_words.get(level, level_words['A1'])
    text_lower = text.lower()
    
    found = []
    for fr_word, en_word in sorted(words.items(), key=lambda x: -len(x[0])):
        if fr_word in text_lower:
            # Get context sentence
            sentences = text.split('.')
            context = ''
            for s in sentences:
                if fr_word in s.lower():
                    context = s.strip()
                    break
            
            found.append({
                'fr': fr_word,
                'en': en_word,
                'context': context[:200] if context else '',
                'category': 'from content',
            })
    
    return found[:20]  # Limit to 20 words


def generate_content_flashcards(vocabulary, level='A1'):
    """Generate flashcard data from extracted vocabulary."""
    cards = []
    for v in vocabulary[:15]:  # Limit to 15 cards
        cards.append({
            'front': v['fr'],
            'back': v['en'],
            'card_type': 'vocab',
            'level': level,
            'meta': {
                'context': v.get('context', ''),
                'source': 'content_ingestion',
            }
        })
    return cards


def generate_content_quiz(vocabulary, level='A1', n=5):
    """Generate a comprehension quiz from extracted vocabulary."""
    if len(vocabulary) < 2:
        return None
    
    questions = []
    sample = random.sample(vocabulary, min(n, len(vocabulary)))
    
    for v in sample:
        # Create a fill-in-the-blank question
        context = v.get('context', '')
        if context and v['fr'] in context:
            blanked = context.replace(v['fr'], '_____')
            questions.append({
                'type': 'fill_blank',
                'prompt': f'Fill in the blank: "{blanked}"',
                'answer': v['fr'],
                'acceptable': [v['fr'].lower()],
                'explanation': f'{v["fr"]} = {v["en"]}',
            })
        else:
            # Create a translation question
            questions.append({
                'type': 'translate_to_fr',
                'prompt': f'Translate: "{v["en"]}"',
                'answer': v['fr'],
                'acceptable': [v['fr'].lower()],
                'explanation': f'{v["fr"]} = {v["en"]}',
            })
    
    return {
        'title': f'Content Vocabulary Quiz ({len(questions)} questions)',
        'exercises': questions,
    }


def process_french_content(text, level='A1'):
    """
    Process French text content and extract learning materials.
    Returns vocabulary, flashcards, and quiz data.
    """
    vocabulary = extract_vocabulary_from_text(text, level)
    flashcards = generate_content_flashcards(vocabulary, level)
    quiz = generate_content_quiz(vocabulary, level)
    
    # Summarize the content
    word_count = len(text.split())
    sentence_count = len([s for s in text.split('.') if s.strip()])
    
    return {
        'vocabulary': vocabulary,
        'flashcards': flashcards,
        'quiz': quiz,
        'summary': {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'vocabulary_found': len(vocabulary),
            'flashcards_generated': len(flashcards),
        }
    }
