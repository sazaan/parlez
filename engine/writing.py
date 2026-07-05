"""
Writing Correction Mode — provides structured correction of French text
with inline annotations for grammar, style, and vocabulary.
"""
import json
import re


def build_writing_correction_prompt(text, level='A1'):
    """
    Build a system prompt for the AI to correct French writing.
    Returns structured output with corrections.
    """
    return f"""You are a French writing tutor correcting a {level} student's text.

TASK: Correct the student's French text and provide structured feedback.

RESPONSE FORMAT (use ```correction code block):
```correction
{{
  "original": "the student's original text",
  "corrected": "the corrected text",
  "score": 85,
  "level_assessment": "A2",
  "corrections": [
    {{
      "type": "grammar",
      "original": "wrong text",
      "corrected": "correct text",
      "explanation": "Why this is wrong and how to fix it"
    }},
    {{
      "type": "vocabulary",
      "original": "basic word",
      "corrected": "better word",
      "explanation": "More natural French word choice"
    }},
    {{
      "type": "style",
      "original": "awkward phrase",
      "corrected": "improved phrase",
      "explanation": "More natural French expression"
    }}
  ],
  "summary": "Overall assessment and key areas to improve",
  "strengths": ["What the student did well"],
  "improvements": ["Areas to focus on"]
}}
```

RULES:
- Be encouraging but honest
- Focus on the most important corrections (max 5-8)
- Use color coding in your explanations: 🔴 grammar, 🔵 vocabulary, 🟢 style
- Give specific examples, not just "this is wrong"
- Suggest 2-3 practice exercises at the end
- For {level} level, focus on the most impactful corrections
"""


def parse_correction_response(response_text):
    """
    Parse the AI's correction response into structured data.
    Returns the correction dict if found, or None.
    """
    # Try to extract ```correction block
    match = re.search(r'```correction\s*([\s\S]*?)```', response_text)
    if match:
        try:
            data = json.loads(match.group(1).strip())
            return data
        except:
            pass
    
    return None


def format_correction_for_display(correction):
    """
    Format a correction dict into HTML for display.
    """
    if not correction:
        return None
    
    html = '<div class="writing-correction">'
    
    # Score
    score = correction.get('score', 0)
    score_color = 'var(--correct)' if score >= 70 else 'var(--secondary)' if score >= 50 else 'var(--incorrect)'
    html += f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;padding:0.75rem;background:rgba(0,0,0,0.02);border-radius:8px">'
    html += f'<div style="font-size:1.5rem;font-weight:700;color:{score_color}">{score}%</div>'
    html += f'<div><div style="font-weight:600">Writing Score</div>'
    html += f'<div style="font-size:0.85rem;color:var(--muted-foreground)">Level: {correction.get("level_assessment", "?")}</div></div>'
    html += '</div>'
    
    # Original vs Corrected
    html += '<div style="margin-bottom:1rem">'
    html += '<div style="font-weight:600;margin-bottom:0.5rem">📝 Your Text</div>'
    html += f'<div style="padding:0.75rem;background:rgba(220,38,38,0.05);border-radius:6px;font-style:italic">{correction.get("original", "")}</div>'
    html += '<div style="font-weight:600;margin:0.5rem 0 0.25rem">✅ Corrected</div>'
    html += f'<div style="padding:0.75rem;background:rgba(22,163,74,0.05);border-radius:6px">{correction.get("corrected", "")}</div>'
    html += '</div>'
    
    # Corrections
    corrections = correction.get('corrections', [])
    if corrections:
        html += '<div style="margin-bottom:1rem">'
        html += '<div style="font-weight:600;margin-bottom:0.5rem">🔍 Corrections</div>'
        for c in corrections:
            icon = {'grammar': '🔴', 'vocabulary': '🔵', 'style': '🟢'}.get(c.get('type', ''), '⚪')
            html += f'<div style="padding:0.5rem;margin-bottom:0.375rem;background:var(--card);border:1px solid var(--border);border-radius:6px;font-size:0.85rem">'
            html += f'{icon} <strong>{c.get("original", "")}</strong> → <strong style="color:var(--correct)">{c.get("corrected", "")}</strong>'
            html += f'<div style="color:var(--muted-foreground);margin-top:0.25rem">{c.get("explanation", "")}</div>'
            html += '</div>'
        html += '</div>'
    
    # Strengths and improvements
    strengths = correction.get('strengths', [])
    improvements = correction.get('improvements', [])
    
    if strengths:
        html += '<div style="margin-bottom:0.75rem">'
        html += '<div style="font-weight:600;margin-bottom:0.25rem">💪 Strengths</div>'
        for s in strengths:
            html += f'<div style="font-size:0.85rem;padding:0.25rem 0">✓ {s}</div>'
        html += '</div>'
    
    if improvements:
        html += '<div style="margin-bottom:0.75rem">'
        html += '<div style="font-weight:600;margin-bottom:0.25rem">📈 Areas to Improve</div>'
        for i in improvements:
            html += f'<div style="font-size:0.85rem;padding:0.25rem 0">→ {i}</div>'
        html += '</div>'
    
    # Summary
    summary = correction.get('summary', '')
    if summary:
        html += f'<div style="padding:0.75rem;background:rgba(45,106,79,0.08);border-radius:6px;font-size:0.85rem">{summary}</div>'
    
    html += '</div>'
    return html
