// Add conjugation data to all course files using proper TypeScript string escaping
const fs = require('fs');

const verbs = {
  'être': {
    translation: 'to be',
    conjugations: [
      { pronoun: 'je', form: 'suis' },
      { pronoun: 'tu', form: 'es' },
      { pronoun: 'il/elle', form: 'est' },
      { pronoun: 'nous', form: 'sommes' },
      { pronoun: 'vous', form: 'êtes' },
      { pronoun: 'ils/elles', form: 'sont' },
    ],
    rule: "Subject + être + adjective/noun/profession. Professions take NO article: Je suis professeur. Used for identity, nationality, location.",
    examples: [
      { fr: "Je suis étudiant.", en: "I am a student." },
      { fr: "Tu es français ?", en: "Are you French?" },
      { fr: "Nous sommes à Paris.", en: "We are in Paris." },
    ],
  },
  'avoir': {
    translation: 'to have',
    conjugations: [
      { pronoun: "j'", form: 'ai' },
      { pronoun: 'tu', form: 'as' },
      { pronoun: 'il/elle', form: 'a' },
      { pronoun: 'nous', form: 'avons' },
      { pronoun: 'vous', form: 'avez' },
      { pronoun: 'ils/elles', form: 'ont' },
    ],
    rule: "Subject + avoir + noun. Used for possession, age (J'ai 20 ans), and expressions like avoir faim/soif/froid. Age uses avoir, NOT être.",
    examples: [
      { fr: "J'ai un frère.", en: "I have a brother." },
      { fr: "Tu as vingt ans.", en: "You are twenty." },
      { fr: "Il a faim.", en: "He is hungry." },
    ],
  },
  'aller': {
    translation: 'to go',
    conjugations: [
      { pronoun: 'je', form: 'vais' },
      { pronoun: 'tu', form: 'vas' },
      { pronoun: 'il/elle', form: 'va' },
      { pronoun: 'nous', form: 'allons' },
      { pronoun: 'vous', form: 'allez' },
      { pronoun: 'ils/elles', form: 'vont' },
    ],
    rule: "Subject + aller + preposition + place. à + le = au, à + les = aux. Also: aller + infinitive = near future (Je vais manger).",
    examples: [
      { fr: "Je vais au cinéma.", en: "I go to the cinema." },
      { fr: "Nous allons à Paris.", en: "We go to Paris." },
      { fr: "Je vais manger.", en: "I am going to eat." },
    ],
  },
  'faire': {
    translation: 'to do/make',
    conjugations: [
      { pronoun: 'je', form: 'fais' },
      { pronoun: 'tu', form: 'fais' },
      { pronoun: 'il/elle', form: 'fait' },
      { pronoun: 'nous', form: 'faisons' },
      { pronoun: 'vous', form: 'faites' },
      { pronoun: 'ils/elles', form: 'font' },
    ],
    rule: "Subject + faire + de + activity (faire du sport, faire de la musique). Expressions: faire la cuisine, faire attention, faire les courses.",
    examples: [
      { fr: "Je fais du sport.", en: "I do sports." },
      { fr: "Elle fait la cuisine.", en: "She cooks." },
      { fr: "Nous faisons les courses.", en: "We shop." },
    ],
  },
  'parler': {
    translation: 'to speak',
    conjugations: [
      { pronoun: 'je', form: 'parle' },
      { pronoun: 'tu', form: 'parles' },
      { pronoun: 'il/elle', form: 'parle' },
      { pronoun: 'nous', form: 'parlons' },
      { pronoun: 'vous', form: 'parlez' },
      { pronoun: 'ils/elles', form: 'parlent' },
    ],
    rule: "Subject + parler + language (no article: Je parle français). Or: parler + à + person. Regular -er verb.",
    examples: [
      { fr: "Je parle français.", en: "I speak French." },
      { fr: "Tu parles à Marie ?", en: "Are you talking to Marie?" },
      { fr: "Nous parlons anglais.", en: "We speak English." },
    ],
  },
  'aimer': {
    translation: 'to like/love',
    conjugations: [
      { pronoun: "j'", form: 'aime' },
      { pronoun: 'tu', form: 'aimes' },
      { pronoun: 'il/elle', form: 'aime' },
      { pronoun: 'nous', form: 'aimons' },
      { pronoun: 'vous', form: 'aimez' },
      { pronoun: 'ils/elles', form: 'aiment' },
    ],
    rule: "Subject + aimer + definite article + noun (J'aime le café). For activities: aimer + infinitive (J'aime lire).",
    examples: [
      { fr: "J'aime le chocolat.", en: "I like chocolate." },
      { fr: "Tu aimes la musique ?", en: "Do you like music?" },
      { fr: "J'aime lire.", en: "I like to read." },
    ],
  },
  'habiter': {
    translation: 'to live',
    conjugations: [
      { pronoun: "j'", form: 'habite' },
      { pronoun: 'tu', form: 'habites' },
      { pronoun: 'il/elle', form: 'habite' },
      { pronoun: 'nous', form: 'habitons' },
      { pronoun: 'vous', form: 'habitez' },
      { pronoun: 'ils/elles', form: 'habitent' },
    ],
    rule: "Subject + habiter + à + city (J'habite à Paris). For countries: en (feminine) or au (masculine). Regular -er verb.",
    examples: [
      { fr: "J'habite à Lyon.", en: "I live in Lyon." },
      { fr: "Il habite en France.", en: "He lives in France." },
      { fr: "Nous habitons au Canada.", en: "We live in Canada." },
    ],
  },
  'manger': {
    translation: 'to eat',
    conjugations: [
      { pronoun: 'je', form: 'mange' },
      { pronoun: 'tu', form: 'manges' },
      { pronoun: 'il/elle', form: 'mange' },
      { pronoun: 'nous', form: 'mangeons' },
      { pronoun: 'vous', form: 'mangez' },
      { pronoun: 'ils/elles', form: 'mangent' },
    ],
    rule: "Subject + manger + food (with partitive: du/de la/des). Nous form = mangeons (extra -e for soft g).",
    examples: [
      { fr: "Je mange une pomme.", en: "I eat an apple." },
      { fr: "Nous mangeons du pain.", en: "We eat bread." },
      { fr: "Tu manges au restaurant ?", en: "Do you eat at the restaurant?" },
    ],
  },
  'travailler': {
    translation: 'to work',
    conjugations: [
      { pronoun: 'je', form: 'travaille' },
      { pronoun: 'tu', form: 'travailles' },
      { pronoun: 'il/elle', form: 'travaille' },
      { pronoun: 'nous', form: 'travaillons' },
      { pronoun: 'vous', form: 'travaillez' },
      { pronoun: 'ils/elles', form: 'travaillent' },
    ],
    rule: "Subject + travailler + à/en + place (Je travaille à Paris). Regular -er verb, double l.",
    examples: [
      { fr: "Je travaille à la maison.", en: "I work at home." },
      { fr: "Tu travailles où ?", en: "Where do you work?" },
      { fr: "Ils travaillent ensemble.", en: "They work together." },
    ],
  },
  'prendre': {
    translation: 'to take',
    conjugations: [
      { pronoun: 'je', form: 'prends' },
      { pronoun: 'tu', form: 'prends' },
      { pronoun: 'il/elle', form: 'prend' },
      { pronoun: 'nous', form: 'prenons' },
      { pronoun: 'vous', form: 'prenez' },
      { pronoun: 'ils/elles', form: 'prennent' },
    ],
    rule: "Subject + prendre + transport (Je prends le métro). Also: prendre un café, prendre le petit-déjeuner. Irregular -re verb.",
    examples: [
      { fr: "Je prends le bus.", en: "I take the bus." },
      { fr: "Tu prends un café ?", en: "Will you have a coffee?" },
      { fr: "Nous prenons le train.", en: "We take the train." },
    ],
  },
  'venir': {
    translation: 'to come',
    conjugations: [
      { pronoun: 'je', form: 'viens' },
      { pronoun: 'tu', form: 'viens' },
      { pronoun: 'il/elle', form: 'vient' },
      { pronoun: 'nous', form: 'venons' },
      { pronoun: 'vous', form: 'venez' },
      { pronoun: 'ils/elles', form: 'viennent' },
    ],
    rule: "Subject + venir + de + place (Je viens de Paris). Venir de + infinitif = just did (passé récent). Irregular -ir verb.",
    examples: [
      { fr: "Je viens de Lyon.", en: "I come from Lyon." },
      { fr: "Elle vient ce soir.", en: "She is coming tonight." },
      { fr: "Je viens de manger.", en: "I just ate." },
    ],
  },
  'vouloir': {
    translation: 'to want',
    conjugations: [
      { pronoun: 'je', form: 'veux' },
      { pronoun: 'tu', form: 'veux' },
      { pronoun: 'il/elle', form: 'veut' },
      { pronoun: 'nous', form: 'voulons' },
      { pronoun: 'vous', form: 'voulez' },
      { pronoun: 'ils/elles', form: 'veulent' },
    ],
    rule: "Subject + vouloir + noun/infinitive. Je voudrais (conditional) = I would like — polite form for ordering. Irregular.",
    examples: [
      { fr: "Je veux un café.", en: "I want a coffee." },
      { fr: "Tu veux venir ?", en: "Do you want to come?" },
      { fr: "Je voudrais un thé.", en: "I would like a tea." },
    ],
  },
  'pouvoir': {
    translation: 'can/be able to',
    conjugations: [
      { pronoun: 'je', form: 'peux' },
      { pronoun: 'tu', form: 'peux' },
      { pronoun: 'il/elle', form: 'peut' },
      { pronoun: 'nous', form: 'pouvons' },
      { pronoun: 'vous', form: 'pouvez' },
      { pronoun: 'ils/elles', form: 'peuvent' },
    ],
    rule: "Subject + pouvoir + infinitive (Je peux parler français). For ability and permission. Irregular.",
    examples: [
      { fr: "Je peux parler français.", en: "I can speak French." },
      { fr: "Tu peux m'aider ?", en: "Can you help me?" },
      { fr: "Nous pouvons partir.", en: "We can leave." },
    ],
  },
  'devoir': {
    translation: 'must/should',
    conjugations: [
      { pronoun: 'je', form: 'dois' },
      { pronoun: 'tu', form: 'dois' },
      { pronoun: 'il/elle', form: 'doit' },
      { pronoun: 'nous', form: 'devons' },
      { pronoun: 'vous', form: 'devez' },
      { pronoun: 'ils/elles', form: 'doivent' },
    ],
    rule: "Subject + devoir + infinitive (Je dois partir = I must leave). For obligation and probability. Irregular.",
    examples: [
      { fr: "Je dois travailler.", en: "I must work." },
      { fr: "Tu dois étudier.", en: "You must study." },
      { fr: "Il doit partir.", en: "He has to leave." },
    ],
  },
  'savoir': {
    translation: 'to know (a fact/how to)',
    conjugations: [
      { pronoun: 'je', form: 'sais' },
      { pronoun: 'tu', form: 'sais' },
      { pronoun: 'il/elle', form: 'sait' },
      { pronoun: 'nous', form: 'savons' },
      { pronoun: 'vous', form: 'savez' },
      { pronoun: 'ils/elles', form: 'savent' },
    ],
    rule: "Subject + savoir + fact/infinitive (Je sais nager = I know how to swim). Different from connaître. Irregular.",
    examples: [
      { fr: "Je sais la réponse.", en: "I know the answer." },
      { fr: "Tu sais nager ?", en: "Do you know how to swim?" },
      { fr: "Nous savons la vérité.", en: "We know the truth." },
    ],
  },
  'finir': {
    translation: 'to finish',
    conjugations: [
      { pronoun: 'je', form: 'finis' },
      { pronoun: 'tu', form: 'finis' },
      { pronoun: 'il/elle', form: 'finit' },
      { pronoun: 'nous', form: 'finissons' },
      { pronoun: 'vous', form: 'finissez' },
      { pronoun: 'ils/elles', form: 'finissent' },
    ],
    rule: "Subject + finir + noun/infinitive (Je finis mon travail). Regular -ir verb: -is, -is, -it, -issons, -issez, -issent.",
    examples: [
      { fr: "Je finis mon devoir.", en: "I finish my homework." },
      { fr: "Tu finis à quelle heure ?", en: "What time do you finish?" },
      { fr: "Nous finissons le projet.", en: "We finish the project." },
    ],
  },
};

function getVerbsForLesson(lessonId, lessonTitle) {
  const id = lessonId.toLowerCase();
  const title = lessonTitle.toLowerCase();
  if (id.includes('u0-l1') || title.includes('greeting') || title.includes('saluer')) return ['être'];
  if (id.includes('u0-l3') || title.includes('number') || title.includes('compter')) return ['avoir'];
  if (id.includes('u1-l1') || title.includes('introduc') || title.includes('présenter')) return ['être', 'avoir'];
  if (id.includes('u1-l2') || title.includes('personal') || title.includes('information')) return ['avoir'];
  if (id.includes('u1-l3') || title.includes('classroom') || title.includes('classe')) return ['être', 'avoir'];
  if (id.includes('u1-l4') || title.includes('question')) return ['être', 'avoir'];
  if (id.includes('u2-l1') || title.includes('family') || title.includes('famille')) return ['avoir'];
  if (id.includes('u2-l2') || title.includes('describ') || title.includes('décrire')) return ['être'];
  if (id.includes('u2-l3') || title.includes('like') || title.includes('goût') || title.includes('aimer')) return ['aimer'];
  if (id.includes('u2-l4') || title.includes('-er') || title.includes('verbe')) return ['parler', 'habiter', 'travailler', 'manger'];
  if (id.includes('u3-l1') || title.includes('time') || title.includes('heure')) return ['être', 'avoir'];
  if (id.includes('u3-l2') || title.includes('aller') || title.includes('future')) return ['aller'];
  if (id.includes('u3-l3') || title.includes('imperat') || title.includes('impératif')) return ['être', 'avoir', 'aller'];
  if (id.includes('u3-l4') || title.includes('outing') || title.includes('sortie')) return ['aller', 'vouloir'];
  if (id.includes('u4-l1') || title.includes('café') || title.includes('commander')) return ['vouloir', 'prendre'];
  if (id.includes('u4-l2') || title.includes('price') || title.includes('prix')) return ['avoir', 'être'];
  if (id.includes('u4-l3') || title.includes('food') || title.includes('nourriture') || title.includes('repas')) return ['manger', 'prendre'];
  if (id.includes('u4-l4') || title.includes('faire') || title.includes('prendre') || title.includes('venir')) return ['faire', 'prendre', 'venir'];
  if (id.includes('u5-l1') || title.includes('city') || title.includes('ville')) return ['aller', 'être'];
  if (id.includes('u5-l2') || title.includes('transport')) return ['prendre', 'aller'];
  if (id.includes('u5-l3') || title.includes('hobb') || title.includes('sport') || title.includes('loisir')) return ['faire', 'aimer'];
  if (id.includes('u5-l4') || title.includes('weather') || title.includes('temps') || title.includes('saison')) return ['être', 'faire'];
  if (id.includes('a2')) return ['avoir', 'être', 'aller'];
  if (id.includes('b1')) return ['être', 'avoir', 'faire', 'aller'];
  if (id.includes('b2')) return ['être', 'avoir', 'faire', 'aller', 'savoir'];
  return ['être', 'avoir'];
}

// Escape a string for use in a single-quoted TS string
function esc(s) {
  return s.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

function makeVerbBlock(verbName, idx) {
  const v = verbs[verbName];
  if (!v) return '';

  let block = '            {\n';
  block += `              infinitive: '${esc(verbName)}',\n`;
  block += `              translation: '${esc(v.translation)}',\n`;
  block += `              tense: 'Présent',\n`;
  block += `              conjugations: [\n`;
  for (const c of v.conjugations) {
    block += `                { pronoun: '${esc(c.pronoun)}', form: '${esc(c.form)}' },\n`;
  }
  block += `              ],\n`;
  block += `              sentenceRule: '${esc(v.rule)}',\n`;
  block += `              sentenceExamples: [\n`;
  for (const ex of v.examples) {
    block += `                { fr: '${esc(ex.fr)}', en: '${esc(ex.en)}' },\n`;
  }
  block += `              ],\n`;
  block += `            }`;
  return block;
}

function makePractice(verbName, lessonId, idx) {
  const v = verbs[verbName];
  if (!v) return [];
  const practices = [];
  const prefix = lessonId + '-conj';

  // Exercise 1: Conjugate for a pronoun
  const c1 = v.conjugations[idx % v.conjugations.length];
  practices.push({
    id: `${prefix}-${idx}-1`,
    type: 'conjugation',
    prompt: `Conjugate "${verbName}" for "${c1.pronoun}":`,
    promptFr: c1.pronoun + ' _____',
    answer: c1.form,
    acceptable: [c1.form],
    explanation: `${c1.pronoun} ${c1.form} — correct form of "${verbName}".`,
  });

  // Exercise 2: Multiple choice
  const c2 = v.conjugations[(idx + 2) % v.conjugations.length];
  const wrong = v.conjugations.filter((_, i) => i !== (idx + 2) % v.conjugations.length).slice(0, 3).map(c => c.form);
  const options = [c2.form, ...wrong];
  practices.push({
    id: `${prefix}-${idx}-2`,
    type: 'multiple_choice',
    prompt: `Complete: "${c2.pronoun} _____" with the correct form of "${verbName}".`,
    options,
    answer: 0,
    explanation: `${c2.pronoun} ${c2.form} — correct conjugation of "${verbName}".`,
  });

  // Exercise 3: Fill in the blank
  const ex = v.examples[idx % v.examples.length];
  const verbForm = v.conjugations.map(c => c.form).find(form => ex.fr.includes(form));
  if (verbForm) {
    const blanked = ex.fr.replace(verbForm, '_____');
    practices.push({
      id: `${prefix}-${idx}-3`,
      type: 'fill_blank',
      prompt: `Fill in the blank: "${blanked}" (${ex.en}) — form of "${verbName}"`,
      answer: verbForm,
      acceptable: [verbForm],
      explanation: `The correct form is "${verbForm}".`,
    });
  }

  return practices;
}

function makePracticeBlock(practices) {
  let block = '[';
  for (const p of practices) {
    block += '\n              {\n';
    block += `                id: '${esc(p.id)}',\n`;
    block += `                type: '${esc(p.type)}',\n`;
    block += `                prompt: '${esc(p.prompt)}',\n`;
    if (p.promptFr) block += `                promptFr: '${esc(p.promptFr)}',\n`;
    if (p.options) {
      block += `                options: [${p.options.map(o => `'${esc(o)}'`).join(', ')}],\n`;
      block += `                answer: ${p.answer},\n`;
    } else {
      block += `                answer: '${esc(p.answer)}',\n`;
      if (p.acceptable) block += `                acceptable: [${p.acceptable.map(a => `'${esc(a)}'`).join(', ')}],\n`;
    }
    if (p.explanation) block += `                explanation: '${esc(p.explanation)}',\n`;
    block += '              },';
  }
  block += '\n            ]';
  return block;
}

const courseFiles = [
  '/home/z/my-project/src/lib/courses/a1.ts',
  '/home/z/my-project/src/lib/courses/a2.ts',
  '/home/z/my-project/src/lib/courses/b1.ts',
  '/home/z/my-project/src/lib/courses/b2.ts',
];

for (const filePath of courseFiles) {
  let content = fs.readFileSync(filePath, 'utf-8');
  if (content.includes('conjugation:')) {
    console.log('Skipping ' + filePath + ' — already has conjugation');
    continue;
  }

  const lessonIdPattern = /id: '((?:a1|a2|b1|b2)-u[0-9]+-l[0-9]+)',/g;
  let match;
  let lessonCount = 0;
  const insertions = [];

  while ((match = lessonIdPattern.exec(content)) !== null) {
    const lessonId = match[1];
    const titleMatch = content.substring(match.index, match.index + 500).match(/title:\s*'([^']+)'/);
    const lessonTitle = titleMatch ? titleMatch[1] : '';
    const selectedVerbs = getVerbsForLesson(lessonId, lessonTitle);

    const verbBlocks = selectedVerbs.map((v, i) => makeVerbBlock(v, i)).join(',\n');
    const practices = selectedVerbs.flatMap((v, i) => makePractice(v, lessonId, i));
    const practiceBlock = makePracticeBlock(practices);

    const conjugationBlock = `          conjugation: {\n            verbs: [\n${verbBlocks}\n            ],\n            practice: ${practiceBlock},\n          },\n`;

    // Find the end of the grammar array by looking for the closing '],'
    // that is followed by the next lesson property (dialogue:, activities:, culturalNote:, etc.)
    const grammarStart = content.indexOf('grammar: [', match.index);
    if (grammarStart === -1) continue;

    // Find the closing '],' of the grammar array
    // We look for '],' followed by optional whitespace and then 'dialogue:' or 'activities:' or 'culturalNote:' or 'conjugation:'
    const searchArea = content.substring(grammarStart, grammarStart + 5000);
    const closePattern = /\],\s*(?:dialogue:|activities:|culturalNote:|conjugation:|exercises:)/;
    const closeMatch = searchArea.match(closePattern);
    if (!closeMatch) continue;
    const closeIndex = grammarStart + closeMatch.index;
    // Position after '],'
    let pos = closeIndex + 2;
    while (content[pos] === ' ' || content[pos] === '\n' || content[pos] === '\r') pos++;

    insertions.push({ pos, text: conjugationBlock });
    lessonCount++;
  }

  // Apply insertions from end to start
  insertions.sort((a, b) => b.pos - a.pos);
  for (const ins of insertions) {
    content = content.substring(0, ins.pos) + ins.text + content.substring(ins.pos);
  }

  fs.writeFileSync(filePath, content);
  console.log('Updated ' + filePath + ': ' + lessonCount + ' lessons');
}

console.log('\nDone!');
