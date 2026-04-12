#!/usr/bin/env node
/**
 * PDF Page-by-Page LET Reviewer Parser - v4 (Final)
 * Fixes: lowercase choices (a. b. c. d.), trim qBlock, collect answers from ALL pages
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { getDocument } from '/home/jarl/.openclaw/workspace/node_modules/pdfjs-dist/legacy/build/pdf.mjs';

const DIR = join(process.cwd(), 'downloads/LET-Reviewer-2026');
const OUTPUT = join(process.cwd(), 'let_review_genprof.json');

// ---------- Answer Parsing ----------

function parseAnswers(text) {
  const answers = {};
  // "1. B 2. B 3. B" or "1.B 2.B" or "1. B*"
  const matches = [...text.matchAll(/(\d+)\s*\.?\s*([A-Da-d])(?:\s*\*)?/gi)];
  for (let m of matches) {
    answers[parseInt(m[1])] = m[2].toUpperCase();
  }
  return answers;
}

// ---------- Question Parsing ----------

function parseQuestionsFromPage(text, part, fileAnswers) {
  const questions = [];

  // Clean noise
  text = text.replace(/This\s+(?:file|reviewer)\s+was\s+submitted\s+to\s+www\.teachpinas\.com/gi, '');
  text = text.replace(/Get more Free LET Reviewers @ www\.teachpinas\.com/gi, '');
  text = text.replace(/\d+\s+ITEMS?\s*/gi, '');
  text = text.replace(/With ANSWERS\s*/gi, '');

  // Split off answer keys section (if present on this page)
  let ansText = '';
  for (let sep of ['Answer Keys', 'ANSWER KEYS', 'Answer Keys  ']) {
    let idx = text.indexOf(sep);
    if (idx > -1) {
      ansText = text.slice(idx + sep.length).trim();
      text = text.slice(0, idx).trim();
      break;
    }
  }

  // Merge page-local answers with file-level answers
  const pageAnswers = parseAnswers(ansText);
  const allAnswers = { ...fileAnswers, ...pageAnswers };

  // Find all question starts: space + number + . + space + (letter or ( or " or ')
  const qStarts = [...text.matchAll(/\s(\d+)\.\s+([A-Za-z("'_])/g)];

  for (let i = 0; i < qStarts.length; i++) {
    const startPos = qStarts[i].index;
    const endPos = i + 1 < qStarts.length ? qStarts[i + 1].index : text.length;
    const qBlock = text.slice(startPos, endPos).trim();

    const qNum = parseInt(qStarts[i][1]);

    // Parse: question text ending in ? + all choice text that follows
    // Parse: question text ending in …? or ? + all choice text
    // Use non-greedy +? to stop at the FIRST occurrence of ? or …
    const qm = qBlock.match(/\d+\.\s*([^…?]+?[?...]))\s*([A-Da-d]\..+)/is);
    if (!qm) continue;

    const question = qm[1].trim();
    const choicesText = qm[2];

    // Split choices by letter marker (supports uppercase AND lowercase!)
    const choiceParts = choicesText.split(/(?=[A-Da-d]\.)\s*/).filter(p => p.trim());
    const choices = {};
    for (let p of choiceParts) {
      const cm = p.match(/^([A-Da-d])\.\s*(.+)/i);
      if (cm) {
        choices[cm[1].toUpperCase()] = cm[2].trim();
      }
    }

    if (question && Object.keys(choices).length >= 2) {
      const ans = allAnswers[qNum];
      globalQNum++;
      questions.push({
        id: `gen_${String(globalQNum).padStart(4,'0')}`,
        part: part,
        subject: null,
        topic: null,
        question: question,
        choices: choices,
        answer: ans || null,
        answer_text: ans ? choices[ans] : null,
        explanation: '',
        source: 'teachpinas.com',
        difficulty: null
      });
    }
  }

  return questions;
}

// ---------- PDF Processing ----------

async function processPDF(filename, subject, part) {
  const filepath = join(DIR, filename);
  const buf = new Uint8Array(readFileSync(filepath));
  const doc = await getDocument({data: buf}).promise;

  // FIRST PASS: collect ALL answer patterns from ALL pages
  const fileAnswers = {};
  for (let pi = 1; pi <= doc.numPages; pi++) {
    const page = await doc.getPage(pi);
    const content = await page.getTextContent();
    const text = content.items.map(item => item.str).join(' ');
    const pageAnswers = parseAnswers(text);
    Object.assign(fileAnswers, pageAnswers);
  }

  // SECOND PASS: extract questions from all pages
  let allQuestions = [];
  for (let pi = 1; pi <= doc.numPages; pi++) {
    const page = await doc.getPage(pi);
    const content = await page.getTextContent();
    const pageText = content.items.map(item => item.str).join(' ');

    const questions = parseQuestionsFromPage(pageText, part, fileAnswers);
    for (let q of questions) q.subject = subject;
    allQuestions.push(...questions);
  }

  return { questions: allQuestions, pageCount: doc.numPages };
}

let globalQNum = 0;

async function main() {
  console.log('PDF Page-by-Page LET Reviewer Parser v5 (Fixed IDs)\n');

  const pdfFiles = [
    { f: 'GenEd-Part1.pdf',  s: 'General Education',           p: 'Part 1' },
    { f: 'GenEd-Part2.pdf',  s: 'General Education',           p: 'Part 2' },
    { f: 'GenEd-Part3.pdf',  s: 'General Education',           p: 'Part 3' },
    { f: 'GenEd-Part4.pdf',  s: 'General Education',           p: 'Part 4' },
    { f: 'GenEd-Part5.pdf',  s: 'General Education',           p: 'Part 5' },
    { f: 'GenEd-Part6.pdf',  s: 'General Education',           p: 'Part 6' },
    { f: 'GenEd-Part7.pdf',  s: 'General Education',           p: 'Part 7' },
    { f: 'GenEd-Part8.pdf',  s: 'General Education',           p: 'Part 8' },
    { f: 'ProfEd-Part1.pdf', s: 'Professional Education',        p: 'Part 1' },
    { f: 'ProfEd-Part2.pdf', s: 'Professional Education',        p: 'Part 2' },
    { f: 'ProfEd-Part3.pdf', s: 'Professional Education',        p: 'Part 3' },
    { f: 'ProfEd-Part4.pdf', s: 'Professional Education',        p: 'Part 4' },
    { f: 'ProfEd-Part5.pdf', s: 'Professional Education',        p: 'Part 5' },
  ];

  let allQuestions = [];
  let totalWithAns = 0;

  for (let item of pdfFiles) {
    console.log(`Processing: ${item.f}`);
    try {
      const result = await processPDF(item.f, item.s, item.p);
      const withAns = result.questions.filter(q => q.answer).length;
      console.log(`  -> ${result.questions.length} questions, ${withAns} with answers`);
      allQuestions.push(...result.questions);
      totalWithAns += withAns;
    } catch (e) {
      console.log(`  ERROR: ${e.message}`);
    }
  }

  allQuestions.sort((a, b) => a.id.localeCompare(b.id));

  writeFileSync(OUTPUT, JSON.stringify(allQuestions, null, 2), 'utf-8');
  console.log(`\n✅ ${allQuestions.length} total questions (${totalWithAns} with answers)`);
  console.log(`   Saved to: ${OUTPUT}`);

  if (allQuestions.length > 0) {
    const sample = allQuestions.find(q => q.answer);
    if (sample) {
      console.log('\nSample (with answer):');
      console.log(JSON.stringify(sample, null, 2));
    }
  }
}

main();
