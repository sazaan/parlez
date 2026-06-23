// Serve pre-built questions from the JSON bank
// On Vercel, the JSON is imported directly (bundled at build time)
// On local dev, it's read from the filesystem
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

// Import the bank at build time (works on both Vercel and local)
import bank from '@/lib/mock-tests/prebuilt-bank.json';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const testType = searchParams.get('testType') as 'TEF' | 'TCF';
    const section = searchParams.get('section');
    const setId = searchParams.get('setId');

    if (!testType || !section || !setId) {
      return NextResponse.json({ error: 'testType, section, and setId are required' }, { status: 400 });
    }

    const key = `${section}-${setId}`;
    const questions = (bank as Record<string, Record<string, unknown[]>>)[testType]?.[key];

    if (!questions || questions.length === 0) {
      return NextResponse.json({
        error: `No pre-built questions for ${testType} ${section} ${setId}. Try Set 6 (AI-generated).`,
      }, { status: 404 });
    }

    return NextResponse.json({ questions });
  } catch (error) {
    console.error('Prebuilt questions error:', error);
    return NextResponse.json({ error: 'Failed to load questions' }, { status: 500 });
  }
}
