import { useLocation, useNavigate, Link } from "react-router-dom";

export default function Results() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { score, total, subject, wrongAnswers } = state || { score: 0, total: 10, wrongAnswers: [] };
  const pct = Math.round((score / total) * 100);

  const grade =
    pct >= 80
      ? { label: "Excellent!", color: "text-green-600" }
      : pct >= 60
        ? { label: "Good job!", color: "text-blue-600" }
        : pct >= 40
          ? { label: "Keep studying", color: "text-yellow-600" }
          : { label: "Need more practice", color: "text-red-600" };

  return (
    <div className="py-12 text-center">
      <div
        className="bg-white rounded-2xl border border-gray-200
                      p-8 shadow-sm"
      >
        <p className={`text-2xl font-bold mb-1 ${grade.color}`}>
          {grade.label}
        </p>
        <p className="text-6xl font-bold text-gray-800 my-4">{pct}%</p>
        <p className="text-gray-500 mb-8">
          {score} out of {total} correct
          {subject && subject !== "All" && ` in ${subject}`}
        </p>

        <div className="flex flex-col gap-3">
          <button
            onClick={() => navigate("/quiz")}
            className="bg-blue-600 text-white py-3 rounded-xl
                       font-medium hover:bg-blue-700 transition"
          >
            Try Again
          </button>
          <Link
            to="/chat"
            state={{ wrongAnswers }}
            className="border border-gray-300 text-gray-700 py-3
                       rounded-xl font-medium hover:border-blue-400
                       hover:text-blue-600 transition"
          >
            Ask AI Tutor About Wrong Answers
          </Link>
        </div>
      </div>
    </div>
  );
}
