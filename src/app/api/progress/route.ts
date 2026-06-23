// Progress tracking API - syncs to Prisma, scoped to the authenticated user
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/config';
import { db } from '@/lib/db';

export const runtime = 'nodejs';

async function getUserId(): Promise<string | null> {
  const session = await getServerSession(authOptions);
  if (!session?.user) return null;
  return (session.user as { id?: string }).id ?? null;
}

export async function GET() {
  try {
    const userId = await getUserId();
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
    }
    const lessons = await db.lessonProgress.findMany({ where: { userId } });
    const tests = await db.testResult.findMany({
      where: { userId },
      orderBy: { takenAt: 'desc' },
      take: 100,
    });
    const user = await db.user.findUnique({ where: { id: userId } });

    return NextResponse.json({
      user: user ? { id: user.id, email: user.email, name: user.name } : null,
      lessons,
      tests,
    });
  } catch (error) {
    console.error('Error fetching progress:', error);
    return NextResponse.json({ user: null, lessons: [], tests: [] });
  }
}

export async function POST(req: NextRequest) {
  try {
    const userId = await getUserId();
    if (!userId) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
    }
    const body = await req.json();
    const { type, data } = body;

    if (type === 'lesson-complete') {
      const { courseLevel, unitId, lessonId, score } = data;
      const existing = await db.lessonProgress.findUnique({
        where: {
          userId_courseLevel_unitId_lessonId: {
            userId,
            courseLevel,
            unitId,
            lessonId,
          },
        },
      });

      if (existing) {
        const updated = await db.lessonProgress.update({
          where: { id: existing.id },
          data: {
            status: 'completed',
            score: Math.max(existing.score, score),
            attempts: existing.attempts + 1,
            completedAt: new Date(),
            lastOpenedAt: new Date(),
          },
        });
        return NextResponse.json(updated);
      } else {
        const created = await db.lessonProgress.create({
          data: {
            userId,
            courseLevel,
            unitId,
            lessonId,
            status: 'completed',
            score,
            attempts: 1,
            completedAt: new Date(),
          },
        });
        return NextResponse.json(created);
      }
    }

    if (type === 'lesson-open') {
      const { courseLevel, unitId, lessonId } = data;
      const existing = await db.lessonProgress.findUnique({
        where: {
          userId_courseLevel_unitId_lessonId: {
            userId, courseLevel, unitId, lessonId,
          },
        },
      });
      if (existing) {
        const updated = await db.lessonProgress.update({
          where: { id: existing.id },
          data: { lastOpenedAt: new Date(), status: existing.status === 'not_started' ? 'in_progress' : existing.status },
        });
        return NextResponse.json(updated);
      }
      const created = await db.lessonProgress.create({
        data: { userId, courseLevel, unitId, lessonId, status: 'in_progress' },
      });
      return NextResponse.json(created);
    }

    if (type === 'test-result') {
      const created = await db.testResult.create({
        data: {
          userId,
          testType: data.testType,
          section: data.section,
          score: data.score,
          totalQuestions: data.totalQuestions,
          correctCount: data.correctCount,
          durationSec: data.durationSec,
          details: data.details || null,
        },
      });
      return NextResponse.json(created);
    }

    return NextResponse.json({ error: 'Unknown type' }, { status: 400 });
  } catch (error) {
    console.error('Error saving progress:', error);
    return NextResponse.json({ error: 'Failed to save progress' }, { status: 500 });
  }
}
