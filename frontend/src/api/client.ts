import axios from "axios";

export const TOKEN_STORAGE_KEY = "ledgerline_access_token";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach the JWT to every outgoing request, if we have one.
//
// Trade-off worth stating out loud: the token is kept in localStorage for
// this project's scope, which is simple but readable by any script on the
// page (XSS risk). A production system would prefer an httpOnly cookie.
// This is a deliberate, explainable simplification, not an oversight.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the backend ever says the token is invalid/expired, clear it so the
// app doesn't keep sending a dead token in a loop; the UI reacts to the
// cleared auth state and routes back to /login.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
