export async function fetchFrameworks() {
  const response = await fetch("/api/frameworks");
  if (!response.ok) {
    throw new Error("Unable to load framework catalog");
  }
  return response.json();
}

export async function routeGoal(goal) {
  const response = await fetch("/api/route", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal })
  });
  if (!response.ok) {
    throw new Error("Unable to route this goal");
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

