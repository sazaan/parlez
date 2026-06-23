// NextAuth configuration with credentials (email/password) provider
// Configured for use behind a reverse proxy (Caddy → localhost:3000)
import type { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import bcrypt from 'bcryptjs';
import { db } from '@/lib/db';

// CRITICAL for reverse proxy setups:
// NextAuth v4's detect-origin.ts checks `process.env.VERCEL ?? process.env.AUTH_TRUST_HOST`
// to decide whether to trust X-Forwarded-Host / X-Forwarded-Proto headers. If neither
// is set, it falls back to "http://localhost:3000" as the origin, which causes the
// session cookie to be set with the wrong callback URL — and the browser then can't
// establish a session through the public HTTPS preview URL.
//
// Setting it here in code (in addition to .env) guarantees it's always set, even if
// the dev server was started before .env was updated (Next.js dev doesn't reload .env).
if (!process.env.AUTH_TRUST_HOST) {
  process.env.AUTH_TRUST_HOST = 'true';
}

export const authOptions: NextAuthOptions = {
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email', placeholder: 'you@example.com' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Email and password are required');
        }
        const email = credentials.email.toLowerCase().trim();
        const user = await db.user.findUnique({ where: { email } });
        if (!user || !user.passwordHash) {
          throw new Error('No account found with that email. Please sign up first.');
        }
        const valid = await bcrypt.compare(credentials.password, user.passwordHash);
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
