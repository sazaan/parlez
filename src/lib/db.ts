// Supabase client — replaces Prisma
// Uses HTTPS API (no direct PostgreSQL connection = no IPv6 issues on Vercel)
import { createClient, SupabaseClient } from '@supabase/supabase-js';

let client: SupabaseClient | null = null;

export function getDB(): SupabaseClient {
  if (client) return client;

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      'Missing Supabase env vars. Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY'
    );
  }

  client = createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });

  return client;
}

// For backward compatibility — code that imports { db } still works
export const db = {
  // Users
  user: {
    async findUnique({ where }: { where: { email?: string; id?: string } }) {
      const supabase = getDB();
      if (where.email) {
        const { data } = await supabase.from('users').select('*').eq('email', where.email).maybeSingle();
        return data;
      }
      if (where.id) {
        const { data } = await supabase.from('users').select('*').eq('id', where.id).maybeSingle();
        return data;
      }
      return null;
    },
    async create({ data }: { data: { email: string; passwordHash: string; name?: string | null } }) {
      const supabase = getDB();
      const { data: result } = await supabase.from('users').insert({
        email: data.email,
        password_hash: data.passwordHash,
        name: data.name || null,
      }).select().single();
      return result;
    },
  },
  // Lesson Progress
  lessonProgress: {
    async findUnique({ where }: { where: { userId_courseLevel_unitId_lessonId: { userId: string; courseLevel: string; unitId: string; lessonId: string } } }) {
      const supabase = getDB();
      const w = where.userId_courseLevel_unitId_lessonId;
      const { data } = await supabase.from('lesson_progress')
        .select('*')
        .eq('user_id', w.userId)
        .eq('course_level', w.courseLevel)
        .eq('unit_id', w.unitId)
        .eq('lesson_id', w.lessonId)
        .maybeSingle();
      // Convert snake_case to camelCase for compatibility
      return data ? camelCaseLesson(data) : null;
    },
    async update({ where, data }: { where: { id: string }; data: Record<string, unknown> }) {
      const supabase = getDB();
      const updateData: Record<string, unknown> = {};
      if (data.status !== undefined) updateData.status = data.status;
      if (data.score !== undefined) updateData.score = data.score;
      if (data.attempts !== undefined) updateData.attempts = data.attempts;
      if (data.completedAt !== undefined) updateData.completed_at = data.completedAt;
      if (data.lastOpenedAt !== undefined) updateData.last_opened_at = data.lastOpenedAt;
      const { data: result } = await supabase.from('lesson_progress').update(updateData).eq('id', where.id).select().single();
      return result ? camelCaseLesson(result) : null;
    },
    async create({ data }: { data: Record<string, unknown> }) {
      const supabase = getDB();
      const insertData = {
        user_id: data.userId,
        course_level: data.courseLevel,
        unit_id: data.unitId,
        lesson_id: data.lessonId,
        status: data.status || 'in_progress',
        score: data.score || 0,
        attempts: data.attempts || 1,
      };
      const { data: result } = await supabase.from('lesson_progress').insert(insertData).select().single();
      return result ? camelCaseLesson(result) : null;
    },
  },
  // Test Results
  testResult: {
    async create({ data }: { data: Record<string, unknown> }) {
      const supabase = getDB();
      const insertData = {
        user_id: data.userId,
        test_type: data.testType,
        section: data.section,
        score: data.score,
        total_questions: data.totalQuestions,
        correct_count: data.correctCount,
        duration_sec: data.durationSec,
        details: data.details || null,
      };
      const { data: result } = await supabase.from('test_results').insert(insertData).select().single();
      return result;
    },
  },
};

// Helper to convert snake_case DB rows to camelCase objects (for backward compatibility)
function camelCaseLesson(row: Record<string, unknown>) {
  return {
    id: row.id,
    userId: row.user_id,
    courseLevel: row.course_level,
    unitId: row.unit_id,
    lessonId: row.lesson_id,
    status: row.status,
    score: row.score,
    attempts: row.attempts,
    lastOpenedAt: row.last_opened_at,
    completedAt: row.completed_at,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}
