"""
Exercise engine - handles grading, answer checking, and exercise generation.
"""

import unicodedata
import re


def normalize_answer(text):
    """Normalize French text for comparison (remove accents, punctuation, lowercase)."""
    if not isinstance(text, str):
        text = str(text)
    # Remove accents
    nfkd = unicodedata.normalize('NFKD', text)
    no_accents = ''.join(c for c in nfkd if not unicodedata.combining(c))
    # Lowercase, strip, remove extra spaces and punctuation
    result = no_accents.lower().strip()
    result = re.sub(r'[^\w\s]', '', result)
    result = re.sub(r'\s+', ' ', result)
    return result


def check_answer(exercise, user_answer):
    """
    Check if user_answer is correct for the given exercise.
    Returns (is_correct: bool, explanation: str)
    """
    if not exercise or user_answer is None:
        return False, ""
    
    user_answer = str(user_answer).strip()
    exercise_type = exercise.get('type', '') if isinstance(exercise, dict) else getattr(exercise, 'type', '')
    
    # Multiple choice - answer is index
    if exercise_type in ('multiple_choice', 'true_false', 'article_choice'):
        try:
            correct_idx = exercise.get('answer', -1) if isinstance(exercise, dict) else getattr(exercise, 'answer', -1)
            user_idx = int(user_answer)
            is_correct = user_idx == correct_idx
            explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
            return is_correct, explanation
        except (ValueError, TypeError):
            return False, "Please select an option number."
    
    # Fill in blank
    elif exercise_type == 'fill_blank':
        correct = exercise.get('answer', '') if isinstance(exercise, dict) else getattr(exercise, 'answer', '')
        acceptable = exercise.get('acceptable', []) if isinstance(exercise, dict) else getattr(exercise, 'acceptable', []) or []
        explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
        
        normalized_user = normalize_answer(user_answer)
        normalized_correct = normalize_answer(correct)
        
        if normalized_user == normalized_correct:
            return True, explanation
        
        for acc in acceptable:
            if normalized_user == normalize_answer(acc):
                return True, explanation
        
        return False, f"The correct answer is: {correct}. {explanation}"
    
    # Translation
    elif exercise_type in ('translate_to_fr', 'translate_to_en'):
        correct = exercise.get('answer', '') if isinstance(exercise, dict) else getattr(exercise, 'answer', '')
        acceptable = exercise.get('acceptable', []) if isinstance(exercise, dict) else getattr(exercise, 'acceptable', []) or []
        explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
        
        normalized_user = normalize_answer(user_answer)
        
        if normalized_user == normalize_answer(correct):
            return True, explanation
        
        for acc in acceptable:
            if normalized_user == normalize_answer(acc):
                return True, explanation
        
        return False, f"The correct translation is: {correct}. {explanation}"
    
    # Conjugation
    elif exercise_type == 'conjugation':
        correct = exercise.get('answer', '') if isinstance(exercise, dict) else getattr(exercise, 'answer', '')
        acceptable = exercise.get('acceptable', []) if isinstance(exercise, dict) else getattr(exercise, 'acceptable', []) or []
        explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
        
        normalized_user = normalize_answer(user_answer)
        
        if normalized_user == normalize_answer(correct):
            return True, explanation
        
        for acc in acceptable:
            if normalized_user == normalize_answer(acc):
                return True, explanation
        
        return False, f"The correct form is: {correct}. {explanation}"
    
    # Word bank / reorder
    elif exercise_type in ('word_bank', 'reorder'):
        correct = exercise.get('answer', '') if isinstance(exercise, dict) else getattr(exercise, 'answer', '')
        acceptable = exercise.get('acceptable', []) if isinstance(exercise, dict) else getattr(exercise, 'acceptable', []) or []
        explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
        
        normalized_user = normalize_answer(user_answer)
        
        if normalized_user == normalize_answer(correct):
            return True, explanation
        
        for acc in acceptable:
            if normalized_user == normalize_answer(acc):
                return True, explanation
        
        return False, f"The correct answer is: {correct}. {explanation}"
    
    # Matching
    elif exercise_type == 'matching':
        # Matching is handled differently - answer is a dict
        return True, "Matching exercises are interactive."
    
    # Dictation
    elif exercise_type == 'dictation':
        correct = exercise.get('answer', '') if isinstance(exercise, dict) else getattr(exercise, 'answer', '')
        acceptable = exercise.get('acceptable', []) if isinstance(exercise, dict) else getattr(exercise, 'acceptable', []) or []
        explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
        
        normalized_user = normalize_answer(user_answer)
        
        if normalized_user == normalize_answer(correct):
            return True, explanation
        
        for acc in acceptable:
            if normalized_user == normalize_answer(acc):
                return True, explanation
        
        return False, f"You heard: {correct}. {explanation}"
    
    # Short answer - loose grading
    elif exercise_type == 'short_answer':
        correct = exercise.get('answer', '') if isinstance(exercise, dict) else getattr(exercise, 'answer', '')
        explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
        
        normalized_user = normalize_answer(user_answer)
        normalized_correct = normalize_answer(correct)
        
        # Check if key words are present
        correct_words = set(normalized_correct.split())
        user_words = set(normalized_user.split())
        overlap = correct_words & user_words
        
        if len(overlap) >= len(correct_words) * 0.6:
            return True, explanation
        
        return False, f"A good answer would be: {correct}. {explanation}"
    
    # Transformation
    elif exercise_type == 'transformation':
        correct = exercise.get('answer', '') if isinstance(exercise, dict) else getattr(exercise, 'answer', '')
        acceptable = exercise.get('acceptable', []) if isinstance(exercise, dict) else getattr(exercise, 'acceptable', []) or []
        explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
        
        normalized_user = normalize_answer(user_answer)
        
        if normalized_user == normalize_answer(correct):
            return True, explanation
        
        for acc in acceptable:
            if normalized_user == normalize_answer(acc):
                return True, explanation
        
        return False, f"The correct transformation is: {correct}. {explanation}"
    
    # Pronoun replace
    elif exercise_type == 'pronoun_replace':
        correct = exercise.get('answer', '') if isinstance(exercise, dict) else getattr(exercise, 'answer', '')
        acceptable = exercise.get('acceptable', []) if isinstance(exercise, dict) else getattr(exercise, 'acceptable', []) or []
        explanation = exercise.get('explanation', '') if isinstance(exercise, dict) else getattr(exercise, 'explanation', '')
        
        normalized_user = normalize_answer(user_answer)
        
        if normalized_user == normalize_answer(correct):
            return True, explanation
        
        for acc in acceptable:
            if normalized_user == normalize_answer(acc):
                return True, explanation
        
        return False, f"The correct pronoun is: {correct}. {explanation}"
    
    # Default - use AI to grade
    return None, "This exercise needs AI grading."


def calculate_score(results):
    """Calculate score from a list of (is_correct, _) tuples."""
    if not results:
        return 0, 0, 0
    correct = sum(1 for is_correct, _ in results if is_correct)
    total = len(results)
    percentage = round((correct / total) * 100) if total > 0 else 0
    return correct, total, percentage
