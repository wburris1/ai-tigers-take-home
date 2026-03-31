import { useMutation } from "@tanstack/react-query";
import { getStoredToken } from "../../lib/session";

export type AiQueryVariables = {
  query: string;
};

export type AiQueryResult = {
  text: string;
  model: string;
  sql?: string;
  result_preview?: {
    columns: string[];
    rows: unknown[][];
    truncated: boolean;
  };
};

async function postAiRequest(variables: AiQueryVariables): Promise<AiQueryResult> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Not authenticated");
  }
  const res = await fetch("/api/ai-request", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query: variables.query }),
  });
  if (res.status === 401) {
    throw new Error("Session expired. Log in again.");
  }
  if (!res.ok) {
    let message = "AI request failed";
    try {
      const data = (await res.json()) as { detail?: unknown };
      const { detail } = data;
      if (typeof detail === "string") {
        message = detail;
      } else if (
        detail &&
        typeof detail === "object" &&
        "message" in detail
      ) {
        message = String((detail as { message: unknown }).message);
      }
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return res.json() as Promise<AiQueryResult>;
}

export function useAIQuery() {
  return useMutation({
    mutationFn: postAiRequest,
  });
}
