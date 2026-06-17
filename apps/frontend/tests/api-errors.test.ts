import assert from "node:assert/strict";
import { test } from "node:test";

import { ApiError, parseApiErrorMessage } from "../src/lib/api/errors";

test("ApiError stores status code", () => {
  const error = new ApiError("Invalid email or password", 401);
  assert.equal(error.message, "Invalid email or password");
  assert.equal(error.status, 401);
  assert.equal(error.name, "ApiError");
});

test("parseApiErrorMessage reads string detail", async () => {
  const response = new Response(
    JSON.stringify({ detail: "Email already registered" }),
    { status: 409, statusText: "Conflict" },
  );

  const message = await parseApiErrorMessage(response);
  assert.equal(message, "Email already registered");
});

test("parseApiErrorMessage reads validation detail array", async () => {
  const response = new Response(
    JSON.stringify({
      detail: [{ msg: "Password must be at least 8 characters" }],
    }),
    { status: 422, statusText: "Unprocessable Entity" },
  );

  const message = await parseApiErrorMessage(response);
  assert.equal(message, "Password must be at least 8 characters");
});

test("parseApiErrorMessage falls back to status text", async () => {
  const response = new Response("not json", {
    status: 500,
    statusText: "Internal Server Error",
  });

  const message = await parseApiErrorMessage(response);
  assert.equal(message, "Internal Server Error");
});
