import type { TokenResponse } from "./types";

const TOKEN_KEY = "access_token";
const USER_KEY = "user_data";

export function saveAuth(token: TokenResponse) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token.access_token);
  localStorage.setItem(
    USER_KEY,
    JSON.stringify({
      id: token.user_id,
      email: token.email,
      rol: token.rol,
    })
  );
}

export function clearAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): { id: number; email: string; rol: string } | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
