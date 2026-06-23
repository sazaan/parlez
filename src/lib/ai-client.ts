// Shared AI client — uses fetch with OpenAI-compatible API format
// Works with:
// 1. NVIDIA NIM endpoint (https://integrate.api.nvidia.com/v1) — set NVIDIA_API_KEY env var
// 2. Z.AI internal API — falls back to /etc/.z-ai-config with custom headers (sandbox only)
// 3. Any OpenAI-compatible endpoint — set NVIDIA_BASE_URL and NVIDIA_API_KEY

interface ChatCompletionMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatCompletionParams {
  model?: string;
  messages: ChatCompletionMessage[];
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  stream?: boolean;
}

interface ChatCompletionResponse {
  choices: Array<{
    message: { role: string; content: string };
    finish_reason?: string;
  }>;
}

interface AIConfig {
  baseUrl: string;
  apiKey: string;
  chatId?: string;
  userId?: string;
  token?: string;
  isInternal: boolean;
}

// Config priority: NVIDIA env vars > ZAI env vars > /etc/.z-ai-config file
async function loadConfig(): Promise<AIConfig> {
  // 1. NVIDIA NIM (production on Vercel)
  const nvidiaKey = process.env.NVIDIA_API_KEY;
  if (nvidiaKey && nvidiaKey !== 'nvapi-your-key-here' && nvidiaKey.length > 10) {
    return {
      baseUrl: process.env.NVIDIA_BASE_URL || 'https://integrate.api.nvidia.com/v1',
      apiKey: nvidiaKey,
      isInternal: false,
    };
  }

  // 2. ZAI env vars (alternative deployment)
  if (process.env.ZAI_API_KEY) {
    return {
      baseUrl: process.env.ZAI_BASE_URL || 'https://internal-api.z.ai/v1',
      apiKey: process.env.ZAI_API_KEY,
      chatId: process.env.ZAI_CHAT_ID,
      userId: process.env.ZAI_USER_ID,
      token: process.env.ZAI_TOKEN,
      isInternal: (process.env.ZAI_BASE_URL || 'https://internal-api.z.ai/v1').includes('internal-api.z.ai'),
    };
  }

  // 3. Fall back to /etc/.z-ai-config (sandbox environment only)
  try {
    const fs = await import('fs');
    const configPath = '/etc/.z-ai-config';
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      return {
        baseUrl: config.baseUrl || 'https://internal-api.z.ai/v1',
        apiKey: config.apiKey,
        chatId: config.chatId,
        userId: config.userId,
        token: config.token,
        isInternal: (config.baseUrl || '').includes('internal-api.z.ai'),
      };
    }
  } catch {}

  throw new Error(
    'No AI API key found. Set NVIDIA_API_KEY env var (get one at https://build.nvidia.com, model: z-ai/glm-5.1).'
  );
}

let cachedConfig: AIConfig | null = null;

async function getConfig(): Promise<AIConfig> {
  if (cachedConfig) return cachedConfig;
  cachedConfig = await loadConfig();
  return cachedConfig;
}

// Model: user can override with AI_MODEL env var
// Default: z-ai/glm-5.1 for NVIDIA NIM, glm-4-flash for ZAI internal
export const AI_MODEL = process.env.AI_MODEL || 'z-ai/glm-5.1';

/**
 * Create a chat completion using the OpenAI-compatible API format.
 * Automatically handles:
 * - NVIDIA NIM: standard OpenAI format, no extra headers
 * - Z.AI internal: adds X-Z-AI-From, X-Chat-Id, X-User-Id, X-Token headers + thinking param
 */
export async function chatCompletion(params: ChatCompletionParams): Promise<ChatCompletionResponse> {
  const config = await getConfig();
  const model = params.model || AI_MODEL;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${config.apiKey}`,
  };

  // Add ZAI-specific headers when using the internal API
  if (config.isInternal) {
    headers['X-Z-AI-From'] = 'Z';
    if (config.chatId) headers['X-Chat-Id'] = config.chatId;
    if (config.userId) headers['X-User-Id'] = config.userId;
    if (config.token) headers['X-Token'] = config.token;
  }

  const body: Record<string, unknown> = {
    model,
    messages: params.messages,
    temperature: params.temperature ?? 0.7,
    top_p: params.top_p ?? 1,
    max_tokens: params.max_tokens ?? 4096,
    stream: false,
  };

  // ZAI internal API needs thinking parameter
  if (config.isInternal) {
    body.thinking = { type: 'disabled' };
  }

  const url = `${config.baseUrl}/chat/completions`;

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`AI API error ${response.status}: ${errorText.substring(0, 300)}`);
  }

  return await response.json();
}
