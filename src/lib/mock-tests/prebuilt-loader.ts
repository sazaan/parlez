// Load pre-built questions from the JSON bank
import fs from 'fs';
import path from 'path';

interface PrebuiltQuestion {
  id: string;
  type: 'multiple_choice';
  prompt: string;
  options: string[];
  answer: number;
  explanation: string;
  audioText?: string;
  level: string;
}

interface PrebuiltBank {
  TEF: Record<string, PrebuiltQuestion[]>;
  TCF: Record<string, PrebuiltQuestion[]>;
}

let cachedBank: PrebuiltBank | null = null;

export function getPrebuiltBank(): PrebuiltBank | null {
  if (cachedBank) return cachedBank;
  try {
    const bankPath = path.join(process.cwd(), 'src/lib/mock-tests/prebuilt-bank.json');
    const data = fs.readFileSync(bankPath, 'utf-8');
    cachedBank = JSON.parse(data);
    return cachedBank;
  } catch {
    return null;
  }
}

export function getPrebuiltQuestions(testType: 'TEF' | 'TCF', section: string, setId: string): PrebuiltQuestion[] | null {
  const bank = getPrebuiltBank();
  if (!bank) return null;
  const key = `${section}-${setId}`;
  return bank[testType]?.[key] || null;
}
