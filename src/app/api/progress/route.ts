// Progress API — uses Supabase instead of Prisma
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/config';
import { getDB } from '@/lib/db';

export const runtime = 'nodejs';

async function getUserId(): Promise<string | null> {
  const session = await getServerSession(authOptions);
  if (!session?.user) return null;
  return (session.user as { id?: string }).id ?? null;
}

export async function GET() {
  try {
    const userId = await getUserId();
    if (!userId) return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });

    const supabase = getDB();

    const { data: lessons } = await supabase
      .from('lesson_progress')
      .select('*')
      .eq('user_id', userId);

    const { data: tests } = await supabase
      .from('test_results')
      .select('*')
      .eq('user_id', userId)
      .order('taken_at', { ascending: false })
      .limit(100);

    const { data: user } = await supabase
      .from('users')
      .select('id, email, name')
      .eq('id', userId)
      .maybeSingle();

    return NextResponse.json({ user, lessons: lessons || [], tests: tests || [] });
  } catch (error) {
    console.error('Error fetching progress:', error);
    return NextResponse.json({ user: null, lessons: [], tests: [] });
  }
}

export async function POST(req: NextRequest) {
  try {
    const userId = await getUserId();
    if (!userId) return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });

    const body = await req.json();
    const { type, data } = body;
    const supabase = getDB();

    if (type === 'lesson-complete') {
      const { courseLevel, unitId, lessonId, score } = data;

      // Check if exists
      const { data: existing } = await supabase
        .from('lesson_progress')
        .select('*')
        .eq('user_id', userId)
        .eq('course_level', courseLevel)
        .eq('unit_id', unitId)
        .eq('lesson_id', lessonId)
        .maybeSingle();

      if (existing) {
        const { data: updated } = await supabase
          .from('lesson_progress')
          .update({
            status: 'completed',
            score: Math.max(existing.score, score),
            attempts: existing.attempts + 1,
            completed_at: new Date().toISOString(),
            last_opened_at: new Date().toISOString(),
          })
          .eq('id', existing.id)
          .select()
          .single();
        return NextResponse.json(updated);
      } else {
        const { data: created } = await supabase
          .from('lesson_progress')
          .insert({
            user_id: userId,
            course_level: courseLevel,
            unit_id: unitId,
            lesson_id: lessonId,
            status: 'completed',
            score,
            attempts: 1,
            completed_at: new Date().toISOString(),
          })
          .select()
          .single();
        return NextResponse.json(created);
      }
    }

    if (type === 'lesson-open') {
      const { courseLevel, unitId, lessonId } = data;
      const { data: existing } = await supabase
        .from('lesson_progress')
        .select('*')
        .eq('user_id', userId)
        .eq('course_level', courseLevel)
        .eq('unit_id', unitId)
        .eq('lesson_id', lessonId)
        .maybeSingle();

      if (existing) {
        const { data: updated } = await supabase
          .from('lesson_progress')
          .update({
            last_opened_at: new Date().toISOString(),
            status: existing.status === 'not_started' ? 'in_progress' : existing.status,
          })
          .eq('id', existing.id)
          .select()
          .single();
        return NextResponse.json(updated);
      } else {
        const { data: created } = await supabase
          .from('lesson_progress')
          .insert({
            user_id: userId,
            course_level: courseLevel,
            unit_id: unitId,
            lesson_id: lessonId,
            status: 'in_progress',
          })
          .select()
          .single();
        return NextResponse.json(created);
      }
    }

    if (type === 'test-result') {
      const { data: created } = await supabase
        .from('test_results')
        .insert({
          user_id: userId,
          test_type: data.testType,
          section: data.section,
          score: data.score,
          total_questions: data.totalQuestions,
          correct_count: data.correctCount,
          duration_sec: data.durationSec,
          details: data.details || null,
        })
        .select()
        .single();
      return NextResponse.json(created);
    }

    return NextResponse.json({ error: 'Unknown type' }, { status: 400 });
  } catch (error) {
    console.error('Error saving progress:', error);
    return NextResponse.json({ error: 'Failed to save progress' }, { status: 500 });
  }
}
