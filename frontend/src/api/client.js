import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Restore auth token on page load
const token = localStorage.getItem("let_token");
if (token) {
  client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

export default client;
