export default function QuestionCard({ question, onAnswer, answered }) {
  if (!question) return null;

  const choices = ["A", "B", "C", "D"];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      {/* Subject + Topic */}
      <div className="flex gap-2 mb-4">
        <span
          className="text-xs bg-blue-100 text-blue-700
                         px-2 py-1 rounded-full"
        >
          {question.subject}
        </span>
        {question.topic && (
          <span
            className="text-xs bg-gray-100 text-gray-600
                           px-2 py-1 rounded-full"
          >
            {question.topic}
          </span>
        )}
      </div>

      {/* Question */}
      <p className="text-gray-800 font-medium mb-6 leading-relaxed">
        {question.question}
      </p>

      {/* Choices */}
      <div className="flex flex-col gap-3">
        {choices.map((letter) => {
          const text = question.choices?.[letter];
          if (!text) return null;

          const isCorrect = answered && letter === answered.correct;
          const isSelected = answered && letter === answered.selected;
          const isWrong = isSelected && !isCorrect;

          return (
            <button
              key={letter}
              disabled={!!answered}
              onClick={() => onAnswer(letter)}
              className={`text-left px-4 py-3 rounded-xl border text-sm
                          transition font-medium
                ${
                  !answered
                    ? "border-gray-200 hover:border-blue-400 hover:bg-blue-50"
                    : isCorrect
                      ? "border-green-400 bg-green-50 text-green-700"
                      : isWrong
                        ? "border-red-400 bg-red-50 text-red-700"
                        : "border-gray-200 text-gray-400"
                }`}
            >
              <span className="font-bold mr-2">{letter}.</span>
              {text}
            </button>
          );
        })}
      </div>

      {/* Explanation */}
      {answered && (
        <div
          className={`mt-5 p-4 rounded-xl text-sm leading-relaxed
          ${
            answered.is_correct
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-800 border border-red-200"
          }`}
        >
          <p className="font-semibold mb-1">
            {answered.is_correct ? "✅ Correct!" : "❌ Incorrect"}
          </p>
          <p>{answered.explanation}</p>
        </div>
      )}
    </div>
  );
}
