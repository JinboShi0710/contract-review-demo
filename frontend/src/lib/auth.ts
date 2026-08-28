/**
 * Token 管理：存储、读取、清除
 */

const TOKEN_KEY = "contractlens_token";
const USER_KEY = "contractlens_user";

export interface CurrentUser {
  id: string;
  username: string;
  role: "admin" | "reviewer" | "manager";
}

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function saveUser(user: CurrentUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getUser(): CurrentUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as CurrentUser;
  } catch {
    return null;
  }
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}
