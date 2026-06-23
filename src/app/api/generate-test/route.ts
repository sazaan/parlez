// AI-powered TEF/TCF question generation API
// Uses OpenAI SDK with NVIDIA NIM endpoint (Z.AI GLM model)
import { NextRequest, NextResponse } from 'next/server';
import { chatCompletion, AI_MODEL } from '@/lib/ai-client';

export const runtime = 'nodejs';
export const maxDuration = 60;

interface GeneratedQuestion {
  id: string;
  type: 'multiple_choice';
  prompt: string;
  options: string[];
  answer: number;
  explanation: string;
  audioText?: string;
  level: string;
}

const EXAM_FORMATS = {
  TEF: {
    reading: { count: 50, duration: 60 },
    listening: { count: 60, duration: 40 },
    vocabulary_grammar: { count: 40, duration: 30 },
  },
  TCF: {
    listening: { count: 29, duration: 25 },
    language_structures: { count: 18, duration: 15 },
    reading: { count: 29, duration: 45 },
  },
};

function getPromptForSection(testType: string, section: string, batchSize: number, batchIndex: number): string {
  const format = EXAM_FORMATS[testType as keyof typeof EXAM_FORMATS]?.[section as keyof typeof EXAM_FORMATS['TEF']];
  const totalQuestions = format?.count || 15;
  const startQ = batchIndex * batchSize + 1;
  const endQ = Math.min(startQ + batchSize - 1, totalQuestions);

  if (testType === 'TEF') {
    if (section === 'reading') {
      return `Create ${batchSize} TEF Canada reading questions (Q${startQ}-${endQ} of ${totalQuestions}).
TEF reading: Section A (signs Q1-15), Section B (short texts Q16-35), Section C (longer texts Q36-50).
Each: a French text + comprehension question + 4 options + 1 correct answer + explanation + CEFR level.

Return ONLY a JSON array. Use \\u2019 for apostrophes. No markdown.
[{"prompt":"FERMÉ LE LUNDI. Ouvert mardi-samedi 9h-19h.\\nQue dit cette affiche?","options":["A","B","C","D"],"answer":0,"explanation":"reason","level":"A1"}]`;
    }
    if (section === 'listening') {
      return `Create ${batchSize} TEF Canada listening questions (Q${startQ}-${endQ} of ${totalQuestions}).
Each: audioText (French text spoken) + question about what was said + 4 options + 1 correct answer + explanation + level.
Q1-15: announcements. Q16-35: conversations. Q36-60: radio/interviews.

Return ONLY a JSON array. Use \\u2019 for apostrophes. No markdown.
[{"prompt":"What does the announcement say?","options":["A","B","C","D"],"answer":0,"explanation":"reason","audioText":"French text here","level":"A1"}]`;
    }
    if (section === 'vocabulary_grammar') {
      return `Create ${batchSize} TEF vocabulary/grammar questions (Q${startQ}-${endQ} of ${totalQuestions}).
Each: sentence with blank or choose correct form + 4 options + 1 correct + explanation + level.
Q1-20: vocabulary. Q21-40: grammar (conjugation, prepositions, pronouns, tenses).

Return ONLY a JSON array. Use \\u2019 for apostrophes. No markdown.
[{"prompt":"Je _____ au cinema.","options":["vais","suis alle","allais","irai"],"answer":0,"explanation":"reason","level":"A1"}]`;
    }
  }

  if (testType === 'TCF') {
    if (section === 'reading') {
      const diff = getTCFDifficulty(startQ, 29);
      return `Create ${batchSize} TCF reading questions (Q${startQ}-${endQ} of 29). Difficulty: ${diff}.
Progressive: Q1-6=A1, Q7-12=A2, Q13-18=B1, Q19-24=B2, Q25-29=C1-C2.
Each: French text + comprehension question + 4 options + 1 correct + explanation + level.

Return ONLY a JSON array. Use \\u2019 for apostrophes. No markdown.
[{"prompt":"text + question","options":["A","B","C","D"],"answer":0,"explanation":"reason","level":"A1"}]`;
    }
    if (section === 'listening') {
      const diff = getTCFDifficulty(startQ, 29);
      return `Create ${batchSize} TCF listening questions (Q${startQ}-${endQ} of 29). Difficulty: ${diff}.
Each: audioText (spoken French) + question + 4 options + 1 correct + explanation + level.

Return ONLY a JSON array. Use \\u2019 for apostrophes. No markdown.
[{"prompt":"question","options":["A","B","C","D"],"answer":0,"explanation":"reason","audioText":"spoken text","level":"A1"}]`;
    }
    if (section === 'language_structures') {
      const diff = getTCFDifficulty(startQ, 18);
      return `Create ${batchSize} TCF language structure questions (Q${startQ}-${endQ} of 18). Difficulty: ${diff}.
Grammar, conjugation, vocabulary. Each: sentence with blank + 4 options + 1 correct + explanation + level.

Return ONLY a JSON array. Use \\u2019 for apostrophes. No markdown.
[{"prompt":"Si j'avais su, je _____ ne pas venir.","options":["avais decide","aurais decide","decide","deciderais"],"answer":1,"explanation":"reason","level":"B2"}]`;
    }
  }
  return 'Generate 10 French exam questions as JSON array.';
}

function getTCFDifficulty(startQ: number, total: number): string {
  if (total === 29) {
    if (startQ <= 6) return 'A1';
    if (startQ <= 12) return 'A2';
    if (startQ <= 18) return 'B1';
    if (startQ <= 24) return 'B2';
    return 'C1-C2';
  }
  if (startQ <= 4) return 'A1-A2';
  if (startQ <= 10) return 'B1';
  if (startQ <= 14) return 'B2';
  return 'C1-C2';
}

function extractJsonArray(content: string): any[] {
  let cleaned = content.replace(/```json\n?/gi, '').replace(/```\n?/g, '').trim();
  try { return JSON.parse(cleaned); } catch {}
  const arrayMatch = cleaned.match(/\[[\s\S]*\]/);
  if (arrayMatch) {
    let jsonStr = arrayMatch[0];
    try { return JSON.parse(jsonStr); } catch {}
    jsonStr = jsonStr
      .replace(/,\s*]/g, ']')
      .replace(/,\s*}/g, '}')
      .replace(/\u2019/g, "'")
      .replace(/\u201c/g, '"')
      .replace(/\u201d/g, '"')
      .replace(/\u00ab/g, '"')
      .replace(/\u00bb/g, '"')
      .replace(/\n/g, '\\n');
    try { return JSON.parse(jsonStr); } catch {}
    const objects: any[] = [];
    const objMatches = jsonStr.match(/\{[^{}]*\}/g);
    if (objMatches) {
      for (const objStr of objMatches) {
        try {
          objects.push(JSON.parse(objStr.replace(/\u2019/g, "'").replace(/\u201c/g, '"').replace(/\u201d/g, '"').replace(/,\s*}/g, '}')));
        } catch {}
      }
      if (objects.length > 0) return objects;
    }
  }
  throw new Error('Could not parse AI response as JSON');
}

export async function POST(req: NextRequest) {
  try {
    const { testType, section, batchSize, batchIndex, setId } = await req.json();

    if (!testType || !section) {
      return NextResponse.json({ error: 'testType and section are required' }, { status: 400 });
    }

    const format = EXAM_FORMATS[testType as keyof typeof EXAM_FORMATS]?.[section as keyof typeof EXAM_FORMATS['TEF']];
    if (!format) {
      return NextResponse.json({ error: `Invalid: ${testType}/${section}` }, { status: 400 });
    }

    const size = batchSize || 15;
    const idx = batchIndex || 0;
    const prompt = getPromptForSection(testType, section, size, idx);
    let questions: GeneratedQuestion[] = [];
    let lastError = '';

    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const completion = await chatCompletion({
          model: AI_MODEL,
          messages: [
            {
              role: 'system',
              content: 'You are an expert French language exam creator. Return ONLY a valid JSON array. No markdown, no text before or after. Use straight apostrophes only.',
            },
            { role: 'user', content: prompt },
          ],
          temperature: 0.8 + attempt * 0.05,
          top_p: 1,
          max_tokens: 4000,
        });

        const content = completion.choices[0]?.message?.content?.trim();
        if (!content) throw new Error('Empty response');

        questions = extractJsonArray(content);
        if (questions.length > 0) break;
      } catch (err) {
        lastError = err instanceof Error ? err.message : String(err);
        console.error(`Attempt ${attempt + 1} failed:`, lastError);
      }
    }

    if (questions.length === 0) {
      return NextResponse.json({ error: `Failed after 3 attempts: ${lastError}` }, { status: 500 });
    }

    const questionsWithIds = questions.map((q, i) => ({
      ...q,
      id: `${testType.toLowerCase()}-${section}-${setId || 'gen'}-${idx * size + i + 1}`,
      type: 'multiple_choice' as const,
    }));

    return NextResponse.json({
      questions: questionsWithIds,
      testType, section,
      setId: setId || 'gen',
      batchIndex: idx, batchSize: size,
    });
  } catch (error) {
    console.error('Question generation error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: `Generation failed: ${message}` }, { status: 500 });
  }
}
