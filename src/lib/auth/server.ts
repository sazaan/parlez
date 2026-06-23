// Reusable auth helpers for server-side use
import { getServerSession } from 'next-auth/next';
import { authOptions } from './config';
import { getDB } from '@/lib/db';

export async function getCurrentUser() {
  const session = await getServerSession(authOptions);
  if (!session?.user) return null;
  const userId = (session.user as { id?: string }).id;
  if (!userId) return null;
  const supabase = getDB();
  const { data: user } = await supabase.from('users').select('*').eq('id', userId).maybeSingle();
  return user;
}

export async function requireUserId(): Promise<string | null> {
  const session = await getServerSession(authOptions);
  if (!session?.user) return null;
  return (session.user as { id?: string }).id ?? null;
}
