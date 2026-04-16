import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Navbar() {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();

  const links = [
    { to: "/", label: "Home" },
    { to: "/quiz", label: "Quiz" },
    { to: "/chat", label: "Chat" },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-3xl mx-auto flex items-center justify-between">
        <Link to="/" className="font-semibold text-blue-600 text-lg">LET Ready</Link>
        <div className="flex gap-4 items-center">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`text-sm font-medium px-3 py-1 rounded-full transition
                ${
                  pathname === l.to
                    ? "bg-blue-600 text-white"
                    : "text-gray-600 hover:text-blue-600"
                }`}
            >
              {l.label}
            </Link>
          ))}
          {user ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Hi, {user.name}</span>
              <button
                onClick={logout}
                className="text-xs text-red-500 hover:text-red-700 font-medium"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="text-sm font-medium text-blue-600 hover:underline"
            >
              Sign in
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
