#!/usr/bin/env python3
"""
Convert TypeScript course files to Python data files.
Uses a more robust parsing approach to extract full lesson data.
"""

import re
import json
import os

TS_DIR = '/home/sajjan/sajjan/parlez-french/src/lib/courses'
OUT_DIR = '/home/sajjan/sajjan/parlez-french/chatbot/courses'

def find_matching_brace(text, start):
    """Find the matching closing brace for an opening brace at position start."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        elif text[i] == "'" or text[i] == '"' or text[i] == '`':
            # Skip strings
            quote = text[i]
            i += 1
            while i < len(text) and text[i] != quote:
                if text[i] == '\\':
                    i += 1  # skip escaped char
                i += 1
        i += 1
    return -1

def extract_ts_string(text, key):
    """Extract a TypeScript string value for a given key."""
    patterns = [
        rf'{key}:\s*"([^"]*)"',
        rf"{key}:\s*'([^']*)'",
        rf'{key}:\s*`([^`]*)`',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None

def extract_ts_number(text, key):
    """Extract a TypeScript number value for a given key."""
    m = re.search(rf'{key}:\s*(\d+)', text)
    return int(m.group(1)) if m else None

def extract_ts_bool(text, key):
    """Extract a TypeScript boolean value for a given key."""
    m = re.search(rf'{key}:\s*(true|false)', text)
    if m:
        return m.group(1) == 'true'
    return None

def extract_ts_array(text, key):
    """Extract a TypeScript array of strings."""
    pattern = rf'{key}:\s*\[([^\]]*)\]'
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return []
    content = m.group(1)
    return re.findall(r"['\"]([^'\"]*?)['\"]", content)

def parse_vocabulary(text):
    """Parse vocabulary items from TypeScript."""
    items = []
    # Find vocabulary array
    vocab_match = re.search(r'vocabulary:\s*\[', text)
    if not vocab_match:
        return items
    
    start = vocab_match.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
        i += 1
    
    vocab_text = text[start:i-1]
    
    # Split by }, { pattern to get individual items
    items_raw = re.split(r'\}\s*,\s*\{', vocab_text)
    
    for item_raw in items_raw:
        item_raw = item_raw.strip().strip('{}')
        item = {}
        
        # Extract fields
        for key in ['fr', 'en', 'ipa', 'example', 'exampleEn', 'category']:
            val = extract_ts_string(item_raw, key)
            if val:
                item[key] = val
        
        if item.get('fr'):
            items.append(item)
    
    return items

def parse_grammar(text):
    """Parse grammar rules from TypeScript."""
    rules = []
    # Find grammar array
    grammar_match = re.search(r'grammar:\s*\[', text)
    if not grammar_match:
        return rules
    
    start = grammar_match.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
        i += 1
    
    grammar_text = text[start:i-1]
    
    # Find each GrammarRule object
    rule_pattern = r'\{\s*title:'
    for m in re.finditer(rule_pattern, grammar_text):
        rule_start = m.start()
        rule_end = find_matching_brace(grammar_text, rule_start)
        if rule_end == -1:
            continue
        
        rule_text = grammar_text[rule_start:rule_end+1]
        
        rule = {}
        rule['title'] = extract_ts_string(rule_text, 'title') or ''
        rule['explanation'] = extract_ts_string(rule_text, 'explanation') or ''
        
        # Parse examples
        examples = []
        ex_match = re.search(r'examples:\s*\[', rule_text)
        if ex_match:
            ex_start = ex_match.end()
            ex_depth = 1
            j = ex_start
            while j < len(rule_text) and ex_depth > 0:
                if rule_text[j] == '[':
                    ex_depth += 1
                elif rule_text[j] == ']':
                    ex_depth -= 1
                j += 1
            ex_text = rule_text[ex_start:j-1]
            ex_items = re.split(r'\}\s*,\s*\{', ex_text)
            for ex_item in ex_items:
                ex_item = ex_item.strip().strip('{}')
                ex = {}
                for key in ['fr', 'en']:
                    val = extract_ts_string(ex_item, key)
                    if val:
                        ex[key] = val
                if ex:
                    examples.append(ex)
        rule['examples'] = examples
        
        # Parse table
        table = {}
        table_match = re.search(r'table:\s*\{', rule_text)
        if table_match:
            t_start = table_match.end()
            t_end = find_matching_brace(rule_text, t_start)
            if t_end > 0:
                table_text = rule_text[t_start:t_end]
                table['caption'] = extract_ts_string(table_text, 'caption')
                # Parse headers
                headers_match = re.search(r'headers:\s*\[([^\]]*)\]', table_text)
                if headers_match:
                    table['headers'] = re.findall(r"['\"]([^'\"]*?)['\"]", headers_match.group(1))
                # Parse rows
                rows_match = re.search(r'rows:\s*\[', table_text)
                if rows_match:
                    r_start = rows_match.end()
                    r_depth = 1
                    k = r_start
                    while k < len(table_text) and r_depth > 0:
                        if table_text[k] == '[':
                            r_depth += 1
                        elif table_text[k] == ']':
                            r_depth -= 1
                        k += 1
                    rows_text = table_text[r_start:k-1]
                    rows = []
                    for row_match in re.finditer(r'\[([^\]]*)\]', rows_text):
                        row = re.findall(r"['\"]([^'\"]*?)['\"]", row_match.group(1))
                        if row:
                            rows.append(row)
                    table['rows'] = rows
        rule['table'] = table if table else None
        
        # Parse tip
        rule['tip'] = extract_ts_string(rule_text, 'tip')
        
        rules.append(rule)
    
    return rules

def parse_dialogue(text):
    """Parse dialogue lines from TypeScript."""
    lines = []
    # Find dialogue array
    dialogue_match = re.search(r'dialogue:\s*\[', text)
    if not dialogue_match:
        return lines
    
    start = dialogue_match.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
        i += 1
    
    dialogue_text = text[start:i-1]
    
    # Split by }, { pattern
    items = re.split(r'\}\s*,\s*\{', dialogue_text)
    
    for item in items:
        item = item.strip().strip('{}')
        line = {}
        line['speaker'] = extract_ts_string(item, 'speaker') or 'A'
        line['name'] = extract_ts_string(item, 'name') or ''
        line['fr'] = extract_ts_string(item, 'fr') or ''
        line['en'] = extract_ts_string(item, 'en') or ''
        if line['fr']:
            lines.append(line)
    
    return lines

def parse_exercises(text):
    """Parse exercises from TypeScript."""
    exercises = []
    # Find exercises array
    exercises_match = re.search(r'exercises:\s*\[', text)
    if not exercises_match:
        return exercises
    
    start = exercises_match.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
        i += 1
    
    exercises_text = text[start:i-1]
    
    # Find each Exercise object
    ex_pattern = r'\{\s*id:'
    for m in re.finditer(ex_pattern, exercises_text):
        ex_start = m.start()
        ex_end = find_matching_brace(exercises_text, ex_start)
        if ex_end == -1:
            continue
        
        ex_text = exercises_text[ex_start:ex_end+1]
        
        ex = {}
        ex['id'] = extract_ts_string(ex_text, 'id') or ''
        ex['type'] = extract_ts_string(ex_text, 'type') or 'multiple_choice'
        ex['prompt'] = extract_ts_string(ex_text, 'prompt') or ''
        
        # Parse options
        options_match = re.search(r'options:\s*\[([^\]]*)\]', ex_text)
        if options_match:
            ex['options'] = re.findall(r"['\"]([^'\"]*?)['\"]", options_match.group(1))
        
        # Parse answer
        answer_match = re.search(r'answer:\s*(\d+)', ex_text)
        if answer_match:
            ex['answer'] = int(answer_match.group(1))
        else:
            answer_str = extract_ts_string(ex_text, 'answer')
            if answer_str:
                ex['answer'] = answer_str
        
        # Parse explanation
        ex['explanation'] = extract_ts_string(ex_text, 'explanation') or ''
        
        # Parse pairs (for matching exercises)
        pairs_match = re.search(r'pairs:\s*\[', ex_text)
        if pairs_match:
            p_start = pairs_match.end()
            p_depth = 1
            j = p_start
            while j < len(ex_text) and p_depth > 0:
                if ex_text[j] == '[':
                    p_depth += 1
                elif ex_text[j] == ']':
                    p_depth -= 1
                j += 1
            pairs_text = ex_text[p_start:j-1]
            pairs = []
            for pair_match in re.finditer(r'\{([^}]*)\}', pairs_text):
                pair = {}
                left = extract_ts_string(pair_match.group(1), 'left')
                right = extract_ts_string(pair_match.group(1), 'right')
                if left and right:
                    pairs.append({'left': left, 'right': right})
            ex['pairs'] = pairs
        
        # Parse wordBank
        wordbank_match = re.search(r'wordBank:\s*\[([^\]]*)\]', ex_text)
        if wordbank_match:
            ex['wordBank'] = re.findall(r"['\"]([^'\"]*?)['\"]", wordbank_match.group(1))
        
        # Parse words (for reorder)
        words_match = re.search(r'words:\s*\[([^\]]*)\]', ex_text)
        if words_match:
            ex['words'] = re.findall(r"['\"]([^'\"]*?)['\"]", words_match.group(1))
        
        # Parse audioText
        ex['audioText'] = extract_ts_string(ex_text, 'audioText')
        
        exercises.append(ex)
    
    return exercises

def parse_conjugation(text):
    """Parse conjugation data from TypeScript."""
    conj_match = re.search(r'conjugation:\s*\{', text)
    if not conj_match:
        return None
    
    start = conj_match.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1
    
    conj_text = text[start:i-1]
    
    result = {'verbs': [], 'practice': []}
    
    # Parse verbs
    verb_pattern = r'infinitive:'
    for m in re.finditer(verb_pattern, conj_text):
        # Find the opening { of this verb object (it sits just before "infinitive:")
        verb_start = m.start()
        open_idx = conj_text.rfind('{', 0, verb_start)
        if open_idx == -1:
            continue
        verb_end = find_matching_brace(conj_text, open_idx)
        if verb_end == -1:
            continue

        verb_text = conj_text[open_idx:verb_end+1]
        
        verb = {}
        verb['infinitive'] = extract_ts_string(verb_text, 'infinitive') or ''
        verb['translation'] = extract_ts_string(verb_text, 'translation') or ''
        verb['tense'] = extract_ts_string(verb_text, 'tense') or ''
        
        # Parse conjugations
        conj_items = []
        conj_match2 = re.search(r'conjugations:\s*\[', verb_text)
        if conj_match2:
            c_start = conj_match2.end()
            c_depth = 1
            j = c_start
            while j < len(verb_text) and c_depth > 0:
                if verb_text[j] == '[':
                    c_depth += 1
                elif verb_text[j] == ']':
                    c_depth -= 1
                j += 1
            c_text = verb_text[c_start:j-1]
            items = re.split(r'\}\s*,\s*\{', c_text)
            for item in items:
                item = item.strip().strip('{}')
                ci = {}
                ci['pronoun'] = extract_ts_string(item, 'pronoun') or ''
                ci['form'] = extract_ts_string(item, 'form') or ''
                if ci['pronoun']:
                    conj_items.append(ci)
        verb['conjugations'] = conj_items
        
        verb['sentenceRule'] = extract_ts_string(verb_text, 'sentenceRule') or ''
        
        # Parse sentenceExamples
        sent_examples = []
        sent_match = re.search(r'sentenceExamples:\s*\[', verb_text)
        if sent_match:
            s_start = sent_match.end()
            s_depth = 1
            k = s_start
            while k < len(verb_text) and s_depth > 0:
                if verb_text[k] == '[':
                    s_depth += 1
                elif verb_text[k] == ']':
                    s_depth -= 1
                k += 1
            s_text = verb_text[s_start:k-1]
            s_items = re.split(r'\}\s*,\s*\{', s_text)
            for item in s_items:
                item = item.strip().strip('{}')
                se = {}
                se['fr'] = extract_ts_string(item, 'fr') or ''
                se['en'] = extract_ts_string(item, 'en') or ''
                if se['fr']:
                    sent_examples.append(se)
        verb['sentenceExamples'] = sent_examples
        
        result['verbs'].append(verb)
    
    # Parse practice exercises
    practice_match = re.search(r'practice:\s*\[', conj_text)
    if practice_match:
        p_start = practice_match.end()
        p_depth = 1
        j = p_start
        while j < len(conj_text) and p_depth > 0:
            if conj_text[j] == '[':
                p_depth += 1
            elif conj_text[j] == ']':
                p_depth -= 1
            j += 1
        p_text = conj_text[p_start:j-1]
        
        ex_pattern = r'\{\s*id:'
        for m in re.finditer(ex_pattern, p_text):
            ex_start = m.start()
            ex_end = find_matching_brace(p_text, ex_start)
            if ex_end == -1:
                continue
            ex_text = p_text[ex_start:ex_end+1]
            
            ex = {}
            ex['id'] = extract_ts_string(ex_text, 'id') or ''
            ex['type'] = extract_ts_string(ex_text, 'type') or 'conjugation'
            ex['prompt'] = extract_ts_string(ex_text, 'prompt') or ''
            ex['answer'] = extract_ts_string(ex_text, 'answer') or ''
            ex['explanation'] = extract_ts_string(ex_text, 'explanation') or ''
            
            options_match = re.search(r'options:\s*\[([^\]]*)\]', ex_text)
            if options_match:
                ex['options'] = re.findall(r"['\"]([^'\"]*?)['\"]", options_match.group(1))
            
            result['practice'].append(ex)
    
    return result

def parse_activities(text):
    """Parse workbook activities from TypeScript."""
    activities_match = re.search(r'activities:\s*\[', text)
    if not activities_match:
        return []
    
    start = activities_match.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
        i += 1
    
    activities_text = text[start:i-1]
    return parse_exercises_from_text(activities_text)

def parse_exercises_from_text(text):
    """Parse exercises from a text block."""
    exercises = []
    ex_pattern = r'\{\s*id:'
    for m in re.finditer(ex_pattern, text):
        ex_start = m.start()
        ex_end = find_matching_brace(text, ex_start)
        if ex_end == -1:
            continue
        ex_text = text[ex_start:ex_end+1]
        
        ex = {}
        ex['id'] = extract_ts_string(ex_text, 'id') or ''
        ex['type'] = extract_ts_string(ex_text, 'type') or 'multiple_choice'
        ex['prompt'] = extract_ts_string(ex_text, 'prompt') or ''
        
        options_match = re.search(r'options:\s*\[([^\]]*)\]', ex_text)
        if options_match:
            ex['options'] = re.findall(r"['\"]([^'\"]*?)['\"]", options_match.group(1))
        
        answer_match = re.search(r'answer:\s*(\d+)', ex_text)
        if answer_match:
            ex['answer'] = int(answer_match.group(1))
        else:
            answer_str = extract_ts_string(ex_text, 'answer')
            if answer_str:
                ex['answer'] = answer_str
        
        ex['explanation'] = extract_ts_string(ex_text, 'explanation') or ''
        ex['audioText'] = extract_ts_string(ex_text, 'audioText')
        
        exercises.append(ex)
    
    return exercises

def parse_lesson(text):
    """Parse a complete lesson from TypeScript."""
    lesson = {}
    lesson['id'] = extract_ts_string(text, 'id') or ''
    lesson['title'] = extract_ts_string(text, 'title') or ''
    lesson['titleFr'] = extract_ts_string(text, 'titleFr') or ''
    lesson['description'] = extract_ts_string(text, 'description') or ''
    lesson['objectives'] = extract_ts_array(text, 'objectives')
    lesson['estimatedMinutes'] = extract_ts_number(text, 'estimatedMinutes') or 30
    lesson['culturalNote'] = extract_ts_string(text, 'culturalNote')
    lesson['vocabulary'] = parse_vocabulary(text)
    lesson['grammar'] = parse_grammar(text)
    lesson['conjugation'] = parse_conjugation(text)
    lesson['dialogue'] = parse_dialogue(text)
    lesson['exercises'] = parse_exercises(text)
    lesson['activities'] = parse_activities(text)
    return lesson

def parse_unit(text):
    """Parse a unit from TypeScript."""
    unit = {}
    unit['id'] = extract_ts_string(text, 'id') or ''
    unit['title'] = extract_ts_string(text, 'title') or ''
    unit['titleFr'] = extract_ts_string(text, 'titleFr') or ''
    unit['theme'] = extract_ts_string(text, 'theme') or ''
    unit['description'] = extract_ts_string(text, 'description') or ''
    unit['lessons'] = []
    
    # Find lessons array
    lessons_match = re.search(r'lessons:\s*\[', text)
    if lessons_match:
        start = lessons_match.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == '[':
                depth += 1
            elif text[i] == ']':
                depth -= 1
            i += 1
        
        lessons_text = text[start:i-1]
        
        # Find each lesson
        lesson_pattern = r'\{\s*id:\s*[\'"][ab][12]-u\d+-l\d+[\'"]'
        positions = [m.start() for m in re.finditer(lesson_pattern, lessons_text)]
        
        for j, pos in enumerate(positions):
            end = positions[j+1] if j+1 < len(positions) else len(lessons_text)
            lesson_text = lessons_text[pos:end]
            lesson = parse_lesson(lesson_text)
            if lesson.get('id'):
                unit['lessons'].append(lesson)
    
    return unit

def parse_course(ts_file):
    """Parse a complete course from a TypeScript file."""
    with open(ts_file, 'r') as f:
        content = f.read()
    
    course = {}
    course['level'] = extract_ts_string(content, 'level') or ''
    course['title'] = extract_ts_string(content, 'title') or ''
    course['book'] = extract_ts_string(content, 'book') or ''
    course['description'] = extract_ts_string(content, 'description') or ''
    course['cefrDescription'] = extract_ts_string(content, 'cefrDescription') or ''
    course['color'] = extract_ts_string(content, 'color') or '#333333'
    course['units'] = []
    
    # Find units array
    units_match = re.search(r'units:\s*\[', content)
    if units_match:
        start = units_match.end()
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == '[':
                depth += 1
            elif content[i] == ']':
                depth -= 1
            i += 1
        
        units_text = content[start:i-1]
        
        # Find each unit
        unit_pattern = r"\{\s*id:\s*['\"][ab][12]-u\d+['\"]"
        positions = [m.start() for m in re.finditer(unit_pattern, units_text)]
        
        for j, pos in enumerate(positions):
            end = positions[j+1] if j+1 < len(positions) else len(units_text)
            unit_text = units_text[pos:end]
            unit = parse_unit(unit_text)
            if unit.get('id'):
                course['units'].append(unit)
    
    return course

def escape_py(s):
    """Escape a string for Python."""
    if s is None:
        return "''"
    s = str(s)
    s = s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')
    return f"'{s}'"

def write_python_course(course, output_path):
    """Write a Python course file."""
    lines = []
    lines.append('from .types import *')
    lines.append('')
    lines.append(f'# {course["level"]} Course')
    lines.append(f'{course["level"].lower()}_course = Course(')
    lines.append(f"    level={escape_py(course['level'])},")
    lines.append(f"    title={escape_py(course['title'])},")
    lines.append(f"    book={escape_py(course['book'])},")
    lines.append(f"    description={escape_py(course['description'])},")
    lines.append(f"    cefrDescription={escape_py(course['cefrDescription'])},")
    lines.append(f"    color={escape_py(course['color'])},")
    lines.append(f"    units=[")
    
    for unit in course['units']:
        lines.append(f"        Unit(")
        lines.append(f"            id={escape_py(unit['id'])},")
        lines.append(f"            title={escape_py(unit['title'])},")
        lines.append(f"            titleFr={escape_py(unit['titleFr'])},")
        lines.append(f"            theme={escape_py(unit['theme'])},")
        lines.append(f"            description={escape_py(unit['description'])},")
        lines.append(f"            lessons=[")
        
        for lesson in unit['lessons']:
            lines.append(f"                Lesson(")
            lines.append(f"                    id={escape_py(lesson['id'])},")
            lines.append(f"                    title={escape_py(lesson['title'])},")
            lines.append(f"                    titleFr={escape_py(lesson['titleFr'])},")
            lines.append(f"                    description={escape_py(lesson['description'])},")
            
            if lesson.get('objectives'):
                lines.append(f"                    objectives={json.dumps(lesson['objectives'])},")
            
            if lesson.get('vocabulary'):
                lines.append(f"                    vocabulary=[")
                for v in lesson['vocabulary']:
                    lines.append(f"                        VocabItem(fr={escape_py(v.get('fr'))}, en={escape_py(v.get('en'))}, ipa={escape_py(v.get('ipa'))}, example={escape_py(v.get('example'))}, exampleEn={escape_py(v.get('exampleEn'))}, category={escape_py(v.get('category'))}),")
                lines.append(f"                    ],")
            
            if lesson.get('grammar'):
                lines.append(f"                    grammar=[")
                for g in lesson['grammar']:
                    lines.append(f"                        GrammarRule(")
                    lines.append(f"                            title={escape_py(g['title'])},")
                    lines.append(f"                            explanation={escape_py(g['explanation'])},")
                    if g.get('examples'):
                        examples_json = json.dumps(g['examples'])
                        lines.append(f"                            examples=[GrammarExample(fr=ex['fr'], en=ex['en']) for ex in {examples_json}],")
                    if g.get('table'):
                        table = g['table']
                        lines.append(f"                            table=GrammarTable(headers={json.dumps(table.get('headers', []))}, rows={json.dumps(table.get('rows', []))}, caption={escape_py(table.get('caption'))}),")
                    if g.get('tip'):
                        lines.append(f"                            tip={escape_py(g['tip'])},")
                    lines.append(f"                        ),")
                lines.append(f"                    ],")
            
            if lesson.get('conjugation'):
                conj = lesson['conjugation']
                lines.append(f"                    conjugation=ConjugationData(")
                if conj.get('verbs'):
                    lines.append(f"                        verbs=[")
                    for v in conj['verbs']:
                        lines.append(f"                            ConjugationVerb(")
                        lines.append(f"                                infinitive={escape_py(v.get('infinitive'))},")
                        lines.append(f"                                translation={escape_py(v.get('translation'))},")
                        lines.append(f"                                tense={escape_py(v.get('tense'))},")
                        lines.append(f"                                conjugations={json.dumps(v.get('conjugations', []))},")
                        lines.append(f"                                sentenceRule={escape_py(v.get('sentenceRule'))},")
                        if v.get('sentenceExamples'):
                            sent_ex_json = json.dumps(v['sentenceExamples'])
                            lines.append(f"                                sentenceExamples=[GrammarExample(fr=se['fr'], en=se['en']) for se in {sent_ex_json}],")
                        lines.append(f"                            ),")
                    lines.append(f"                        ],")
                if conj.get('practice'):
                    lines.append(f"                        practice=[")
                    for p in conj['practice']:
                        p_opts = 'None'
                        if p.get('options'):
                            p_opts = '[' + ', '.join(escape_py(o) for o in p['options'] if o is not None) + ']'
                        lines.append(f"                            Exercise(id={escape_py(p['id'])}, type={escape_py(p['type'])}, prompt={escape_py(p['prompt'])}, answer={escape_py(p.get('answer'))}, options={p_opts}, explanation={escape_py(p.get('explanation'))}),")
                    lines.append(f"                        ],")
                lines.append(f"                    ),")
            
            if lesson.get('dialogue'):
                lines.append(f"                    dialogue=[")
                for d in lesson['dialogue']:
                    lines.append(f"                        DialogueLine(speaker={escape_py(d.get('speaker', 'A'))}, name={escape_py(d.get('name'))}, fr={escape_py(d.get('fr'))}, en={escape_py(d.get('en'))}),")
                lines.append(f"                    ],")
            
            if lesson.get('exercises'):
                lines.append(f"                    exercises=[")
                for e in lesson['exercises']:
                    opts_str = 'None'
                    if e.get('options'):
                        opts_list = [o for o in e['options'] if o is not None]
                        if opts_list:
                            opts_str = '[' + ', '.join(escape_py(o) for o in opts_list) + ']'
                    answer = 'None'
                    if e.get('answer') is not None:
                        answer = repr(e['answer'])
                    if answer in ('null', 'undefined'):
                        answer = 'None'
                    lines.append(f"                        Exercise(id={escape_py(e['id'])}, type={escape_py(e['type'])}, prompt={escape_py(e['prompt'])}, options={opts_str}, answer={answer}, explanation={escape_py(e.get('explanation'))}),")
                lines.append(f"                    ],")
            
            if lesson.get('activities'):
                lines.append(f"                    activities=[")
                for a in lesson['activities']:
                    opts_str = 'None'
                    if a.get('options'):
                        opts_list = [o for o in a['options'] if o is not None]
                        if opts_list:
                            opts_str = '[' + ', '.join(escape_py(o) for o in opts_list) + ']'
                    answer = 'None'
                    if a.get('answer') is not None:
                        answer = repr(a['answer'])
                    if answer in ('null', 'undefined'):
                        answer = 'None'
                    lines.append(f"                        Exercise(id={escape_py(a['id'])}, type={escape_py(a['type'])}, prompt={escape_py(a['prompt'])}, options={opts_str}, answer={answer}, explanation={escape_py(a.get('explanation'))}),")
                lines.append(f"                    ],")
            
            if lesson.get('culturalNote'):
                lines.append(f"                    culturalNote={escape_py(lesson['culturalNote'])},")
            
            lines.append(f"                    estimatedMinutes={lesson.get('estimatedMinutes', 30)},")
            lines.append(f"                ),")
        
        lines.append(f"            ],")
        lines.append(f"        ),")
    
    lines.append(f"    ],")
    lines.append(f")")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

def main():
    levels = ['a1', 'a2', 'b1', 'b2']
    
    for level in levels:
        ts_file = os.path.join(TS_DIR, f'{level}.ts')
        if not os.path.exists(ts_file):
            print(f"Skipping {level}: file not found")
            continue
        
        print(f"Parsing {level}.ts...")
        course = parse_course(ts_file)
        
        output_path = os.path.join(OUT_DIR, f'{level}_course.py')
        write_python_course(course, output_path)
        
        unit_count = len(course['units'])
        lesson_count = sum(len(u['lessons']) for u in course['units'])
        total_vocab = sum(len(l.get('vocabulary', [])) for u in course['units'] for l in u['lessons'])
        total_grammar = sum(len(l.get('grammar', [])) for u in course['units'] for l in u['lessons'])
        total_exercises = sum(len(l.get('exercises', [])) for u in course['units'] for l in u['lessons'])
        
        print(f"  ✓ Generated {output_path}")
        print(f"    {unit_count} units, {lesson_count} lessons")
        print(f"    {total_vocab} vocab items, {total_grammar} grammar rules, {total_exercises} exercises")

if __name__ == '__main__':
    main()
