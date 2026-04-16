import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../api/client";

export default function Home() {
  const [count, setCount] = useState(null);

  useEffect(() => {
    api.get("/").then((r) => setCount(r.data.questions));
  }, []);

  return (
    <div className="text-center py-16">
      <h1 className="text-4xl font-bold text-gray-800 mb-2">LET Ready</h1>
      <p className="text-gray-500 mb-2">AI-Powered LET Exam Reviewer</p>
      {count && (
        <p className="text-blue-500 text-sm mb-10">
          {count} questions in the database
        </p>
      )}

      <div className="flex flex-col gap-4 items-center">
        <Link
          to="/quiz"
          className="w-64 bg-blue-600 text-white py-3 rounded-xl
                     font-medium hover:bg-blue-700 transition"
        >
          Start Quiz
        </Link>
        <Link
          to="/chat"
          className="w-64 bg-white border border-gray-300 text-gray-700
                     py-3 rounded-xl font-medium hover:border-blue-400
                     hover:text-blue-600 transition"
        >
          Ask AI Tutor
        </Link>
      </div>
    </div>
  );
}
