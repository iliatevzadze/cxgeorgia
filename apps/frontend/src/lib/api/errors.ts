export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function parseApiErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as {
      detail?: string | Array<{ msg?: string }>;
      error?: string;
    };

    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      const messages = body.detail
        .map((entry) => entry.msg)
        .filter((message): message is string => Boolean(message));
      if (messages.length > 0) {
        return messages.join(", ");
      }
      return "Validation failed";
    }

    if (typeof body.error === "string") {
      return body.error;
    }
  } catch {
    // Response body is not JSON.
  }

  return response.statusText || "Request failed";
}
