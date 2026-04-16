import { useState, useRef, useEffect } from "react";
import { useLocation } from "react-router-dom";
import api from "../api/client";

export default function Chat() {
  const location = useLocation();
  const wrongAnswers = location.state?.wrongAnswers || [];
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: wrongAnswers.length > 0
        ? `I see you missed ${wrongAnswers.length} question${wrongAnswers.length > 1 ? "s" : ""}. Let me help you understand what went wrong. What would you like to ask about?`
        : "Hi! I am your LET exam tutor. Ask me anything about the topics you are studying!",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await api.post("/chat/", {
        message: userMsg,
        wrong_answers: wrongAnswers,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: res.data.answer },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Sorry, something went wrong. Try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="flex flex-col h-[75vh]">
      <h2 className="text-xl font-bold text-gray-800 mb-4">AI Tutor</h2>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-4 mb-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm
                          leading-relaxed
                ${
                  m.role === "user"
                    ? "bg-blue-600 text-white rounded-br-sm"
                    : "bg-white border border-gray-200 text-gray-700 rounded-bl-sm"
                }`}
            >
              {m.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div
              className="bg-white border border-gray-200 px-4 py-3
                            rounded-2xl rounded-bl-sm text-sm text-gray-400"
            >
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about any LET topic..."
          className="flex-1 border border-gray-300 rounded-xl px-4 py-3
                     text-sm focus:outline-none focus:border-blue-400"
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-blue-600 text-white px-5 py-3 rounded-xl
                     font-medium hover:bg-blue-700 transition
                     disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  );
}
