// /api/me — returns current user info using Supabase
import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/config';
import { getDB } from '@/lib/db';

export const runtime = 'nodejs';

export async function GET() {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) return NextResponse.json({ user: null });

    const userId = (session.user as { id?: string }).id;
    if (!userId) return NextResponse.json({ user: null });

    const supabase = getDB();
    const { data: user } = await supabase
      .from('users')
      .select('id, email, name, created_at')
      .eq('id', userId)
      .maybeSingle();

    if (!user) return NextResponse.json({ user: null });

    const { count: lessonCount } = await supabase
      .from('lesson_progress')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId)
      .eq('status', 'completed');

    const { count: testCount } = await supabase
      .from('test_results')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId);

    return NextResponse.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        createdAt: user.created_at,
      },
      stats: {
        lessonsCompleted: lessonCount || 0,
        testsTaken: testCount || 0,
      },
    });
  } catch (error) {
    console.error('Error in /api/me:', error);
    return NextResponse.json({ user: null, error: 'Failed to load user' }, { status: 500 });
  }
}
