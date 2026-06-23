// Reusable auth helpers for server-side use
import { getServerSession } from 'next-auth/next';
import { authOptions } from './config';
import { db } from '@/lib/db';

export async function getCurrentUser() {
  const session = await getServerSession(authOptions);
  if (!session?.user) return null;
  const userId = (session.user as { id?: string }).id;
  if (!userId) return null;
  const user = await db.user.findUnique({ where: { id: userId } });
  return user;
}

export async function requireUserId(): Promise<string | null> {
  const session = await getServerSession(authOptions);
  if (!session?.user) return null;
  return (session.user as { id?: string }).id ?? null;
}
