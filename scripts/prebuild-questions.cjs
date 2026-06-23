// Pre-generate all TEF and TCF questions and save to a JSON file
// This creates 5 sets of pre-built questions so they don't need to be generated at runtime

const fs = require('fs');

const EXAM_SECTIONS = {
  TEF: [
    { id: 'reading', count: 50 },
    { id: 'listening', count: 60 },
    { id: 'vocabulary_grammar', count: 40 },
  ],
  TCF: [
    { id: 'listening', count: 29 },
    { id: 'language_structures', count: 18 },
    { id: 'reading', count: 29 },
  ],
};

const SETS = 5;
const BATCH_SIZE = 15;

async function generateBatch(testType, section, batchSize, batchIndex, setId) {
  const res = await fetch('http://localhost:3000/api/generate-test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ testType, section, batchSize, batchIndex, setId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(`API error: ${err.error || res.status}`);
  }
  const data = await res.json();
  return data.questions;
}

async function main() {
  const bank = { TEF: {}, TCF: {} };

  for (const testType of ['TEF', 'TCF']) {
    const sections = EXAM_SECTIONS[testType];
    for (let setNum = 1; setNum <= SETS; setNum++) {
      const setId = `set${setNum}`;
      console.log(`\n=== ${testType} Set ${setNum} ===`);

      for (const section of sections) {
        console.log(`  ${section.id}: ${section.count} questions...`);
        const allQuestions = [];
        const numBatches = Math.ceil(section.count / BATCH_SIZE);

        for (let batch = 0; batch < numBatches; batch++) {
          const currentBatchSize = Math.min(BATCH_SIZE, section.count - batch * BATCH_SIZE);
          process.stdout.write(`    Batch ${batch + 1}/${numBatches}...`);
          try {
            const questions = await generateBatch(testType, section.id, currentBatchSize, batch, setId);
            allQuestions.push(...questions);
            process.stdout.write(` ${questions.length} questions\n`);
          } catch (err) {
            console.error(`\n    FAILED: ${err.message}`);
            // Continue with what we have
          }
        }

        const key = `${section.id}-${setId}`;
        bank[testType][key] = allQuestions;
        console.log(`  ${section.id}: ${allQuestions.length}/${section.count} questions total`);
      }
    }
  }

  // Save to file
  const outputPath = '/home/z/my-project/src/lib/mock-tests/prebuilt-bank.json';
  fs.writeFileSync(outputPath, JSON.stringify(bank, null, 2));
  console.log(`\nSaved to ${outputPath}`);

  // Print summary
  let total = 0;
  for (const testType of ['TEF', 'TCF']) {
    for (const key of Object.keys(bank[testType])) {
      total += bank[testType][key].length;
    }
  }
  console.log(`Total questions: ${total}`);
}

main().catch(console.error);
