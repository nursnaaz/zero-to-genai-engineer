import axios, { type AxiosError } from "axios";

// Reads VITE_API_URL from .env (or defaults to empty string for dev with Vite proxy)
const BASE_URL = import.meta.env.VITE_API_URL || "";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 0,   // no timeout — LLM calls are proxied through SSE; axios is only used for fast endpoints
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor: normalize errors into a consistent shape
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: string; code: string; hint: string }>) => {
    const serverMessage = error.response?.data?.detail;
    const hint = error.response?.data?.hint;
    const message = serverMessage || error.message || "An unexpected error occurred";
    const enriched = new Error(hint ? `${message} (${hint})` : message);
    return Promise.reject(enriched);
  }
);
