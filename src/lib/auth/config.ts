// NextAuth configuration — uses Supabase (via db.ts) instead of Prisma
import type { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import bcrypt from 'bcryptjs';
import { getDB } from '@/lib/db';

export const authOptions: NextAuthOptions = {
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60,
  },
  trustHost: true,
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Email and password are required');
        }
        const email = credentials.email.toLowerCase().trim();
        const supabase = getDB();
        const { data: user, error } = await supabase
          .from('users')
          .select('*')
          .eq('email', email)
          .maybeSingle();

        if (error) throw new Error('Database error');
        if (!user || !user.password_hash) {
          throw new Error('No account found with that email. Please sign up first.');
        }
        const valid = await bcrypt.compare(credentials.password, user.password_hash);
        if (!valid) {
          throw new Error('Incorrect password. Please try again.');
        }
        return {
          id: user.id,
          email: user.email,
          name: user.name ?? undefined,
          image: user.image ?? undefined,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user && token.id) {
        (session.user as { id?: string }).id = token.id as string;
      }
      return session;
    },
  },
  pages: {
    signIn: '/auth/login',
    newUser: '/auth/signup',
  },
  secret: process.env.NEXTAUTH_SECRET || 'parlez-dev-secret-change-in-production-2024',
};
