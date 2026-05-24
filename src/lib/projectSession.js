export const PROJECT_COOKIE_NAME = "omniframe_project_id";

export function deriveProjectTitle(goal, maxLength = 80) {
  const firstLine = goal
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find(Boolean);
  const title = firstLine || "Untitled analysis";
  if (title.length <= maxLength) {
    return title;
  }
  return `${title.slice(0, maxLength - 1).trimEnd()}…`;
}

export function parseCookieValue(cookieHeader, name) {
  if (!cookieHeader) {
    return null;
  }
  const prefix = `${name}=`;
  const parts = cookieHeader.split(";").map((part) => part.trim());
  const match = parts.find((part) => part.startsWith(prefix));
  if (!match) {
    return null;
  }
  try {
    return decodeURIComponent(match.slice(prefix.length));
  } catch {
    return match.slice(prefix.length);
  }
}

export function buildProjectCookie(id) {
  return `${PROJECT_COOKIE_NAME}=${encodeURIComponent(id)}; path=/; SameSite=Lax`;
}

export function buildClearProjectCookie() {
  return `${PROJECT_COOKIE_NAME}=; path=/; SameSite=Lax; Max-Age=0`;
}

export function getProjectId() {
  if (typeof document === "undefined") {
    return null;
  }
  return parseCookieValue(document.cookie, PROJECT_COOKIE_NAME);
}

export function setProjectId(id) {
  if (typeof document === "undefined" || !id) {
    return;
  }
  document.cookie = buildProjectCookie(String(id));
}

export function clearProjectId() {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = buildClearProjectCookie();
}
