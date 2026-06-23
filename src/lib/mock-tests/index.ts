import type { MockTest } from './types';
import { tefTest } from './tef';
import { tcfTest } from './tcf';

export const mockTests: MockTest[] = [tefTest, tcfTest];

export function getTest(type: 'TEF' | 'TCF'): MockTest {
  return mockTests.find((t) => t.type === type) ?? tefTest;
}
