import { Channel, invoke } from "@tauri-apps/api/core";

export type ReasonixStatus = {
  status: "available" | "unavailable" | "setup_required" | "disabled";
  reason: string | null;
  version: string;
  model: string;
  platform: string;
};

export type ReasonixEvent =
  | { type: "chunk"; text: string }
  | { type: "status"; state: string };

export type ExplainResult = {
  text: string;
  citations_ok: boolean;
  usage_unavailable: boolean;
  session_id: string;
};

export type ReasonixError = {
  code: string;
  message: string;
};

/** True only inside the Tauri desktop WebView; false in a plain browser. */
export function isDesktopRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

export async function getReasonixStatus(): Promise<ReasonixStatus> {
  return invoke<ReasonixStatus>("reasonix_status");
}

export async function explainWithReasonix(
  question: string,
  snapshot: string,
  onEvent: (event: ReasonixEvent) => void,
): Promise<ExplainResult> {
  const channel = new Channel<ReasonixEvent>();
  channel.onmessage = onEvent;
  return invoke<ExplainResult>("reasonix_explain", { question, snapshot, onEvent: channel });
}

export function asReasonixError(error: unknown): ReasonixError {
  if (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof (error as { code: unknown }).code === "string"
  ) {
    const candidate = error as { code: string; message?: unknown };
    return {
      code: candidate.code,
      message: typeof candidate.message === "string" ? candidate.message : candidate.code,
    };
  }
  return { code: "UNKNOWN", message: String(error) };
}
