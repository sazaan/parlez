// High-quality French Text-to-Speech API
// Uses Google Translate TTS (free, natural French voice, no API key needed)
// Splits long text into chunks (Google TTS has a ~200 char limit per request)
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 30;

const MAX_CHUNK_LENGTH = 190; // Google TTS limit is ~200 chars, stay safely under

function splitTextIntoChunks(text: string): string[] {
  if (text.length <= MAX_CHUNK_LENGTH) {
    return [text];
  }

  const chunks: string[] = [];
  let remaining = text;

  while (remaining.length > MAX_CHUNK_LENGTH) {
    // Try to split at a sentence boundary (. ! ? ;)
    let splitAt = remaining.lastIndexOf('.', MAX_CHUNK_LENGTH);
    if (splitAt < MAX_CHUNK_LENGTH * 0.5) {
      splitAt = remaining.lastIndexOf('!', MAX_CHUNK_LENGTH);
    }
    if (splitAt < MAX_CHUNK_LENGTH * 0.5) {
      splitAt = remaining.lastIndexOf('?', MAX_CHUNK_LENGTH);
    }
    if (splitAt < MAX_CHUNK_LENGTH * 0.5) {
      splitAt = remaining.lastIndexOf(';', MAX_CHUNK_LENGTH);
    }
    // If no sentence boundary, split at a comma
    if (splitAt < MAX_CHUNK_LENGTH * 0.5) {
      splitAt = remaining.lastIndexOf(',', MAX_CHUNK_LENGTH);
    }
    // If no comma, split at a space
    if (splitAt < MAX_CHUNK_LENGTH * 0.5) {
      splitAt = remaining.lastIndexOf(' ', MAX_CHUNK_LENGTH);
    }
    // If no space, just hard-cut
    if (splitAt < MAX_CHUNK_LENGTH * 0.3) {
      splitAt = MAX_CHUNK_LENGTH;
    }

    chunks.push(remaining.substring(0, splitAt + 1).trim());
    remaining = remaining.substring(splitAt + 1).trim();
  }

  if (remaining.length > 0) {
    chunks.push(remaining);
  }

  return chunks;
}

async function fetchTTSAudio(text: string): Promise<Buffer> {
  const encodedText = encodeURIComponent(text);
  const url = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encodedText}&tl=fr&client=tw-ob&ttsspeed=1.0`;

  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Referer': 'https://translate.google.com/',
    },
  });

  if (!response.ok) {
    throw new Error(`Google TTS returned ${response.status}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  return Buffer.from(new Uint8Array(arrayBuffer));
}

export async function POST(req: NextRequest) {
  try {
    const { text, slow } = await req.json();

    if (!text || typeof text !== 'string') {
      return NextResponse.json({ error: 'Text is required' }, { status: 400 });
    }

    // No more 300 char limit — we split into chunks now
    // Split text into chunks that Google TTS can handle
    const chunks = splitTextIntoChunks(text);

    if (chunks.length === 1) {
      // Single chunk — return directly
      const buffer = await fetchTTSAudio(chunks[0]);
      return new NextResponse(buffer, {
        status: 200,
        headers: {
          'Content-Type': 'audio/mpeg',
          'Content-Length': buffer.length.toString(),
          'Cache-Control': 'public, max-age=86400',
        },
      });
    }

    // Multiple chunks — fetch each and concatenate
    // MP3 files can be concatenated directly
    const buffers: Buffer[] = [];
    for (const chunk of chunks) {
      try {
        const buf = await fetchTTSAudio(chunk);
        buffers.push(buf);
      } catch (err) {
        console.error('TTS chunk failed:', err);
        // Continue with other chunks even if one fails
      }
    }

    if (buffers.length === 0) {
      throw new Error('All TTS chunks failed');
    }

    const combined = Buffer.concat(buffers);

    return new NextResponse(combined, {
      status: 200,
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': combined.length.toString(),
        'Cache-Control': 'public, max-age=86400',
      },
    });
  } catch (error) {
    console.error('TTS API error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: `TTS failed: ${message}` }, { status: 500 });
  }
}
