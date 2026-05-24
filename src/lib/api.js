export async function fetchFrameworks() {
  const response = await fetch("/api/frameworks");
  if (!response.ok) {
    throw new Error("Unable to load framework catalog");
  }
  return response.json();
}

export async function fetchModelOptions() {
  const response = await fetch("/api/model-options");
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
    headers: { "Content-Type": "application/json" },
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
    headers: { "Content-Type": "application/json" },
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("Unable to store feedback");
  }
  return response.json();
}
