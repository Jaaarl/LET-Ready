import { useState, useEffect } from "react";
import api from "../api/client";
import QuestionCard from "../components/QuestionCard";
import ProgressBar from "../components/ProgressBar";
import { useNavigate } from "react-router-dom";

const SUBJECTS = [
  "All",
  "General Education",
  "Professional Education",
  "Biology",
];

const TOTAL = 10;

export default function Quiz() {
  const [subject, setSubject] = useState("All");
  const [questions, setQuestions] = useState([]);
  const [current, setCurrent] = useState(0);
  const [answered, setAnswered] = useState(null);
  const [score, setScore] = useState(0);
  const [wrongAnswers, setWrongAnswers] = useState([]);
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function loadQuestion() {
    setLoading(true);
    setAnswered(null);
    try {
      const params = subject !== "All" ? { subject } : {};
      const res = await api.get("/quiz/random", { params });
      setQuestions((prev) => [...prev, res.data]);
    } finally {
      setLoading(false);
    }
  }

  async function handleAnswer(selected) {
    const q = questions[current];
    const res = await api.post(
      `/quiz/check-answer?question_id=${q.id}&selected=${selected}`,
    );
    const result = {
      ...res.data,
      selected,
      question: q.question,
      subject: q.subject,
      topic: q.topic,
    };
    setAnswered(result);
    if (result.is_correct) {
      setScore((s) => s + 1);
    } else {
      setWrongAnswers((prev) => [...prev, result]);
    }
  }

  function handleNext() {
    if (current + 1 >= TOTAL) {
      navigate("/results", {
        state: { score, total: TOTAL, subject, wrongAnswers },
      });
      return;
    }
    setCurrent((c) => c + 1);
    loadQuestion();
  }

  function startQuiz() {
    setStarted(true);
    loadQuestion();
  }

  // ── Not started yet ──────────────────────────────────────────────────────
  if (!started) {
    return (
      <div className="py-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Start a Quiz</h2>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Choose subject
          </label>
          <div className="flex flex-wrap gap-2">
            {SUBJECTS.map((s) => (
              <button
                key={s}
                onClick={() => setSubject(s)}
                className={`px-4 py-2 rounded-full text-sm font-medium
                            border transition
                  ${
                    subject === s
                      ? "bg-blue-600 text-white border-blue-600"
                      : "border-gray-300 text-gray-600 hover:border-blue-400"
                  }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={startQuiz}
          className="w-full bg-blue-600 text-white py-3 rounded-xl
                     font-medium hover:bg-blue-700 transition"
        >
          Start {TOTAL} Questions
        </button>
      </div>
    );
  }

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading || !questions[current]) {
    return (
      <div className="py-16 text-center text-gray-400">Loading question...</div>
    );
  }

  return (
    <div className="py-4">
      <ProgressBar current={current + 1} total={TOTAL} correct={score} />

      <QuestionCard
        question={questions[current]}
        answered={answered}
        onAnswer={handleAnswer}
      />

      {answered && (
        <button
          onClick={handleNext}
          className="mt-4 w-full bg-blue-600 text-white py-3
                     rounded-xl font-medium hover:bg-blue-700 transition"
        >
          {current + 1 >= TOTAL ? "See Results" : "Next Question"}
        </button>
      )}
    </div>
  );
}
