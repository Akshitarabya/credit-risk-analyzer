import { AxiosError } from "axios";

/**
 * FastAPI returns errors as either {"detail": "message"} for our own raised
 * HTTPExceptions, or {"detail": [{"msg": "...", ...}, ...]} for Pydantic
 * validation errors. This normalizes both into a single readable string so
 * every form can show a sensible message without duplicating this logic.
 */
export function getErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item: { msg?: string }) => item.msg)
        .filter(Boolean)
        .join(" ");
    }

    if (error.code === "ERR_NETWORK") {
      return "Can't reach the server. Check that the backend is running.";
    }
  }

  return fallback;
}
