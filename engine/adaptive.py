"""
Adaptive Difficulty Engine — analyzes student performance and identifies weak areas.
The AI tutor uses this to proactively target areas where the student struggles.
"""
import time
from collections import defaultdict


def analyze_weak_areas(exercise_history, test_results=None, min_samples=3, threshold=0.6):
    """
    Analyze exercise and test history to identify weak areas.
    
    Returns a dict with:
    - weak_types: exercise types where accuracy < threshold
    - weak_grammar: grammar topics with low accuracy
    - weak_vocabulary: vocabulary categories with low accuracy
    - strong_types: exercise types where accuracy >= 0.8
    - recent_trend: improving, declining, or stable
    - recommendations: specific practice suggestions
    """
    if not exercise_history:
        return {
            'weak_types': [], 'weak_grammar': [], 'weak_vocabulary': [],
            'strong_types': [], 'recent_trend': 'stable', 'recommendations': [],
            'total_exercises': 0, 'overall_accuracy': 0,
        }
    
    # --- Exercise type analysis ---
    by_type = defaultdict(lambda: {'total': 0, 'correct': 0})
    for h in exercise_history:
        t = h.get('type', 'unknown')
        by_type[t]['total'] += 1
        if h.get('correct'):
            by_type[t]['correct'] += 1
    
    weak_types = []
    strong_types = []
    for t, stats in by_type.items():
        if stats['total'] < min_samples:
            continue
        accuracy = stats['correct'] / stats['total']
        if accuracy < threshold:
            weak_types.append({'type': t, 'accuracy': round(accuracy * 100), 'total': stats['total'], 'correct': stats['correct']})
        elif accuracy >= 0.8:
            strong_types.append({'type': t, 'accuracy': round(accuracy * 100), 'total': stats['total']})
    
    weak_types.sort(key=lambda x: x['accuracy'])
    strong_types.sort(key=lambda x: -x['accuracy'])
    
    # --- Recent trend analysis ---
    recent_trend = 'stable'
    if len(exercise_history) >= 10:
        recent = exercise_history[-10:]
        older = exercise_history[-20:-10] if len(exercise_history) >= 20 else exercise_history[:10]
        
        recent_acc = sum(1 for h in recent if h.get('correct')) / len(recent)
        older_acc = sum(1 for h in older if h.get('correct')) / len(older) if older else recent_acc
        
        if recent_acc - older_acc > 0.1:
            recent_trend = 'improving'
        elif older_acc - recent_acc > 0.1:
            recent_trend = 'declining'
    
    # --- Recommendations ---
    recommendations = []
    
    if weak_types:
        top_weak = weak_types[0]
        rec_map = {
            'multiple_choice': f"You're struggling with multiple choice questions. Let's practice with some targeted quizzes.",
            'fill_blank': f"Fill-in-the-blank exercises need work. Let's practice completing sentences.",
            'translate_to_fr': f"Translation to French is challenging. Let's work on building French sentences.",
            'translate_to_en': f"French to English translation needs practice. Let's work on comprehension.",
            'conjugation': f"Verb conjugation needs attention. Let's practice conjugating common verbs.",
            'reorder': f"Word ordering needs practice. Let's build sentences from word banks.",
            'matching': f"Vocabulary matching needs work. Let's review vocabulary connections.",
            'dictation': f"Dictation exercises need practice. Let's improve listening comprehension.",
            'article_choice': f"Article usage (le/la/les) needs practice. Let's review French articles.",
            'pronoun_replace': f"Pronoun replacement needs work. Let's practice pronoun usage.",
            'transformation': f"Sentence transformation needs practice. Let's work on restructuring sentences.",
            'true_false': f"True/False comprehension needs improvement. Let's work on reading carefully.",
        }
        rec = rec_map.get(top_weak['type'], f"Focus on {top_weak['type']} exercises (accuracy: {top_weak['accuracy']}%).")
        recommendations.append(rec)
    
    if recent_trend == 'declining':
        recommendations.append("Your recent performance has declined. Let's review what you've learned and reinforce the basics.")
    elif recent_trend == 'improving':
        recommendations.append("Great progress! You're improving. Let's keep building on your strengths.")
    
    # Overall stats
    total = sum(s['total'] for s in by_type.values())
    correct = sum(s['correct'] for s in by_type.values())
    overall_acc = round((correct / total) * 100) if total > 0 else 0
    
    return {
        'weak_types': weak_types,
        'strong_types': strong_types,
        'recent_trend': recent_trend,
        'recommendations': recommendations,
        'total_exercises': total,
        'overall_accuracy': overall_acc,
    }


def get_difficulty_adjustments(level, weak_analysis):
    """
    Determine how to adjust the AI tutor's behavior based on weak areas.
    Returns adjustments dict with:
    - french_ratio: how much French to use (0.0-1.0)
    - focus_areas: topics to emphasize
    - practice_count: how many exercises to generate
    - complexity: suggested complexity level
    """
    base_ratios = {'A1': 0.4, 'A2': 0.5, 'B1': 0.65, 'B2': 0.8}
    french_ratio = base_ratios.get(level, 0.5)
    
    # Adjust based on performance
    overall_acc = weak_analysis.get('overall_accuracy', 70)
    if overall_acc < 50:
        french_ratio = max(0.3, french_ratio - 0.15)  # More English for struggling students
    elif overall_acc > 85:
        french_ratio = min(0.9, french_ratio + 0.1)  # More French for advanced students
    
    # Determine focus areas
    focus_areas = []
    for weak in weak_analysis.get('weak_types', []):
        focus_areas.append(weak['type'])
    
    # Adjust practice count based on weak areas
    practice_count = 3
    if len(focus_areas) > 2:
        practice_count = 5
    elif len(focus_areas) == 0:
        practice_count = 4  # More exercises for students doing well
    
    # Determine complexity
    complexity = 'normal'
    if overall_acc < 40:
        complexity = 'simpler'
    elif overall_acc > 80:
        complexity = 'more challenging'
    
    return {
        'french_ratio': round(french_ratio, 2),
        'focus_areas': focus_areas,
        'practice_count': practice_count,
        'complexity': complexity,
    }


def build_adaptive_prompt_addition(level, weak_analysis, adjustments):
    """
    Build an addition to the system prompt that instructs the AI to
    proactively target weak areas.
    """
    parts = []
    
    # Weak areas notification
    if weak_analysis.get('weak_types'):
        weak_names = [w['type'].replace('_', ' ') for w in weak_analysis['weak_types'][:3]]
        parts.append(f"WEAK AREAS DETECTED: The student struggles with: {', '.join(weak_names)}. Give EXTRA practice on these topics. When teaching new content, include examples and exercises that target these areas.")
    
    # Strong areas acknowledgment
    if weak_analysis.get('strong_types'):
        strong_names = [s['type'].replace('_', ' ') for s in weak_analysis['strong_types'][:3]]
        parts.append(f"STRENGTHS: The student excels at: {', '.join(strong_names)}. You can move faster on these topics and use more complex examples.")
    
    # Trend adjustment
    trend = weak_analysis.get('recent_trend', 'stable')
    if trend == 'declining':
        parts.append("RECENT TREND: The student's performance has been declining. Slow down, review fundamentals, and provide more encouragement.")
    elif trend == 'improving':
        parts.append("RECENT TREND: The student is improving! Reinforce positive momentum with encouraging feedback.")
    
    # French ratio adjustment
    french_pct = round(adjustments.get('french_ratio', 0.5) * 100)
    eng_pct = 100 - french_pct
    parts.append(f"LANGUAGE RATIO: Use approximately {french_pct}% French and {eng_pct}% English in your responses.")
    
    # Practice count
    count = adjustments.get('practice_count', 3)
    parts.append(f"PRACTICE: Generate {count} exercises after explaining each concept.")
    
    # Complexity
    complexity = adjustments.get('complexity', 'normal')
    if complexity == 'simpler':
        parts.append("COMPLEXITY: Use simpler vocabulary and shorter sentences. Break down complex ideas into smaller steps.")
    elif complexity == 'more challenging':
        parts.append("COMPLEXITY: The student is doing well. Use more challenging vocabulary, complex sentence structures, and nuanced explanations.")
    
    if parts:
        return "\n\n" + "\n".join(parts)
    return ""
