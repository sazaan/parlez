// Translation API: English <-> French
// Uses OpenAI SDK with NVIDIA NIM endpoint (Z.AI GLM model)
import { NextRequest, NextResponse } from 'next/server';
import { chatCompletion, AI_MODEL } from '@/lib/ai-client';

export const runtime = 'nodejs';
export const maxDuration = 15;

export async function POST(req: NextRequest) {
  try {
    const { text, direction } = await req.json();

    if (!text || typeof text !== 'string') {
      return NextResponse.json({ error: 'Text is required' }, { status: 400 });
    }

    if (text.length > 500) {
      return NextResponse.json({ error: 'Text too long (max 500 characters)' }, { status: 400 });
    }

    const isFrToEn = direction === 'fr-to-en';
    const systemPrompt = isFrToEn
      ? 'You are a professional French-to-English translator. Translate the French text to natural, correct English. Return ONLY the translation — no explanations, no notes, no quotes.'
      : 'You are a professional English-to-French translator. Translate the English text to natural, correct French. Return ONLY the translation — no explanations, no notes, no quotes.';

    const userPrompt = isFrToEn
      ? `Translate this French text to English:\n\n${text}`
      : `Translate this English text to French:\n\n${text}`;

    const completion = await chatCompletion({
      model: AI_MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0.3,
      top_p: 1,
      max_tokens: 200,
    });

    const translation = completion.choices[0]?.message?.content?.trim();

    if (!translation) {
      return NextResponse.json({ error: 'No translation returned' }, { status: 500 });
    }

    const cleaned = translation.replace(/^["'\u00ab\u00bb]+|["'\u00ab\u00bb]+$/g, '').trim();

    return NextResponse.json({
      translation: cleaned,
      original: text,
      direction: direction || 'en-to-fr',
    });
  } catch (error) {
    console.error('Translation API error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: `Translation failed: ${message}` }, { status: 500 });
  }
}
