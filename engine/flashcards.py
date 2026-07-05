"""
SM-2 Spaced Repetition System for flashcards.
Based on the SuperMemo-2 algorithm with modifications.
"""
import time
import math


def sm2_next_interval(quality, repetitions, ease_factor, interval):
    """
    Calculate next review interval using SM-2 algorithm.
    
    quality: 0-5 (0=blackout, 5=perfect)
    repetitions: number of successful reviews in a row
    ease_factor: difficulty factor (>= 1.3)
    interval: current interval in days
    
    Returns: (new_interval_days, new_repetitions, new_ease_factor)
    """
    if quality < 0: quality = 0
    if quality > 5: quality = 5
    
    if quality >= 3:
        # Successful review
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)
        new_repetitions = repetitions + 1
    else:
        # Failed review - reset
        new_interval = 1
        new_repetitions = 0
    
    # Update ease factor
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if new_ef < 1.3:
        new_ef = 1.3
    
    return new_interval, new_repetitions, new_ef


def create_flashcard(front, back, card_type='vocab', level='A1', lesson_id=None, meta=None):
    """Create a new flashcard with default SM-2 parameters."""
    return {
        'id': str(int(time.time() * 1000))[-8:] + str(hash(front) % 1000)[-3:],
        'front': front,
        'back': back,
        'type': card_type,
        'level': level,
        'lesson_id': lesson_id,
        'meta': meta or {},
        'repetitions': 0,
        'ease_factor': 2.5,
        'interval': 0,
        'next_review': time.time(),
        'last_review': None,
        'created': time.time(),
        'review_count': 0,
    }


def review_flashcard(card, quality):
    """
    Review a flashcard and update its schedule.
    quality: 1-5 (1=hard, 2=good, 3=easy, 4=very easy, 5=perfect)
    
    Returns updated card.
    """
    card = card.copy()
    
    interval, repetitions, ease_factor = sm2_next_interval(
        quality,
        card.get('repetitions', 0),
        card.get('ease_factor', 2.5),
        card.get('interval', 0)
    )
    
    card['interval'] = interval
    card['repetitions'] = repetitions
    card['ease_factor'] = ease_factor
    card['next_review'] = time.time() + (interval * 86400)
    card['last_review'] = time.time()
    card['review_count'] = card.get('review_count', 0) + 1
    
    return card


def get_due_cards(cards):
    """Get cards that are due for review (next_review <= now)."""
    now = time.time()
    return [c for c in cards if c.get('next_review', 0) <= now]


def get_new_cards(cards, n=10):
    """Get cards that have never been reviewed."""
    new = [c for c in cards if c.get('review_count', 0) == 0]
    return new[:n]


def get_review_stats(cards):
    """Get statistics about the card deck."""
    now = time.time()
    total = len(cards)
    new = sum(1 for c in cards if c.get('review_count', 0) == 0)
    learning = sum(1 for c in cards if 0 < c.get('repetitions', 0) < 3)
    mature = sum(1 for c in cards if c.get('repetitions', 0) >= 3)
    due = sum(1 for c in cards if c.get('next_review', 0) <= now)
    
    return {
        'total': total,
        'new': new,
        'learning': learning,
        'mature': mature,
        'due': due,
    }


def quality_from_answer(is_correct, response_time_ms=None):
    """
    Convert exercise result to SM-2 quality score.
    quality: 1-5
    """
    if is_correct:
        if response_time_ms and response_time_ms < 3000:
            return 5  # Fast correct = perfect
        elif response_time_ms and response_time_ms < 8000:
            return 4  # Medium speed = very easy
        else:
            return 3  # Slow correct = easy
    else:
        return 1  # Incorrect = hard (not 0, to avoid too-aggressive reset)
