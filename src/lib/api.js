import {
  clearProjectId,
  deriveProjectTitle,
  getProjectId,
  setProjectId
} from "./projectSession.js";

export { clearProjectId, deriveProjectTitle, getProjectId, setProjectId };

const PROFILE_STORAGE_KEY = "omniframe_profile_id";

function createProfileId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const random = Math.floor(Math.random() * 16);
    const value = char === "x" ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

export function getOrCreateProfileId() {
  const existing = localStorage.getItem(PROFILE_STORAGE_KEY);
  if (existing) {
    return existing;
  }
  const profileId = createProfileId();
  localStorage.setItem(PROFILE_STORAGE_KEY, profileId);
  return profileId;
}

function profileHeaders(extra = {}) {
  return {
    "X-OmniFrame-Profile-Id": getOrCreateProfileId(),
    ...extra
  };
}

async function apiFetch(path, options = {}) {
  const headers = profileHeaders(options.headers ?? {});
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const error = new Error(`Request failed: ${path}`);
    error.status = response.status;
    try {
      const body = await response.clone().json();
      error.detail = body?.detail;
    } catch {
      // response body was not JSON
    }
    throw error;
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function requireSessionProjectId() {
  const projectId = getProjectId();
  if (!projectId) {
    throw new Error("No active project session");
  }
  return projectId;
}

export async function fetchFrameworks() {
  const response = await fetch("/api/frameworks", { headers: profileHeaders() });
  if (!response.ok) {
    throw new Error("Unable to load framework catalog");
  }
  return response.json();
}

export async function fetchModelOptions() {
  const response = await fetch("/api/model-options", { headers: profileHeaders() });
  if (!response.ok) {
    throw new Error("Unable to load model options");
  }
  return response.json();
}

export async function routeGoal(goal, frameworkId = null) {
  const modelProvider = localStorage.getItem("omniframe_model_provider") || "openai";
  const modelId = localStorage.getItem("omniframe_model_id") || "gpt-5.1";
  const response = await fetch("/api/route", {
    method: "POST",
    headers: profileHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ goal, framework_id: frameworkId, model_provider: modelProvider, model_id: modelId })
  });
  if (!response.ok) {
    throw new Error("Unable to route this goal");
  }
  return response.json();
}

export async function refreshOptions(payload) {
  const modelProvider = localStorage.getItem("omniframe_model_provider") || "openai";
  const modelId = localStorage.getItem("omniframe_model_id") || "gpt-5.1";
  const response = await fetch("/api/options/refresh", {
    method: "POST",
    headers: profileHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ...payload, model_provider: modelProvider, model_id: modelId })
  });
  if (!response.ok) {
    throw new Error("Unable to refresh options");
  }
  return response.json();
}

export async function sendFeedback(payload) {
  const response = await fetch("/api/feedback", {
    method: "POST",
    headers: profileHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Unable to store feedback");
  }
  return response.json();
}

export async function upsertProfile(displayName = null) {
  const profileId = getOrCreateProfileId();
  return apiFetch(`/api/profiles/${profileId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name: displayName })
  });
}

export async function createProject({ title, goal, frameworkId = null, status = "draft" }) {
  const profileId = getOrCreateProfileId();
  return apiFetch(`/api/profiles/${profileId}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, goal, framework_id: frameworkId, status })
  });
}

export async function createProjectForGoal(goal, frameworkId = null) {
  return createProject({
    title: deriveProjectTitle(goal),
    goal,
    frameworkId,
    status: "active"
  });
}

export async function fetchProject(projectId) {
  return apiFetch(`/api/projects/${projectId}`);
}

export async function updateProject(projectId, payload) {
  return apiFetch(`/api/projects/${projectId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function persistSessionProject(goal, frameworkId) {
  await upsertProfile();
  const project = await createProjectForGoal(goal, frameworkId);
  setProjectId(project.id);
  return project;
}

export async function saveAnswers(answers) {
  const projectId = requireSessionProjectId();
  return apiFetch(`/api/projects/${projectId}/answers`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers })
  });
}

export async function saveElementScore(payload) {
  const projectId = requireSessionProjectId();
  return apiFetch(`/api/projects/${projectId}/scores`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function saveProjectDetails(details) {
  const projectId = requireSessionProjectId();
  return updateProject(projectId, { details });
}

export async function chatProjectDetails(instruction) {
  const projectId = requireSessionProjectId();
  const modelProvider = localStorage.getItem("omniframe_model_provider") || "openai";
  const modelId = localStorage.getItem("omniframe_model_id") || "gpt-5.1";
  return apiFetch(`/api/projects/${projectId}/details/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ instruction, model_provider: modelProvider, model_id: modelId })
  });
}

export async function importProjectDetails(documentText, filename = null) {
  const projectId = requireSessionProjectId();
  const modelProvider = localStorage.getItem("omniframe_model_provider") || "openai";
  const modelId = localStorage.getItem("omniframe_model_id") || "gpt-5.1";
  return apiFetch(`/api/projects/${projectId}/details/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document: documentText, filename, model_provider: modelProvider, model_id: modelId })
  });
}

export async function fetchComponentResults(frameworkId) {
  const projectId = requireSessionProjectId();
  const query = new URLSearchParams({ framework_id: frameworkId }).toString();
  return apiFetch(`/api/projects/${projectId}/component-results?${query}`);
}

export async function generateComponentResult(frameworkId, componentId, { regenerate = false } = {}) {
  const projectId = requireSessionProjectId();
  const modelProvider = localStorage.getItem("omniframe_model_provider") || "openai";
  const modelId = localStorage.getItem("omniframe_model_id") || "gpt-5.1";
  return apiFetch(`/api/projects/${projectId}/components/${encodeURIComponent(componentId)}/result`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ framework_id: frameworkId, regenerate, model_provider: modelProvider, model_id: modelId })
  });
}
